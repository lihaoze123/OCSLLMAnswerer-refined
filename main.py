import uvicorn

from app.config import get_settings
from app.logging import configure_logging, log_info


def main() -> None:
    configure_logging()
    settings = get_settings()
    log_info(f"服务启动在 http://{settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        access_log=False,
        log_config=None,
        reload=False,
        factory=False,
    )


if __name__ == "__main__":
    main()
