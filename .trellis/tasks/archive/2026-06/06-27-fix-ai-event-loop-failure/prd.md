# Fix AI Event Loop Failure

## Goal

Fix the production AI answer path so `/search` can call Pydantic AI from FastAPI without raising `This event loop is already running`, while preserving the existing OCS response contract and fallback behavior.

## What I Already Know

* User observed: `AI 调用或结构化输出失败: This event loop is already running`, followed by fallback answer `未知` and analysis `服务器处理出错`.
* `app/main.py` defines `/search` as an async FastAPI route and currently calls `request.app.state.answerer.answer(payload)` synchronously.
* `app/llm.py` implements `PydanticAIAnswerer.answer()` as a synchronous method and calls `agent.run_sync(...)`.
* Calling a sync wrapper that manages an event loop from inside FastAPI's already-running event loop is the likely root cause.
* `tests/test_api.py` verifies the public failure response remains HTTP 200 with `code: 1`, `answer: 未知`, and `analysis: 服务器处理出错` for AI-layer failures.

## Assumptions

* The intended behavior is to perform the real AI call successfully rather than fall back when the server is healthy.
* The fallback response shape should remain unchanged for configuration, provider, validation, or structured-output failures.
* It is acceptable to make the answerer interface async if tests and route call sites are updated consistently.

## Open Questions

* Resolved: scope is limited to fixing the event-loop bug while preserving existing fallback behavior.

## Requirements

* The `/search` route must await the AI answer path instead of invoking a sync event-loop wrapper inside FastAPI's event loop.
* The Pydantic AI call should use the library's async API for the live request path.
* The current OCS success and AI fallback response contracts must remain unchanged.
* Existing image-question prompt construction and binary image handling must keep working.
* Tests should cover the async answerer path without making network calls.

## Acceptance Criteria

* [x] A normal `/search` request can call a fake async Pydantic AI agent and return the model answer.
* [x] Missing model configuration still returns the existing fallback answer.
* [x] Image questions still download images and pass `BinaryContent` in the prompt payload.
* [x] Existing API response-shape tests pass.
* [x] Lint/type checks or the project's closest available test command pass.

## Definition of Done

* Tests added/updated where behavior changes.
* Project quality checks run and reported.
* Trellis spec update considered after implementation.

## Out of Scope

* Changing provider settings, model selection, prompts, or the public OCS response schema.
* Adding retry/backoff behavior beyond Pydantic AI's existing agent retry setting.
* Changing image download concurrency or timeout behavior.

## Technical Approach

Convert the answer path from synchronous to async:

* Update the `Answerer` and `AgentRunner` protocols to expose async methods.
* Change `PydanticAIAnswerer.answer()` and `_run_agent()` to async methods.
* Replace `agent.run_sync(...)` with the Pydantic AI async run method.
* Update `/search` to `await request.app.state.answerer.answer(payload)`.
* Update test fakes and tests to await the answerer where needed.

## Decision (ADR-lite)

**Context**: FastAPI already runs request handlers inside an event loop. Pydantic AI's synchronous runner attempts to manage event-loop execution itself, which fails under the running server loop.

**Decision**: Use an async answerer interface and call Pydantic AI through its async API from the live FastAPI path.

**Consequences**: Route and test fakes must become async-aware. This keeps the server concurrency model coherent and avoids thread or nested-loop workarounds.

## Technical Notes

* Relevant code: `app/main.py`, `app/llm.py`, `tests/test_api.py`, `tests/test_llm.py`.
* Relevant specs: `.trellis/spec/backend/index.md`, plus backend quality/error/logging guidance before implementation.
