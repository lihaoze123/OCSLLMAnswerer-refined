from typing import Annotated

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.llm import Answerer, LiteLLMAnswerer
from app.logging import configure_logging, log_error, log_request, log_response
from app.schemas import ErrorResponse, HealthResponse, SearchRequest, SearchResponse


def create_app(settings: Settings | None = None, answerer: Answerer | None = None) -> FastAPI:
    configure_logging()
    resolved_settings = settings or get_settings()
    resolved_answerer = answerer or LiteLLMAnswerer(resolved_settings)

    fastapi_app = FastAPI(title="OCS AI Answerer Server", version="0.1.0")
    fastapi_app.state.settings = resolved_settings
    fastapi_app.state.answerer = resolved_answerer

    @fastapi_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(msg=format_validation_error(exc)).model_dump(),
        )

    @fastapi_app.api_route("/", methods=["GET", "HEAD"], response_model=HealthResponse)
    def index() -> HealthResponse:
        return HealthResponse(msg="OCS ChatGPT Server is running")

    @fastapi_app.post("/search", response_model=SearchResponse)
    def search_answer(
        payload: Annotated[SearchRequest, Body(...)],
        request: Request,
    ) -> SearchResponse | JSONResponse:
        try:
            log_request(payload.title, payload.options, payload.type_label)
            result = request.app.state.answerer.answer(payload)
            log_response(result.answer, result.analysis)
            return SearchResponse(
                question=payload.title,
                answer=result.answer,
                analysis=result.analysis,
            )
        except Exception as exc:
            log_error(f"服务器内部错误: {exc}")
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(msg=str(exc)).model_dump(),
            )

    return fastapi_app


def format_validation_error(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "请求数据校验失败"
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", []) if part != "body")
    message = str(first.get("msg", "请求数据校验失败"))
    if location:
        return f"{location}: {message}"
    return message


app = create_app()
