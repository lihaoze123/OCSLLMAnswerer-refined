import logging

from rich.logging import RichHandler

from app import logging as app_logging


def test_configure_logging_is_idempotent_and_unifies_known_loggers() -> None:
    app_logging.configure_logging()
    app_logging.configure_logging()

    app_handler = app_logging.logger.handlers[0]
    assert isinstance(app_handler, RichHandler)
    assert app_logging.logger.handlers == [app_handler]

    assert logging.getLogger("uvicorn.error").handlers == [app_handler]
    assert logging.getLogger("uvicorn.error").disabled is False
    assert logging.getLogger("uvicorn.access").handlers == []
    assert logging.getLogger("uvicorn.access").disabled is True
    assert logging.getLogger("LiteLLM").handlers == [app_handler]
    assert logging.getLogger("LiteLLM").level == logging.ERROR
