from collections.abc import Callable, Sequence
from typing import Any, Protocol

from pydantic_ai import Agent, BinaryContent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import AIProvider, Settings
from app.images import DownloadedImage, ImageDownloader
from app.logging import log_error
from app.prompts import SYSTEM_INSTRUCTIONS, build_prompt
from app.question_images import extract_image_urls, split_image_parts
from app.schemas import ModelAnswer, SearchRequest

FALLBACK_ANSWER = ModelAnswer(answer="未知", analysis="服务器处理出错")
DUMMY_API_KEY = "not-needed"


class Answerer(Protocol):
    def answer(self, payload: SearchRequest) -> ModelAnswer: ...


class AgentRunner(Protocol):
    def run_sync(
        self,
        user_prompt: str | Sequence[Any] | None = None,
        *,
        model_settings: ModelSettings | None = None,
    ) -> Any: ...


AgentFactory = Callable[[Any], AgentRunner]


class PydanticAIAnswerer:
    def __init__(
        self,
        settings: Settings,
        *,
        image_downloader: ImageDownloader | None = None,
        agent_factory: AgentFactory | None = None,
    ) -> None:
        self._settings = settings
        self._image_downloader = image_downloader or ImageDownloader(settings.chaoxing_cookie_value)
        self._agent_factory = agent_factory or create_answer_agent

    def answer(self, payload: SearchRequest) -> ModelAnswer:
        try:
            return self._run_agent(payload)
        except Exception as exc:
            log_error(f"AI 调用或结构化输出失败: {exc}")
            return FALLBACK_ANSWER

    def _run_agent(self, payload: SearchRequest) -> ModelAnswer:
        image_urls = extract_image_urls(payload.title, payload.options)
        model_name = select_model_name(self._settings, has_images=bool(image_urls))
        images_by_url = self._download_images(image_urls)
        model = build_model(self._settings, model_name)
        agent = self._agent_factory(model)
        result = agent.run_sync(
            build_agent_input(payload, images_by_url),
            model_settings=ModelSettings(
                temperature=self._settings.ai_temperature,
                timeout=self._settings.ai_timeout,
            ),
        )
        output = result.output
        if not isinstance(output, ModelAnswer):
            return ModelAnswer.model_validate(output)
        return output

    def _download_images(self, image_urls: list[str]) -> dict[str, DownloadedImage]:
        return {url: self._image_downloader.download(url) for url in image_urls}


def create_answer_agent(model: Any) -> AgentRunner:
    return Agent(
        model,
        output_type=ModelAnswer,
        instructions=SYSTEM_INSTRUCTIONS,
        retries=2,
    )


def select_model_name(settings: Settings, *, has_images: bool) -> str:
    if has_images:
        if not settings.ai_vision_model:
            raise RuntimeError("AI_VISION_MODEL is not configured")
        return settings.ai_vision_model

    if not settings.ai_text_model:
        raise RuntimeError("AI_TEXT_MODEL is not configured")
    return settings.ai_text_model


def build_model(settings: Settings, model_name: str) -> OpenAIChatModel:
    if settings.ai_provider != AIProvider.openai_compatible:
        raise RuntimeError(f"Unsupported AI_PROVIDER: {settings.ai_provider}")

    provider = OpenAIProvider(
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key_value or DUMMY_API_KEY,
    )
    return OpenAIChatModel(normalize_openai_model_name(model_name), provider=provider)


def normalize_openai_model_name(model_name: str) -> str:
    prefix = "openai:"
    if model_name.startswith(prefix):
        return model_name[len(prefix) :]
    return model_name


def build_agent_input(
    payload: SearchRequest,
    images_by_url: dict[str, DownloadedImage],
) -> str | list[Any]:
    prompt = build_prompt(payload, image_count=len(images_by_url))
    if not images_by_url:
        return prompt

    content: list[Any] = []
    for part in split_image_parts(prompt):
        if part.kind == "text" and part.text:
            content.append(part.text)
        elif part.kind == "image":
            image = images_by_url.get(part.url)
            if image is None:
                raise RuntimeError(f"图片未完成下载: {part.url}")
            content.append(BinaryContent(data=image.data, media_type=image.media_type))

    return content
