# Directory Structure

> How backend code is organized in this project.

---

## Overview

This project is a compact FastAPI backend with a deliberately small package
layout. The root `main.py` is only a compatible startup entrypoint; runtime API
behavior lives under `app/`.

Do not expand this into a platform-style `api/services/providers/domain`
hierarchy unless the product scope grows beyond the local OCS answer server.
Keep splits aligned to concrete responsibilities: API routes, settings, schemas,
prompt construction, LLM gateway calls, parsing, and logging.

---

## Directory Layout

```
.
|-- main.py             # Compatible uvicorn startup entrypoint
|-- app/
|   |-- main.py         # FastAPI app factory, routes, validation handler
|   |-- config.py       # pydantic-settings environment configuration
|   |-- schemas.py      # Pydantic request/response/answer models
|   |-- prompts.py      # OCS question prompt construction
|   |-- question_images.py # Image URL parsing and ordered text/image splitting
|   |-- images.py       # Local image download and media-type detection
|   |-- llm.py          # Pydantic AI gateway + structured output/fallback
|   `-- logging.py      # Standard logging setup with colored local output
|-- ocs_config.json     # OCS script-side search endpoint configuration
|-- pyproject.toml      # Python >=3.13 metadata and runtime dependencies
|-- README.md           # User-facing setup and OCS configuration instructions
|-- AGENTS.md           # Trellis/Codex project instructions
`-- .trellis/spec/      # AI coding guidelines populated by this task
```

---

## Module Organization

Current organization:

- Root `main.py` loads settings and launches uvicorn for `app.main:app`.
- `app.main.create_app()` owns FastAPI app construction, route registration,
  `/search` raw-body JSON parsing for OCS content-type compatibility, request
  validation error conversion, and test dependency injection.
- `app.config.Settings` owns all environment-driven runtime configuration.
- `app.schemas` owns OCS boundary models, `QuestionType`, and OCS-facing
  question-type alias normalization.
- `app.prompts` owns prompt construction and question-type instructions.
- `app.question_images` owns image URL matching, URL deduplication, and ordered
  text/image part splitting.
- `app.images` owns local image downloads, provider-aware request headers,
  max-size enforcement, and media-type detection.
- `app.llm.PydanticAIAnswerer` owns Pydantic AI calls, text/vision model
  routing, `BinaryContent` construction, structured answer validation, and
  AI-level fallback behavior.
- `app.logging` owns local colored console output through standard `logging`.

When adding behavior, modify the module that owns that behavior. For example,
add a new supported OCS question type in `app.schemas.QuestionType`, labels in
`TYPE_LABELS`, prompt text in `app.prompts`, and tests for `/search`.

---

## Naming Conventions

- Python functions use `snake_case`.
- Constants use `UPPER_SNAKE_CASE`, as shown by `TYPE_LABELS`.
- Request fields mirror OCS payload names: `title`, `options`, and `type`.
- JSON response fields are part of the external contract: `code`, `question`,
  `answer`, `analysis`, and `msg`.
- Environment variables are uppercase and loaded through `pydantic-settings`.
  AI provider settings use `AI_*`; legacy `LLM_*` / `OPENAI_*` variables are no
  longer compatibility fallbacks.
- Keep new file names lowercase with underscores if the project is split into
  modules later.

---

## Examples

- `app/main.py`: canonical example for FastAPI route structure and OCS JSON
  response shape.
- `app/llm.py`: canonical example for Pydantic AI setup, text/vision routing,
  structured output handling, multimodal `BinaryContent`, and fallback behavior.
- `ocs_config.json`: canonical example for the OCS consumer contract. Its
  handler expects a successful lookup to use `code === 1` and returns the
  `question` and `answer` fields.
- `README.md`: user-facing setup should stay aligned with the default
  FastAPI/uvicorn host/port and `/search` endpoint in `app/main.py`.
