# Ensure AI Can Read Question Images

## Goal

When OCS sends a question whose title or options contain image URLs, the service should pass those images to the LLM as visual inputs instead of leaving them as plain text. This lets vision-capable OpenAI-compatible models inspect table screenshots and other embedded question images before answering.

## What I already know

* The user provided an example SQL multiple-choice question containing a Chaoxing image URL in the title.
* The correct SQL answer for the example is the option using `学号 IN (SELECT DISTINCT 学号 FROM 选课 WHERE 课号='2002')`.
* The current OCS config in `README.md` sends `title`, `options`, and `type` only.
* `app/schemas.py` validates `SearchRequest` with only `title`, `options`, and `type`.
* `app/prompts.py` currently builds a pure text user message, so image URLs are not passed as model-visible images.
* `app/llm.py` sends the messages through LiteLLM's Chat Completions-compatible `completion()` call.

## Assumptions

* Image URLs may appear inline in `title` or `options`, not necessarily in a separate request field.
* The MVP should work with vision-capable OpenAI-compatible models by using Chat Completions image content blocks.
* If the configured model/provider does not support image inputs, the existing LLM failure fallback remains acceptable.

## Requirements

* Detect image URLs in the question title and options.
* Include detected images in the LLM user message using multimodal message content.
* Keep the existing OCS `/search` request and response contracts compatible.
* Preserve the original title/options text so the model still sees the full question context.
* Add tests covering image URL extraction and multimodal message construction.
* Update user-facing docs/config notes if behavior or model requirements change.

## Acceptance Criteria

* [x] A request whose `title` contains `https://p.ananas.chaoxing.com/...png` results in a user message that includes an `image_url` content block.
* [x] A request without image URLs still builds the same pure-text style message shape expected by existing tests.
* [x] `/search` still returns the existing OCS success and fallback response shape.
* [x] Test suite passes with `uv run pytest`.
* [x] Static checks pass with `uv run ruff check` and `uv run ty check`.

## Definition of Done

* Tests added or updated for the image-question path.
* Lint, type-check, and tests pass.
* README documents that image questions require a vision-capable configured model.
* No persistence, caching, or real network image fetching is introduced unless required later.

## Technical Approach

Recommended MVP: auto-extract image URLs from `title` and `options`, keep the prompt text intact, and build the user message as a content list containing the text prompt plus one `image_url` block per detected image. This stays within the existing OCS payload shape and uses the standard OpenAI-compatible multimodal Chat Completions format supported by LiteLLM for capable providers.

## Decision (ADR-lite)

**Context**: The current service receives OCS text fields and sends a pure-text prompt to LiteLLM, so image-only question content is invisible to the model.

**Decision**: Prefer pass-through multimodal `image_url` content blocks extracted from existing fields over adding OCR, downloading images server-side, or changing the OCS request contract.

**Consequences**: This is low-risk and preserves compatibility, but it requires the configured LLM model/provider to support image inputs and to be able to access the image URL.

## Out of Scope

* OCR fallback for text-only models.
* Server-side image download, base64 conversion, caching, or retry queues.
* Changing the OCS browser-script payload contract.
* Guaranteeing image support for every configured model/provider.

## Technical Notes

* Impacted files: `app/prompts.py`, `tests/test_prompts.py`, `README.md`, and `.trellis/spec/backend/quality-guidelines.md`.
* Backend spec index: `.trellis/spec/backend/index.md`.
* Relevant checks from project docs: `uv run ruff format`, `uv run ruff check`, `uv run ty check`, `uv run pytest`.
