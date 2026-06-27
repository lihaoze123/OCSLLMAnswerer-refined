import json
from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app import main as app_main
from app.config import Settings
from app.llm import PydanticAIAnswerer
from app.main import create_app
from app.schemas import ModelAnswer, QuestionType, SearchRequest


class FakeAnswerer:
    def __init__(self) -> None:
        self.payloads: list[SearchRequest] = []

    async def answer(self, payload: SearchRequest) -> ModelAnswer:
        self.payloads.append(payload)
        return ModelAnswer(answer="A", analysis="测试解析")


def make_client(answerer: FakeAnswerer | None = None) -> TestClient:
    settings = Settings(
        ai_api_key=SecretStr("test-key"),
        ai_text_model="test-model",
    )
    app = create_app(settings=settings, answerer=answerer or FakeAnswerer())
    return TestClient(app)


def test_health_endpoint_preserves_ocs_shape() -> None:
    client = make_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"code": 1, "msg": "OCS ChatGPT Server is running"}


def test_head_health_endpoint_is_supported() -> None:
    client = make_client()

    response = client.head("/")

    assert response.status_code == 200


def test_search_preserves_success_contract_and_normalizes_options() -> None:
    answerer = FakeAnswerer()
    client = make_client(answerer)

    response = client.post(
        "/search",
        json={
            "title": "  题目内容  ",
            "options": " A. 选项A \n\n B. 选项B ",
            "type": "single",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "code": 1,
        "question": "题目内容",
        "answer": "A",
        "analysis": "测试解析",
    }
    assert answerer.payloads[0].options == "A. 选项A\nB. 选项B"


def test_search_awaits_pydantic_ai_answerer_without_event_loop_fallback() -> None:
    captured: dict[str, Any] = {}

    class FakeAgent:
        async def run(
            self,
            user_prompt: str | Sequence[Any] | None = None,
            *,
            model_settings: object = None,
        ) -> object:
            captured["user_prompt"] = user_prompt
            captured["model_settings"] = model_settings
            return SimpleNamespace(output=ModelAnswer(answer="B", analysis="async ok"))

    settings = Settings(
        ai_api_key=SecretStr("test-key"),
        ai_text_model="test-model",
    )
    answerer = PydanticAIAnswerer(settings, agent_factory=lambda model: FakeAgent())
    client = TestClient(create_app(settings=settings, answerer=answerer))

    response = client.post("/search", json={"title": "题目", "options": "", "type": "single"})

    assert response.status_code == 200
    assert response.json() == {
        "code": 1,
        "question": "题目",
        "answer": "B",
        "analysis": "async ok",
    }
    assert "题目: 题目" in captured["user_prompt"]
    assert captured["model_settings"]["timeout"] == 30.0


def test_search_unwraps_nested_json_answer_field() -> None:
    class FakeAgent:
        async def run(
            self,
            user_prompt: str | Sequence[Any] | None = None,
            *,
            model_settings: object = None,
        ) -> object:
            return SimpleNamespace(
                output=ModelAnswer(
                    answer='{"answer":"对","analysis":"二属性关系模式一定满足 BCNF。"}',
                    analysis="outer analysis should not be returned",
                )
            )

    settings = Settings(
        ai_api_key=SecretStr("test-key"),
        ai_text_model="test-model",
    )
    answerer = PydanticAIAnswerer(settings, agent_factory=lambda model: FakeAgent())
    client = TestClient(create_app(settings=settings, answerer=answerer))

    response = client.post(
        "/search",
        json={
            "title": "任何一个只包含两个属性的关系模式一定满足BCNF。",
            "options": "对\n错",
            "type": "judgement",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "code": 1,
        "question": "任何一个只包含两个属性的关系模式一定满足BCNF。",
        "answer": "对",
        "analysis": "二属性关系模式一定满足 BCNF。",
    }


def test_search_preserves_ai_failure_fallback_success_shape() -> None:
    settings = Settings(ai_text_model=None)
    app = create_app(settings=settings)
    client = TestClient(app)

    response = client.post("/search", json={"title": "题目", "options": "", "type": "single"})

    assert response.status_code == 200
    assert response.json() == {
        "code": 1,
        "question": "题目",
        "answer": "未知",
        "analysis": "服务器处理出错",
    }


def test_empty_title_returns_ocs_error_shape() -> None:
    client = make_client()

    response = client.post("/search", json={"title": "   ", "options": "", "type": "single"})

    assert response.status_code == 400
    assert response.json()["code"] == 0
    assert "title" in response.json()["msg"]


def test_validation_error_logs_request_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_log_validation_error(**kwargs: object) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(app_main, "log_validation_error", fake_log_validation_error)
    client = make_client()

    response = client.post("/search", json={"options": "", "type": "single"})

    assert response.status_code == 400
    assert calls
    assert calls[0]["method"] == "POST"
    assert calls[0]["path"] == "/search"
    assert calls[0]["content_type"] == "application/json"
    body = calls[0]["body"]
    errors = calls[0]["errors"]
    assert isinstance(body, bytes)
    assert b'"options"' in body
    assert errors


@pytest.mark.parametrize(
    ("type_value", "expected_type"),
    [
        ("单选题", QuestionType.single),
        ("多选题", QuestionType.multiple),
        ("判断题", QuestionType.judgement),
        ("填空题", QuestionType.completion),
    ],
)
def test_chinese_question_type_alias_is_accepted(
    type_value: str,
    expected_type: QuestionType,
) -> None:
    answerer = FakeAnswerer()
    client = make_client(answerer)

    response = client.post("/search", json={"title": "题目", "options": "", "type": type_value})

    assert response.status_code == 200
    assert response.json()["code"] == 1
    assert answerer.payloads[0].type == expected_type


def test_unsupported_question_type_falls_back_to_unknown() -> None:
    answerer = FakeAnswerer()
    client = make_client(answerer)

    response = client.post("/search", json={"title": "题目", "options": "", "type": "essay"})

    assert response.status_code == 200
    assert response.json()["code"] == 1
    assert answerer.payloads[0].type == QuestionType.unknown


def test_search_accepts_ocs_text_plain_json_payload() -> None:
    answerer = FakeAnswerer()
    client = make_client(answerer)
    payload = {
        "title": "题目",
        "options": " A. 选项A \n B. 选项B ",
        "type": "single",
    }

    response = client.post(
        "/search",
        content=json.dumps(payload, ensure_ascii=False),
        headers={"content-type": "text/plain;charset=UTF-8"},
    )

    assert response.status_code == 200
    assert response.json()["code"] == 1
    assert response.json()["question"] == "题目"
    assert answerer.payloads[0].options == "A. 选项A\nB. 选项B"


def test_malformed_text_plain_payload_returns_ocs_error_shape() -> None:
    client = make_client()

    response = client.post(
        "/search",
        content="not-json",
        headers={"content-type": "text/plain;charset=UTF-8"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == 0
    assert "无法解析 JSON 数据" in response.json()["msg"]
