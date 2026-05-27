# Refactor AI and Image Input Architecture

## Goal

Refactor the OCS AI answer server as an overall architecture cleanup, not just an AI framework swap. Replace the current LiteLLM/OpenAI Chat Completions style implementation with Pydantic AI, and redesign image input handling using Miaozeqiu/ZError as a reference where it fits this Python/FastAPI service.

## What I Already Know

* The user wants a one-time breaking migration rather than preserving the old `LLM_*`/`OPENAI_*` compatibility contract.
* LiteLLM should be removed rather than kept as a provider routing layer.
* The public `/search` behavior should still tolerate model failures and return the existing OCS-compatible success shape with fallback answer text.
* The scope is now an overall refactor, including image input architecture, not only replacing the AI call framework.
* ZError is the explicit external reference for image input behavior and broader OCS AI题库 ergonomics.
* Current AI code is concentrated in `app/llm.py`; prompt/message construction is in `app/prompts.py`; Chaoxing image handling is in `app/images.py`; settings are in `app/config.py`.
* ZError separates URL/image questions from text-only questions, downloads images locally as data URLs, caches images, normalizes small/transparent images, and uses a separate selected vision model for image questions.

## Assumptions

* The FastAPI `/` and `/search` endpoints remain because this project is still an OCS local AI题库 server.
* The answer response contract remains `code/question/answer/analysis`.
* The refactor may change internal modules, settings names, dependency list, README, and tests.

## Open Questions

* Ready to start implementation after this PRD, or should more design details be resolved first?

## Requirements

* Use Pydantic AI for model invocation and structured output validation.
* Remove LiteLLM dependency and LiteLLM-specific JSON mode detection.
* Replace hand-written model response JSON extraction with Pydantic AI `output_type=ModelAnswer` or an equivalent Pydantic AI structured output path.
* Keep robust outer error handling so model/API/validation failures do not break the OCS caller flow.
* Research ZError image handling before finalizing the local image input design.
* Introduce a dedicated backend image-question pipeline inspired by ZError: ordered URL parsing, local image fetching, image normalization, multimodal input construction, and image-aware model routing.
* Configure text and vision models separately. Text-only questions use the text model; image-containing questions require a configured vision model.
* If an image-containing question arrives without a configured vision model, return the existing fallback answer rather than silently using the text model.
* If any image URL in a question cannot be fetched and prepared, fail the model run and return the existing fallback answer. Do not skip failed images and continue answering.
* Do not add image caching in this task; caching will be designed later as a unified concern.
* Image preparation in this task is limited to local download, image media-type validation/detection, max-size enforcement, and Pydantic AI `BinaryContent` construction.
* Replace Chaoxing-only image resolution with a general image downloader inspired by ZError:
  * Try browser-like, simplified, and mobile-like request strategies.
  * Use provider-aware referers for known education domains such as Chaoxing and Zhihuishu.
  * Enforce the existing max image byte limit.
  * Detect media type from magic bytes for `png`, `jpeg`, `gif`, `webp`, and `bmp`, with header/URL fallback as needed.
  * Return image bytes plus media type for Pydantic AI `BinaryContent`.
* Do not add Pillow-based white-background compositing, transparent-image inversion, minimum-size resizing, or provider-error-triggered image resize retry in this task.
* Use a simple single-provider configuration shape with separate text and vision model names, such as `AI_PROVIDER`, `AI_API_KEY`, `AI_BASE_URL`, `AI_TEXT_MODEL`, `AI_VISION_MODEL`, `AI_TIMEOUT`, and `AI_TEMPERATURE`.
* Do not add ZError-style multi-provider/model catalog management in this task.
* Implement image URL recognition as a fixed built-in parser, not a hot-updated or user-configurable algorithm.
* Put image URL parsing behind a dedicated module with testable match/span/normalized URL/trailing text APIs inspired by ZError.
* Keep the public `/search` response contract and OCS-facing answer formatting unchanged.
* Preserve answer format intent: single-choice returns option content, multiple-choice uses `#`, judgement returns `正确`/`错误`, completion returns direct fill-in content.
* Do not add ZError-like local answer cache, question-bank database, folder classification, pending-correction workflow, or UI/SSE model-call bridge in this task.

## Acceptance Criteria

* [x] Runtime AI answer generation is implemented through Pydantic AI.
* [x] LiteLLM is removed from dependencies and application code.
* [x] Tests cover model success, model failure fallback, configuration validation, and image input construction.
* [x] Documentation describes the new configuration and image handling behavior.
* [x] Existing OCS API tests continue to pass or are intentionally updated to the new agreed contract.

## Definition of Done

* Tests added or updated for changed behavior.
* `ruff`, `ty`, and `pytest` pass.
* README/config examples are updated.
* Trellis specs reviewed for any new project conventions worth recording.

## Out of Scope

* Building a Tauri/Vue desktop UI like ZError.
* Adding remote sync or a full local题库 management UI.
* Adding local answer cache/question-bank database behavior.
* Adding image cache behavior.
* Adding multi-provider/model catalog management.
* Adding remote image-matching algorithms, user-defined regexes, or external script execution.

## Technical Notes

* Reference repository: https://github.com/Miaozeqiu/ZError
* ZError local clone for research: `/tmp/ZError`
* Research notes: `research/zerror-image-architecture.md`
* Research notes: `research/pydantic-ai-integration.md`
* Pydantic AI docs researched so far:
  * https://pydantic.dev/docs/ai/core-concepts/output/
  * https://pydantic.dev/docs/ai/models/openai/
  * https://pydantic.dev/docs/ai/advanced-features/input/
