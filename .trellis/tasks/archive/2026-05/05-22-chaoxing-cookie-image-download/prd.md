# Support Chaoxing Cookie Image Download

## Goal

Fix image-question failures caused by OpenAI/LiteLLM being unable to download
Chaoxing `p.ananas.chaoxing.com` image URLs directly. The local service should
use the operator-provided `CHAOXING_COOKIE` environment variable to fetch those
images itself, convert successful downloads into data URLs, and send those data
URLs to the vision model.

## Requirements

* Add a `CHAOXING_COOKIE` setting, loaded from the environment or `.env`.
* For extracted Chaoxing image URLs, try to download each image locally before
  calling LiteLLM.
* Use browser-like request headers for Chaoxing image downloads, including
  `Cookie: <CHAOXING_COOKIE>`, `Referer: https://mooc1.chaoxing.com/`, and a
  normal user agent.
* Convert successfully fetched images into
  `data:<content-type>;base64,<payload>` strings before attaching them as
  Chat Completions `image_url` blocks.
* If no `CHAOXING_COOKIE` is configured or a download fails, keep the service
  tolerant: continue with the original URL or text prompt rather than crashing
  the OCS request path.
* Do not log cookie values or other secrets.

## Acceptance Criteria

* [ ] A Chaoxing image URL can be transformed into a base64 data URL when
      `CHAOXING_COOKIE` is configured and the image fetch succeeds.
* [ ] Image download failures do not make `/search` return a server error.
* [ ] Existing text-only prompt behavior remains unchanged.
* [ ] Existing non-Chaoxing image URL behavior remains compatible by continuing
      to pass public URLs through directly.
* [ ] Tests cover successful data URL conversion and download-failure fallback.

## Definition of Done

* Tests added or updated for the image handling behavior.
* `uv run ruff format --check`, `uv run ruff check`, `uv run ty check`, and
  `uv run pytest` pass.
* README documents `CHAOXING_COOKIE` and the new image-fetching behavior.
* README documents that local Chaoxing image downloads intentionally skip SSL
  certificate verification.

## Technical Approach

* Keep URL extraction in `app.prompts`.
* Add image resolution near the LiteLLM gateway so prompt construction can still
  be tested independently and answer requests can apply environment-driven
  behavior.
* Use a small, injectable fetcher abstraction or function so tests can avoid
  real network calls.
* Use `httpx` as a runtime dependency for image fetches so timeout, redirects,
  HTTP status errors, streaming, and fixed `verify=False` behavior are explicit.
* Preserve LiteLLM as the model gateway and preserve OCS response shapes.

## Decision (ADR-lite)

**Context**: Chaoxing image URLs can require login cookies or anti-hotlinking
headers. OpenAI servers cannot provide the user's Chaoxing browser session, so
direct remote `image_url` fetches can fail with HTTP 403.

**Decision**: The local service will optionally resolve Chaoxing image URLs into
data URLs using `CHAOXING_COOKIE` before sending the request to LiteLLM.

**Consequences**: This keeps vision answers working for protected Chaoxing
images while keeping the cookie local. Failed fetches still degrade gracefully,
so the OCS integration does not break because of one inaccessible image.

## Out of Scope

* OCR fallback for inaccessible images.
* Persistent image caching or image storage.
* Browser automation to automatically extract Chaoxing cookies.
* Provider-specific SDK replacement for LiteLLM.

## Technical Notes

* Relevant files inspected: `app/prompts.py`, `app/llm.py`, `app/config.py`,
  `tests/test_prompts.py`, `tests/test_llm.py`, `README.md`, `pyproject.toml`.
* Backend specs consulted: `.trellis/spec/backend/index.md`,
  `.trellis/spec/backend/quality-guidelines.md`,
  `.trellis/spec/backend/error-handling.md`,
  `.trellis/spec/backend/logging-guidelines.md`.
* `httpx` was moved from the dev dependency group to runtime dependencies
  because image fetching is part of the production request path.
