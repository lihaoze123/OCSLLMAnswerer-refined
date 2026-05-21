import logging

from rich.logging import RichHandler

LOGGER_NAME = "ocs_answerer"
logger = logging.getLogger(LOGGER_NAME)


def configure_logging() -> None:
    if logger.handlers:
        return

    handler = RichHandler(
        log_time_format="%H:%M:%S",
        rich_tracebacks=True,
        show_path=False,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def log_info(message: str) -> None:
    logger.info(message)


def log_error(message: str) -> None:
    logger.error(message)


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
