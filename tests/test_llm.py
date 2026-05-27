from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any

from pydantic import SecretStr
from pydantic_ai import BinaryContent

from app.config import Settings
from app.images import DownloadedImage, ImageDownloader
from app.llm import (
    FALLBACK_ANSWER,
    PydanticAIAnswerer,
    build_agent_input,
    normalize_openai_model_name,
    select_model_name,
)
from app.schemas import ModelAnswer, QuestionType, SearchRequest


def make_payload(
    *,
    title: str = "题目",
    options: str = "A. 正确\nB. 错误",
) -> SearchRequest:
    return SearchRequest(title=title, options=options, type=QuestionType.single)


def make_settings(
    *,
    text_model: str | None = "gpt-4o-mini",
    vision_model: str | None = "gpt-4o",
) -> Settings:
    return Settings(
        ai_api_key=SecretStr("test-key"),
        ai_base_url="https://example.invalid/v1",
        ai_text_model=text_model,
        ai_vision_model=vision_model,
    )


def test_answerer_returns_fallback_when_text_model_is_missing() -> None:
    answer = PydanticAIAnswerer(make_settings(text_model=None)).answer(make_payload())

    assert answer == FALLBACK_ANSWER


def test_answerer_calls_pydantic_ai_agent_without_network() -> None:
    captured: dict[str, Any] = {}

    class FakeAgent:
        def run_sync(
            self,
            user_prompt: str | Sequence[Any] | None = None,
            *,
            model_settings: object = None,
        ) -> object:
            captured["user_prompt"] = user_prompt
            captured["model_settings"] = model_settings
            return SimpleNamespace(output=ModelAnswer(answer="A", analysis="ok"))

    answer = PydanticAIAnswerer(
        make_settings(),
        agent_factory=lambda model: FakeAgent(),
    ).answer(make_payload())

    assert answer.answer == "A"
    assert "题目: 题目" in captured["user_prompt"]
    assert captured["model_settings"]["temperature"] == 0.3
    assert captured["model_settings"]["timeout"] == 30.0


def test_image_question_requires_vision_model() -> None:
    payload = make_payload(title="题目 https://example.com/table.png")

    answer = PydanticAIAnswerer(make_settings(vision_model=None)).answer(payload)

    assert answer == FALLBACK_ANSWER


def test_image_question_downloads_images_and_uses_binary_content() -> None:
    captured: dict[str, Any] = {}

    class FakeAgent:
        def run_sync(
            self,
            user_prompt: str | Sequence[Any] | None = None,
            *,
            model_settings: object = None,
        ) -> object:
            captured["user_prompt"] = user_prompt
            return SimpleNamespace(output=ModelAnswer(answer="A", analysis="ok"))

    class FakeDownloader(ImageDownloader):
        def download(self, url: str) -> DownloadedImage:
            captured.setdefault("downloaded", []).append(url)
            return DownloadedImage(data=b"image-bytes", media_type="image/png")

    payload = make_payload(title="题目 https://example.com/table.png求答案")
    answer = PydanticAIAnswerer(
        make_settings(),
        image_downloader=FakeDownloader(),
        agent_factory=lambda model: FakeAgent(),
    ).answer(payload)

    assert answer.answer == "A"
    assert captured["downloaded"] == ["https://example.com/table.png"]
    user_prompt = captured["user_prompt"]
    assert isinstance(user_prompt, list)
    assert any(isinstance(part, BinaryContent) for part in user_prompt)


def test_build_agent_input_preserves_text_and_binary_image_order() -> None:
    payload = make_payload(title="前 https://example.com/a.png 后")
    user_prompt = build_agent_input(
        payload,
        {"https://example.com/a.png": DownloadedImage(data=b"abc", media_type="image/png")},
    )

    assert isinstance(user_prompt, list)
    binary_index = next(i for i, part in enumerate(user_prompt) if isinstance(part, BinaryContent))
    assert "前 " in user_prompt[binary_index - 1]
    assert " 后" in user_prompt[binary_index + 1]


def test_select_model_name_routes_by_image_presence() -> None:
    settings = make_settings(text_model="text-model", vision_model="vision-model")

    assert select_model_name(settings, has_images=False) == "text-model"
    assert select_model_name(settings, has_images=True) == "vision-model"


def test_normalize_openai_model_name_accepts_optional_openai_prefix() -> None:
    assert normalize_openai_model_name("openai:gpt-4o-mini") == "gpt-4o-mini"
    assert normalize_openai_model_name("gpt-4o-mini") == "gpt-4o-mini"
