# Modernize Project Architecture and Toolchain

## Goal

Refactor the current compact Flask-based OCS AI Answerer into a modern,
maintainable local OCS answer service while preserving the existing product
positioning, OCS integration contract, and OpenAI-compatible provider support.
The modernization target includes current Python tooling such as `uv`, `ruff`,
and `ty`, plus a FastAPI-based web layer if the compatibility and operational
costs stay low.

## What I Already Know

* The current runtime is a single-file Flask application in `main.py`.
* The service exposes `GET/HEAD /` for health and `POST /search` for OCS answer
  lookup.
* The external OCS contract uses request fields `title`, `options`, and `type`.
* Successful `/search` responses currently include `code`, `question`,
  `answer`, and `analysis`; failures use `code: 0` plus `msg`.
* The OCS consumer config in `ocs_config.json` checks `res.code === 1` and uses
  `res.question` plus `res.answer`.
* The service must remain compatible with OpenAI-format providers via
  `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, and optional `OPENAI_MODEL`.
* Current model-output cleanup strips `<think>...</think>`, Markdown JSON fences,
  and surrounding text before parsing the first JSON object.
* Current dependency management is already based on `uv.lock` and
  `pyproject.toml`.
* The project targets Python 3.13 via both `pyproject.toml` and
  `.python-version`.
* There is no automated test runner, formatter, linter, or type checker
  configured yet.
* There is no database, cache, persistent storage, or migration system.
* The README is user-facing and still describes Flask, Python 3.8+, and
  `requirements.txt`, so it is stale relative to the current `uv` project
  metadata.
* The user chose target shape A: keep the original local OCS answer server
  product positioning unchanged.
* The user wants a maximum refactor within that product boundary, with package
  choices based on current Python/FastAPI best practices rather than preserving
  older dependencies by default.
* The user provided a reference architecture centered on FastAPI, Pydantic v2,
  `pydantic-settings`, typed request/response models, structured LLM outputs
  where possible, categorized OpenAI SDK errors, standard logging, pytest,
  Ruff, and deployable ASGI startup.
* OpenAI official models and OpenAI's current API best practices are the primary
  LLM design target.
* The LLM integration should use a minimal architecture and maximize
  compatibility with mainstream providers that support the OpenAI API.
* DeepSeek should be used as an important OpenAI-compatible provider reference
  to avoid OpenAI-only assumptions.
* DeepSeek's official docs emphasize OpenAI-compatible Chat Completions and JSON
  Output via `response_format={"type": "json_object"}`, not Responses API.
* OCS AnswererWrapper examples commonly guard handler output with
  `res.code === 1` and return `[question, answer]` for successful answers.
* The user wants LLM access to go through a generic AI gateway library rather
  than tying the implementation directly to the OpenAI SDK.

## Assumptions

* Backward compatibility with OCS is required unless explicitly rejected.
* Provider compatibility is more important than using a provider-specific SDK.
* A large refactor should introduce compatibility tests before changing the
  framework or module structure.
* The new architecture should split request routing, configuration, schemas,
  LLM calls, prompt construction, response parsing, and logging into focused
  modules without becoming a large platform-style architecture.
* Persistence remains out of scope unless the product goal changes.

## Open Questions

* None. Awaiting final user confirmation before implementation.

## Requirements

* Preserve OCS-compatible `/search` request and response behavior unless a
  deliberate migration plan is defined.
* Use strict OCS API compatibility during the FastAPI migration:
  * Preserve `GET/HEAD /` and `POST /search`.
  * Preserve default local serving on `0.0.0.0:5000`.
  * Preserve request fields `title`, `options`, and `type`.
  * Preserve success response fields `code`, `question`, `answer`, and
    `analysis`.
  * Preserve failure response shape using `code: 0` plus `msg`.
  * Preserve `code: 1` / `code: 0` semantics used by `ocs_config.json`.
* Keep the service a local OCS answer backend; do not expand scope into a
  production platform, admin UI, account system, history store, or题库 platform.
* Migrate the web layer from Flask to FastAPI.
* Keep the existing public endpoints during migration: `GET/HEAD /` and
  `POST /search`.
* Use a compact module layout; do not over-split into a full platform-style
  `api/services/providers/domain/infrastructure` hierarchy.
* Keep modules aligned to real responsibilities only, such as app/routes,
  settings, LLM client/prompting, response parsing, and terminal logging.
* Implement the compact package layout as:
  * `app/main.py` for FastAPI app creation and routes.
  * `app/config.py` for `pydantic-settings`.
  * `app/schemas.py` for Pydantic request/response/answer models and enums.
  * `app/prompts.py` for prompt construction and question-type instructions.
  * `app/llm.py` for synchronous OpenAI-compatible client calls and parsing.
  * `app/logging.py` for logging setup and local readable request/response logs.
  * root `main.py` for the compatible startup entrypoint.
* Use Pydantic models for API boundaries and LLM answer objects, including
  request validation for title/options/type and response serialization for the
  OCS contract.
* Validate `type` as a strict enum of supported OCS question types:
  `single`, `multiple`, `judgement`, `completion`, and `unknown`. Other values
  should return an OCS-compatible validation error with `code: 0`.
* Convert FastAPI/Pydantic validation failures on `/search` into OCS-compatible
  error responses using `{"code": 0, "msg": "..."}` rather than exposing
  FastAPI's default `{"detail": ...}` response body.
* Preserve `python main.py` as the user-facing startup entrypoint. The entrypoint
  may internally launch uvicorn for the FastAPI app.
* Document `uv run python main.py` as the primary run command.
* Document an ASGI server command such as `uv run uvicorn ... --host 0.0.0.0
  --port 5000` for users who want a direct deployable server command.
* Keep provider configuration environment-driven.
* Use new generic `LLM_*` settings as the primary configuration surface:
  `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_TIMEOUT`.
* Preserve backward-compatible fallback to existing `OPENAI_API_KEY`,
  `OPENAI_BASE_URL`, and `OPENAI_MODEL` when the equivalent `LLM_*` setting is
  absent.
* Require `LLM_MODEL` or fallback `OPENAI_MODEL` to be explicitly configured;
  do not hard-code a default model name.
* Default LLM integration should use the smallest common OpenAI-compatible
  surface across mainstream providers: Chat Completions through the gateway
  abstraction.
* Use LiteLLM Python SDK in-process as the gateway library. Do not require users
  to run LiteLLM Proxy Server for this local OCS service.
* Do not make Responses API the default path because the project prioritizes
  minimal architecture and broad OpenAI-compatible provider support.
* Do not expose or implement a Responses API mode in this refactor. Standardize
  on Chat Completions/LiteLLM `completion()` only.
* Enable Chat Completions JSON mode when LiteLLM reports that the configured
  model/provider supports `response_format`.
* When JSON mode is enabled, pass `response_format={"type": "json_object"}` and
  include explicit JSON output instructions in the prompt.
* When LiteLLM reports no `response_format` support, omit the parameter and rely
  on prompt instructions plus parser/Pydantic validation.
* Add `LLM_JSON_MODE` with values `auto`, `on`, and `off`:
  * `auto` (default): use LiteLLM capability detection and enable JSON mode only
    when `response_format` is supported.
  * `on`: always pass `response_format={"type": "json_object"}`.
  * `off`: never pass `response_format`.
* Support DeepSeek-compatible JSON Output through `response_format` where
  practical, then validate the returned object with Pydantic.
* Preserve parser/fallback handling for empty, malformed, fenced, or reasoning
  wrapped model output because DeepSeek-compatible JSON Output is not guaranteed
  to produce schema-valid non-empty content.
* Preserve the current LLM failure fallback behavior: provider call failures,
  malformed model output, or parser failures return a successful OCS answer
  shape with `code: 1`, the original `question`, `answer: "未知"`, and
  `analysis: "服务器处理出错"` rather than returning `code: 0`.
* Add lightweight prompt-injection hardening in the model instructions: question
  title and options are data to analyze, not instructions to override output
  format or reveal prompts.
* Reevaluate all runtime and development package choices according to current
  Python/FastAPI best practices rather than preserving old dependencies for
  conservatism.
* Remove replaced or unnecessary packages during the refactor unless tests or
  runtime behavior prove they are still needed.
* Preserve the existing project name and Python target (`requires-python =
  ">=3.13"` plus `.python-version` set to `3.13`).
* Use `pydantic-settings` for typed settings, `.env` loading, and test-friendly
  settings overrides.
* Continue reading provider settings from the environment or `.env`.
* Add optional local server settings such as host and port if needed, preserving
  defaults of `0.0.0.0` and `5000`.
* Replace ad-hoc `print()` logging with Python standard-library `logging`.
* Preserve readable colored terminal output for the local operator, including
  request title/type/options and returned answer/analysis.
* Keep the OpenAI-compatible SDK call path synchronous. Use sync FastAPI path
  operations or sync service functions rather than `AsyncOpenAI`.
* Enforce a practical strict quality gate:
  * `uv run ruff format` or an equivalent format check must pass.
  * `uv run ruff check` must pass.
  * `uv run ty check` must pass.
  * `uv run pytest` must pass.
  * Type-check suppressions are allowed only when minimal and justified; do not
    exclude whole modules from checking.
* Tests must not make real OpenAI-compatible provider requests.
* LLM interactions in tests should use fakes/mocks and deterministic sample
  responses.
* Preserve the external answer contract and question-type intent during the
  refactor. Prompt and parser internals may be modernized only where required
  for structured output handling, prompt-injection hardening, or provider-mode
  compatibility.
* Add a modern quality toolchain around `uv`, `ruff`, `ty`, and tests.
* Update project documentation and example configuration to match the new
  runtime commands.
* Avoid adding persistence incidentally.

## Acceptance Criteria

* [ ] The chosen target architecture is documented before implementation.
* [ ] Compatibility tests cover the existing OCS request/response contract.
* [ ] Tests run without `OPENAI_API_KEY` and without network access.
* [ ] The project has configured lint, format, type-check, and test commands.
* [ ] Quality commands pass: Ruff format/check, ty check, and pytest.
* [ ] The README and OCS config match the implemented routes and startup flow.
* [ ] Existing OpenAI-compatible provider behavior remains configurable by
      environment variables.
* [ ] `LLM_*` settings work and existing `OPENAI_*` settings remain accepted as
      compatibility fallback.

## Definition of Done

* Tests added or updated for the OCS API contract and parser behavior.
* `ruff` formatting/linting passes.
* `ty` type checking passes or has documented, minimal exclusions.
* The relevant test suite passes.
* Documentation reflects the new architecture, commands, and environment setup.
* Rollout and rollback risk are considered before replacing Flask with FastAPI.

## Out of Scope

* Adding a database, cache, analytics, persistent logs, or user accounts unless
  explicitly pulled into scope later.
* Changing OCS client-side behavior beyond the compatibility config needed for
  the refactored service.
* Switching from OpenAI-compatible APIs to a provider-specific SDK.

## Technical Notes

* Inspected `main.py`, `pyproject.toml`, `README.md`, `ocs_config.json`,
  `.python-version`, `.gitignore`, `.env.tempate`, and backend Trellis specs.
* Relevant specs:
  * `.trellis/spec/backend/directory-structure.md`
  * `.trellis/spec/backend/quality-guidelines.md`
  * `.trellis/spec/backend/error-handling.md`
  * `.trellis/spec/backend/logging-guidelines.md`
  * `.trellis/spec/backend/database-guidelines.md`
* Current code is small enough that the biggest risk is not mechanical
  migration, but accidentally changing the OCS contract while restructuring.
* Toolchain research is recorded in
  `research/modern-python-toolchain.md`.

## Research References

* [`research/modern-python-toolchain.md`](research/modern-python-toolchain.md)
  — Ruff, ty, uv dependency groups, and FastAPI testing conventions from
  official documentation.
