from typing import Any

import app.images as images_module
from app.images import (
    CHAOXING_REFERER,
    DEFAULT_REFERER,
    ImageDownloader,
    build_request_strategies,
    detect_image_media_type,
    is_chaoxing_url,
    resolve_image_media_type,
    resolve_referer,
)


def test_detect_image_media_type_uses_magic_bytes() -> None:
    assert detect_image_media_type(b"\x89PNG\r\n\x1a\nabc") == "image/png"
    assert detect_image_media_type(b"\xff\xd8\xffabc") == "image/jpeg"
    assert detect_image_media_type(b"GIF89aabc") == "image/gif"
    assert detect_image_media_type(b"RIFFxxxxWEBPabc") == "image/webp"
    assert detect_image_media_type(b"BMabc") == "image/bmp"
    assert detect_image_media_type(b"abc") is None


def test_resolve_image_media_type_falls_back_to_image_header() -> None:
    assert (
        resolve_image_media_type(
            b"unknown",
            "image/jpeg; charset=binary",
            "https://example.com/a.png",
        )
        == "image/jpeg"
    )


def test_is_chaoxing_url_matches_subdomains() -> None:
    assert is_chaoxing_url("https://p.ananas.chaoxing.com/star3/origin/a.png")
    assert not is_chaoxing_url("https://example.com/a.png")


def test_resolve_referer_uses_known_domain_referers() -> None:
    assert resolve_referer("https://p.ananas.chaoxing.com/a.png") == CHAOXING_REFERER
    assert resolve_referer("https://example.com/a.png") == DEFAULT_REFERER


def test_build_request_strategies_includes_chaoxing_cookie_only_for_chaoxing() -> None:
    chaoxing_headers = build_request_strategies(
        "https://p.ananas.chaoxing.com/a.png",
        "secret-cookie",
    )[0].headers
    public_headers = build_request_strategies("https://example.com/a.png", "secret-cookie")[
        0
    ].headers

    assert chaoxing_headers["Cookie"] == "secret-cookie"
    assert "Cookie" not in public_headers


def test_image_downloader_fetches_with_browser_strategy(monkeypatch: Any) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        headers = {"content-type": "image/png"}

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self) -> list[bytes]:
            return [b"\x89PNG\r\n\x1a\nabc"]

    class FakeClient:
        def __init__(self, *, timeout: float, follow_redirects: bool, verify: bool) -> None:
            captured.update(
                {
                    "timeout": timeout,
                    "follow_redirects": follow_redirects,
                    "verify": verify,
                }
            )

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def stream(self, method: str, url: str, headers: dict[str, str]) -> FakeResponse:
            captured.update(
                {
                    "method": method,
                    "url": url,
                    "referer": headers["Referer"],
                    "user_agent": headers["User-Agent"],
                    "cookie": headers["Cookie"],
                }
            )
            return FakeResponse()

    monkeypatch.setattr(images_module.httpx, "Client", FakeClient)

    image = ImageDownloader("secret-cookie", timeout=5.0).download(
        "https://p.ananas.chaoxing.com/star3/origin/a.png"
    )

    assert image.media_type == "image/png"
    assert image.data == b"\x89PNG\r\n\x1a\nabc"
    assert captured["timeout"] == 5.0
    assert captured["follow_redirects"] is True
    assert captured["verify"] is False
    assert captured["method"] == "GET"
    assert captured["referer"] == CHAOXING_REFERER
    assert captured["cookie"] == "secret-cookie"


def test_image_downloader_enforces_size_limit(monkeypatch: Any) -> None:
    class FakeResponse:
        headers = {"content-type": "image/png"}

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self) -> list[bytes]:
            return [b"too-large"]

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            return None

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def stream(self, method: str, url: str, headers: dict[str, str]) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(images_module.httpx, "Client", FakeClient)

    try:
        ImageDownloader(max_bytes=1).download("https://example.com/a.png")
    except RuntimeError as exc:
        assert "图片下载失败" in str(exc)
    else:
        raise AssertionError("expected oversized image download to fail")
