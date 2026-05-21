from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import JsonMode, Settings
from app.main import create_app
from app.schemas import ModelAnswer, SearchRequest


class FakeAnswerer:
    def __init__(self) -> None:
        self.payloads: list[SearchRequest] = []

    def answer(self, payload: SearchRequest) -> ModelAnswer:
        self.payloads.append(payload)
        return ModelAnswer(answer="A", analysis="测试解析")


def make_client(answerer: FakeAnswerer | None = None) -> TestClient:
    settings = Settings(
        llm_api_key=SecretStr("test-key"),
        llm_model="test-model",
        llm_json_mode=JsonMode.off,
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


def test_search_preserves_llm_failure_fallback_success_shape() -> None:
    settings = Settings(llm_model=None, llm_json_mode=JsonMode.off)
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


def test_invalid_question_type_returns_ocs_error_shape() -> None:
    client = make_client()

    response = client.post("/search", json={"title": "题目", "options": "", "type": "essay"})

    assert response.status_code == 400
    assert response.json()["code"] == 0
    assert "type" in response.json()["msg"]
