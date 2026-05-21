import json
import re
from collections.abc import Mapping
from typing import Any, Protocol

from litellm import completion, get_supported_openai_params

from app.config import JsonMode, Settings
from app.logging import log_error
from app.prompts import build_messages
from app.schemas import ModelAnswer, SearchRequest

FALLBACK_ANSWER = ModelAnswer(answer="未知", analysis="服务器处理出错")


class Answerer(Protocol):
    def answer(self, payload: SearchRequest) -> ModelAnswer: ...


class LiteLLMAnswerer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def answer(self, payload: SearchRequest) -> ModelAnswer:
        try:
            content = self._request_model(payload)
            return parse_model_answer(content)
        except Exception as exc:
            log_error(f"LLM 调用或解析失败: {exc}")
            return FALLBACK_ANSWER

    def _request_model(self, payload: SearchRequest) -> str:
        if not self._settings.llm_model:
            raise RuntimeError("LLM_MODEL is not configured")

        kwargs = build_completion_kwargs(self._settings, payload)
        response = completion(**kwargs)
        return extract_message_content(response)


def build_completion_kwargs(settings: Settings, payload: SearchRequest) -> dict[str, Any]:
    if not settings.llm_model:
        raise RuntimeError("LLM_MODEL is not configured")

    kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": build_messages(payload),
        "temperature": settings.llm_temperature,
        "timeout": settings.llm_timeout,
    }
    if settings.llm_api_key_value:
        kwargs["api_key"] = settings.llm_api_key_value
    if settings.llm_base_url:
        kwargs["api_base"] = settings.llm_base_url
    if should_enable_json_mode(settings):
        kwargs["response_format"] = {"type": "json_object"}
    return kwargs


def should_enable_json_mode(settings: Settings) -> bool:
    if settings.llm_json_mode == JsonMode.on:
        return True
    if settings.llm_json_mode == JsonMode.off:
        return False
    if not settings.llm_model:
        return False

    try:
        supported_params = get_supported_openai_params(model=settings.llm_model)
    except Exception as exc:
        log_error(f"无法检测模型 JSON mode 支持情况: {exc}")
        return False
    return "response_format" in set(supported_params or [])


def extract_message_content(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content

    if isinstance(response, Mapping):
        choices_obj = response.get("choices")
        if isinstance(choices_obj, list) and choices_obj:
            choice = choices_obj[0]
            if isinstance(choice, Mapping):
                message = choice.get("message")
                if isinstance(message, Mapping):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content

    raise ValueError("模型响应中没有可解析的 content")


def parse_model_answer(content: str) -> ModelAnswer:
    cleaned = clean_model_content(content)
    obj = extract_first_json_object(cleaned)
    return ModelAnswer.model_validate(obj)


def clean_model_content(content: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def extract_first_json_object(content: str) -> Any:
    decoder = json.JSONDecoder()
    for index, char in enumerate(content):
        if char != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(content[index:])
            return obj
        except json.JSONDecodeError:
            continue
    raise ValueError("模型输出中没有合法 JSON 对象")
