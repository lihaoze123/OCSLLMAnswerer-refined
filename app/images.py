import base64
import mimetypes
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.logging import log_error

CHAOXING_HOST_SUFFIX = ".chaoxing.com"
CHAOXING_REFERER = "https://mooc1.chaoxing.com/"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
IMAGE_FETCH_TIMEOUT = 10.0
MAX_IMAGE_BYTES = 20 * 1024 * 1024

ImageFetcher = Callable[[str, str, float], str]


@dataclass(frozen=True)
class ImageUrlResolver:
    chaoxing_cookie: str | None
    fetcher: ImageFetcher | None = None
    timeout: float = IMAGE_FETCH_TIMEOUT

    def resolve(self, url: str) -> str | None:
        if not is_chaoxing_url(url):
            return url
        if not self.chaoxing_cookie:
            log_error("跳过超星图片下载: 未配置 CHAOXING_COOKIE")
            return None

        try:
            fetcher = self.fetcher or fetch_chaoxing_image_as_data_url
            return fetcher(url, self.chaoxing_cookie, self.timeout)
        except Exception as exc:
            log_error(f"超星图片下载失败，已跳过图片: {exc}")
            return None


def is_chaoxing_url(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host == "chaoxing.com" or host.endswith(CHAOXING_HOST_SUFFIX)


def fetch_chaoxing_image_as_data_url(
    url: str,
    cookie: str,
    timeout: float,
) -> str:
    headers = {
        "Cookie": cookie,
        "Referer": CHAOXING_REFERER,
        "User-Agent": DEFAULT_USER_AGENT,
    }

    try:
        chunks: list[bytes] = []
        total_bytes = 0
        with (
            httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client,
            client.stream("GET", url, headers=headers) as response,
        ):
            response.raise_for_status()
            content_type = resolve_image_content_type(
                response.headers.get("content-type"),
                url,
            )
            for chunk in response.iter_bytes():
                total_bytes += len(chunk)
                if total_bytes > MAX_IMAGE_BYTES:
                    raise RuntimeError("图片超过 20 MB 限制")
                chunks.append(chunk)
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"HTTP {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(str(exc)) from exc

    body = b"".join(chunks)
    return build_image_data_url(content_type, body)


def resolve_image_content_type(header_value: str | None, url: str) -> str:
    if header_value:
        content_type = header_value.split(";", maxsplit=1)[0].strip().lower()
        if content_type.startswith("image/"):
            return content_type
        raise RuntimeError(f"响应不是图片: {content_type}")

    guessed_type = mimetypes.guess_type(url)[0]
    if guessed_type and guessed_type.startswith("image/"):
        return guessed_type
    return "image/png"


def build_image_data_url(content_type: str, body: bytes) -> str:
    encoded = base64.b64encode(body).decode("ascii")
    return f"data:{content_type};base64,{encoded}"
