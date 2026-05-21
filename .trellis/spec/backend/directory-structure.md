# Directory Structure

> How backend code is organized in this project.

---

## Overview

This project is currently a compact Flask backend, not a package-structured
application. The runtime code lives in `main.py`, with OCS integration config in
`ocs_config.json` and project metadata/dependencies in `pyproject.toml`.

There are no `src/`, `app/`, `routes/`, `services/`, or package directories yet.
Until the codebase grows, keep small endpoint, prompt, parsing, and logging
changes close to the existing module-level functions in `main.py`.

---

## Directory Layout

```
.
|-- main.py             # Flask app, routes, OpenAI client, prompt/parsing logic
|-- ocs_config.json     # OCS script-side search endpoint configuration
|-- pyproject.toml      # Python >=3.13 metadata and runtime dependencies
|-- README.md           # User-facing setup and OCS configuration instructions
|-- AGENTS.md           # Trellis/Codex project instructions
`-- .trellis/spec/      # AI coding guidelines populated by this task
```

---

## Module Organization

Current organization in `main.py`:

- Imports and environment setup are at the top.
- `app = Flask(__name__)` and the OpenAI-compatible client are module-level
  singletons.
- Console logging helpers are module-level functions:
  `log_info`, `log_success`, `log_error`, `log_request`, and `log_response`.
- `TYPE_MAPPING` is the central question-type mapping.
- `get_chatgpt_answer()` owns prompt construction, LLM invocation, response
  cleanup, JSON parsing, and LLM-level fallback behavior.
- Flask routes are declared after helpers: `/` for health and `/search` for OCS
  answer lookup.

When adding small behavior, extend the existing function that owns that behavior.
For example, add a new OCS question type by updating `TYPE_MAPPING` and the
branching inside `get_chatgpt_answer()`, then verify `/search` still returns the
same top-level JSON fields.

If a future change makes `main.py` hard to navigate, split by responsibility:
routes, LLM answer generation, response parsing, logging, and configuration.
Do that as a focused refactor with compatibility tests rather than mixing it
into an unrelated behavior change.

---

## Naming Conventions

- Python functions use `snake_case`.
- Constants use `UPPER_SNAKE_CASE`, as shown by `TYPE_MAPPING`.
- Request fields mirror OCS payload names: `title`, `options`, and `type`.
- JSON response fields are part of the external contract: `code`, `question`,
  `answer`, `analysis`, and `msg`.
- Environment variables are uppercase and read through `os.getenv`, currently
  `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`.
- Keep new file names lowercase with underscores if the project is split into
  modules later.

---

## Examples

- `main.py`: canonical example for route structure, OpenAI-compatible client
  setup, prompt generation, LLM response cleanup, and OCS JSON response shape.
- `ocs_config.json`: canonical example for the OCS consumer contract. Its
  handler expects a successful lookup to use `code === 1` and returns the
  `question` and `answer` fields.
- `README.md`: user-facing setup should stay aligned with the default Flask
  host/port and `/search` endpoint in `main.py`.
