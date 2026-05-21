import logging
from collections.abc import Mapping, Sequence
from typing import Any

from rich.logging import RichHandler

LOGGER_NAME = "ocs_answerer"
BODY_PREVIEW_LIMIT = 500
UVICORN_LOGGERS = ("uvicorn", "uvicorn.error")
LITELLM_LOGGERS = ("LiteLLM", "litellm")
logger = logging.getLogger(LOGGER_NAME)


def configure_logging() -> None:
    handler = get_console_handler()
    configure_logger(logger, handler=handler, level=logging.INFO, disabled=False)
    configure_uvicorn_loggers(handler)
    configure_litellm_loggers(handler)


def get_console_handler() -> RichHandler:
    for handler in logger.handlers:
        if isinstance(handler, RichHandler):
            return handler
    handler = RichHandler(
        log_time_format="%H:%M:%S",
        rich_tracebacks=True,
        show_path=False,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


def configure_logger(
    target: logging.Logger,
    *,
    handler: logging.Handler,
    level: int,
    disabled: bool,
) -> None:
    target.handlers = [handler]
    target.setLevel(level)
    target.disabled = disabled
    target.propagate = False


def configure_uvicorn_loggers(handler: logging.Handler) -> None:
    for name in UVICORN_LOGGERS:
        configure_logger(
            logging.getLogger(name),
            handler=handler,
            level=logging.INFO,
            disabled=False,
        )

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = []
    access_logger.disabled = True
    access_logger.propagate = False


def configure_litellm_loggers(handler: logging.Handler) -> None:
    for name in LITELLM_LOGGERS:
        configure_logger(
            logging.getLogger(name),
            handler=handler,
            level=logging.ERROR,
            disabled=False,
        )


def log_info(message: str) -> None:
    logger.info(message)


def log_error(message: str) -> None:
    logger.error(message)


def log_validation_error(
    *,
    method: str,
    path: str,
    client: str,
    content_type: str | None,
    content_length: str | None,
    body: bytes,
    errors: Sequence[Mapping[str, Any]],
) -> None:
    parts = [
        "\n请求校验失败",
        f"方法: {method}",
        f"路径: {path}",
        f"客户端: {client}",
        f"Content-Type: {content_type or '<missing>'}",
        f"Content-Length: {content_length or '<missing>'}",
        f"Body字节数: {len(body)}",
        f"Body预览: {format_body_preview(body)}",
        f"校验错误: {format_validation_errors(errors)}",
    ]
    logger.error("\n".join(parts))


def log_request(title: str, options: str, question_type: str) -> None:
    parts = [
        "\n新的请求",
        f"题目: {title}",
        f"类型: {question_type}",
    ]
    if options:
        parts.append(f"选项:\n{options.strip()}")
    logger.info("\n".join(parts))


def log_response(answer: str, analysis: str) -> None:
    logger.info("答案: %s", answer)
    logger.info("解析: %s", analysis)


def format_body_preview(body: bytes, limit: int = BODY_PREVIEW_LIMIT) -> str:
    if not body:
        return "<empty>"

    text = body.decode("utf-8", errors="replace")
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...<truncated {len(text) - limit} chars>"


def format_validation_errors(errors: Sequence[Mapping[str, Any]]) -> str:
    if not errors:
        return "<empty>"

    formatted: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.get("loc", []))
        error_type = str(error.get("type", "unknown"))
        message = str(error.get("msg", "validation failed"))
        if location:
            formatted.append(f"{location}: {message} ({error_type})")
        else:
            formatted.append(f"{message} ({error_type})")
    return "; ".join(formatted)
