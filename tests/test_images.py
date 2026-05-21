from typing import Any

import app.images as images_module
from app.images import (
    ImageUrlResolver,
    build_image_data_url,
    fetch_chaoxing_image_as_data_url,
    is_chaoxing_url,
    resolve_image_content_type,
)


def test_build_image_data_url_encodes_bytes() -> None:
    assert build_image_data_url("image/png", b"abc") == "data:image/png;base64,YWJj"


def test_resolve_image_content_type_prefers_image_header() -> None:
    assert resolve_image_content_type(
        "image/jpeg; charset=binary", "https://example.com/a.png"
    ) == ("image/jpeg")


def test_is_chaoxing_url_matches_subdomains() -> None:
    assert is_chaoxing_url("https://p.ananas.chaoxing.com/star3/origin/a.png")
    assert not is_chaoxing_url("https://example.com/a.png")


def test_image_url_resolver_fetches_chaoxing_images_with_cookie() -> None:
    captured: dict[str, object] = {}

    def fake_fetcher(url: str, cookie: str, timeout: float) -> str:
        captured.update({"url": url, "cookie": cookie, "timeout": timeout})
        return "data:image/png;base64,YWJj"

    resolver = ImageUrlResolver(
        "secret-cookie",
        fetcher=fake_fetcher,
        timeout=3,
    )
    url = "https://p.ananas.chaoxing.com/star3/origin/a.png"

    assert resolver.resolve(url) == "data:image/png;base64,YWJj"
    assert captured == {
        "url": url,
        "cookie": "secret-cookie",
        "timeout": 3,
    }


def test_image_url_resolver_skips_chaoxing_without_cookie() -> None:
    resolver = ImageUrlResolver(None)

    assert resolver.resolve("https://p.ananas.chaoxing.com/star3/origin/a.png") is None


def test_image_url_resolver_keeps_non_chaoxing_url() -> None:
    resolver = ImageUrlResolver(None)

    assert resolver.resolve("https://example.com/a.png") == "https://example.com/a.png"


def test_image_url_resolver_skips_failed_chaoxing_fetch() -> None:
    def fake_fetcher(url: str, cookie: str, timeout: float) -> str:
        raise RuntimeError("HTTP 403")

    resolver = ImageUrlResolver("secret-cookie", fetcher=fake_fetcher)

    assert resolver.resolve("https://p.ananas.chaoxing.com/star3/origin/a.png") is None


def test_fetch_chaoxing_image_always_disables_ssl_verification(monkeypatch: Any) -> None:
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
            return [b"abc"]

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
            captured.update({"method": method, "url": url, "cookie": headers["Cookie"]})
            return FakeResponse()

    monkeypatch.setattr(images_module.httpx, "Client", FakeClient)

    data_url = fetch_chaoxing_image_as_data_url(
        "https://p.ananas.chaoxing.com/star3/origin/a.png",
        "secret-cookie",
        5.0,
    )

    assert data_url == "data:image/png;base64,YWJj"
    assert captured == {
        "timeout": 5.0,
        "follow_redirects": True,
        "verify": False,
        "method": "GET",
        "url": "https://p.ananas.chaoxing.com/star3/origin/a.png",
        "cookie": "secret-cookie",
    }
