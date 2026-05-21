from typing import Any

from pydantic import SecretStr

import app.llm as llm_module
from app.config import JsonMode, Settings
from app.llm import FALLBACK_ANSWER, LiteLLMAnswerer, build_completion_kwargs, parse_model_answer
from app.schemas import QuestionType, SearchRequest


def make_payload() -> SearchRequest:
    return SearchRequest(title="题目", options="A. 正确\nB. 错误", type=QuestionType.single)


def make_settings(json_mode: JsonMode = JsonMode.auto) -> Settings:
    return Settings(
        llm_api_key=SecretStr("test-key"),
        llm_base_url="https://example.invalid/v1",
        llm_model="openai/test-model",
        llm_json_mode=json_mode,
    )


def test_parse_model_answer_cleans_fences_and_reasoning_tags() -> None:
    answer = parse_model_answer(
        '<think>reasoning</think>\n```json\n{"answer": "正确", "analysis": "因为如此"}\n```'
    )

    assert answer.answer == "正确"
    assert answer.analysis == "因为如此"


def test_parse_model_answer_extracts_surrounded_json() -> None:
    answer = parse_model_answer('前缀 {"answer": "A", "analysis": "ok"} 后缀')

    assert answer.answer == "A"
    assert answer.analysis == "ok"


def test_litellm_answerer_returns_fallback_on_failure() -> None:
    settings = Settings(llm_model=None, llm_json_mode=JsonMode.off)

    answer = LiteLLMAnswerer(settings).answer(make_payload())

    assert answer == FALLBACK_ANSWER


def test_json_mode_auto_uses_litellm_capability_detection(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        llm_module,
        "get_supported_openai_params",
        lambda model: ["temperature", "response_format"],
    )

    kwargs = build_completion_kwargs(make_settings(JsonMode.auto), make_payload())

    assert kwargs["response_format"] == {"type": "json_object"}


def test_json_mode_auto_omits_unsupported_response_format(monkeypatch: Any) -> None:
    monkeypatch.setattr(llm_module, "get_supported_openai_params", lambda model: ["temperature"])

    kwargs = build_completion_kwargs(make_settings(JsonMode.auto), make_payload())

    assert "response_format" not in kwargs


def test_json_mode_on_forces_response_format() -> None:
    kwargs = build_completion_kwargs(make_settings(JsonMode.on), make_payload())

    assert kwargs["response_format"] == {"type": "json_object"}


def test_litellm_completion_is_called_without_network(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_completion(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"choices": [{"message": {"content": '{"answer": "A", "analysis": "ok"}'}}]}

    monkeypatch.setattr(llm_module, "completion", fake_completion)
    monkeypatch.setattr(
        llm_module, "get_supported_openai_params", lambda model: ["response_format"]
    )

    answer = LiteLLMAnswerer(make_settings()).answer(make_payload())

    assert answer.answer == "A"
    assert captured["api_key"] == "test-key"
    assert captured["api_base"] == "https://example.invalid/v1"
    assert captured["response_format"] == {"type": "json_object"}


def test_build_completion_kwargs_applies_image_url_mapper() -> None:
    payload = SearchRequest(
        title="题目 https://p.ananas.chaoxing.com/star3/origin/a.png",
        options="A. 正确\nB. 错误",
        type=QuestionType.single,
    )

    kwargs = build_completion_kwargs(
        make_settings(JsonMode.off),
        payload,
        image_url_mapper=lambda url: "data:image/png;base64,YWJj",
    )
    user_content = kwargs["messages"][1]["content"]

    assert isinstance(user_content, list)
    assert user_content[1:] == [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,YWJj"}},
    ]


def test_settings_reads_chaoxing_cookie_value() -> None:
    settings = Settings(
        llm_model="openai/test-model",
        chaoxing_cookie=SecretStr("chaoxing-cookie"),
    )

    assert settings.chaoxing_cookie_value == "chaoxing-cookie"
