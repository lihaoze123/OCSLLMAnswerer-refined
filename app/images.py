import mimetypes
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

CHAOXING_HOST_SUFFIX = ".chaoxing.com"
ZHISHU_HOST_SUFFIX = ".zhihuishu.com"
CHAOXING_REFERER = "https://mooc1-1.chaoxing.com/"
ZHISHU_REFERER = "https://www.zhihuishu.com/"
DEFAULT_REFERER = "https://www.google.com/"
IMAGE_FETCH_TIMEOUT = 10.0
MAX_IMAGE_BYTES = 20 * 1024 * 1024

DESKTOP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
SIMPLE_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


@dataclass(frozen=True)
class DownloadedImage:
    data: bytes
    media_type: str


@dataclass(frozen=True)
class RequestStrategy:
    name: str
    headers: dict[str, str]


HttpClientFactory = Callable[..., httpx.Client]


@dataclass(frozen=True)
class ImageDownloader:
    chaoxing_cookie: str | None = None
    timeout: float = IMAGE_FETCH_TIMEOUT
    max_bytes: int = MAX_IMAGE_BYTES
    client_factory: HttpClientFactory | None = None

    def download(self, url: str) -> DownloadedImage:
        errors: list[str] = []

        for strategy in build_request_strategies(url, self.chaoxing_cookie):
            try:
                return self._download_with_strategy(url, strategy)
            except Exception as exc:
                errors.append(f"{strategy.name}: {exc}")

        raise RuntimeError(f"图片下载失败: {'; '.join(errors)}")

    def _download_with_strategy(self, url: str, strategy: RequestStrategy) -> DownloadedImage:
        chunks: list[bytes] = []
        total_bytes = 0
        verify = not is_chaoxing_url(url)

        with (
            (self.client_factory or httpx.Client)(
                timeout=self.timeout,
                follow_redirects=True,
                verify=verify,
            ) as client,
            client.stream("GET", url, headers=strategy.headers) as response,
        ):
            response.raise_for_status()
            content_type = response.headers.get("content-type")
            for chunk in response.iter_bytes():
                total_bytes += len(chunk)
                if total_bytes > self.max_bytes:
                    raise RuntimeError("图片超过 20 MB 限制")
                chunks.append(chunk)

        data = b"".join(chunks)
        media_type = resolve_image_media_type(data, content_type, url)
        return DownloadedImage(data=data, media_type=media_type)


def build_request_strategies(url: str, chaoxing_cookie: str | None = None) -> list[RequestStrategy]:
    referer = resolve_referer(url)
    cookie_headers = {"Cookie": chaoxing_cookie} if chaoxing_cookie and is_chaoxing_url(url) else {}

    return [
        RequestStrategy(
            name="完整浏览器伪装",
            headers={
                "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
                "Upgrade-Insecure-Requests": "1",
                "DNT": "1",
                "Connection": "keep-alive",
                "Referer": referer,
                "User-Agent": DESKTOP_USER_AGENT,
                **cookie_headers,
            },
        ),
        RequestStrategy(
            name="简化请求头",
            headers={
                "Accept": "image/*,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": referer,
                "User-Agent": SIMPLE_USER_AGENT,
                **cookie_headers,
            },
        ),
        RequestStrategy(
            name="移动端伪装",
            headers={
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh-Hans;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": referer,
                "User-Agent": MOBILE_USER_AGENT,
                **cookie_headers,
            },
        ),
    ]


def resolve_referer(url: str) -> str:
    host = urlparse(url).hostname or ""
    if is_chaoxing_host(host):
        return CHAOXING_REFERER
    if is_zhishu_host(host):
        return ZHISHU_REFERER
    return DEFAULT_REFERER


def is_chaoxing_url(url: str) -> bool:
    return is_chaoxing_host(urlparse(url).hostname or "")


def is_chaoxing_host(host: str) -> bool:
    return host == "chaoxing.com" or host.endswith(CHAOXING_HOST_SUFFIX)


def is_zhishu_host(host: str) -> bool:
    return host == "zhihuishu.com" or host.endswith(ZHISHU_HOST_SUFFIX)


def resolve_image_media_type(data: bytes, header_value: str | None, url: str) -> str:
    magic_type = detect_image_media_type(data)
    if magic_type:
        return magic_type

    if header_value:
        content_type = header_value.split(";", maxsplit=1)[0].strip().lower()
        if content_type.startswith("image/"):
            return content_type
        raise RuntimeError(f"响应不是图片: {content_type}")

    guessed_type = mimetypes.guess_type(url)[0]
    if guessed_type and guessed_type.startswith("image/"):
        return guessed_type
    raise RuntimeError("无法识别图片类型")


def detect_image_media_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"BM"):
        return "image/bmp"
    return None
