# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

This is a small Python FastAPI service targeting Python >=3.13. The main quality
bar is preserving the OCS integration contract while keeping prompt/response
handling readable, typed, and failure-tolerant.

The configured quality gate is:

- `uv run ruff format --check`
- `uv run ruff check`
- `uv run ty check`
- `uv run pytest`

---

## Forbidden Patterns

- Do not hard-code API keys, base URLs, model names, or provider credentials.
  Read them from `app.config.Settings`.
- Do not change `/search` success response fields (`code`, `question`,
  `answer`, `analysis`) without updating `ocs_config.json` and README examples.
- Do not return Markdown, prose wrappers, or raw model output to OCS; keep the
  parsed answer/analysis JSON contract.
- Do not add database, cache, or persistent logging behavior without documenting
  privacy and deployment consequences.
- Do not replace the LiteLLM gateway path with a provider-specific SDK unless
  multi-provider compatibility is no longer a requirement.

---

## Required Patterns

- Keep provider configuration environment-driven through primary `LLM_*` keys
  with legacy `OPENAI_*` fallbacks.
- Keep question-type behavior centralized around `QuestionType`,
  `QUESTION_TYPE_ALIASES`, `TYPE_LABELS`, and `build_special_instruction()`.
  OCS-facing request parsing should accept common English aliases, Chinese type
  labels, and unknown labels without rejecting the lookup.
- Strip reasoning wrappers and Markdown fences before parsing model JSON. The
  current code removes `<think>...</think>`, trims fenced `json` blocks,
  extracts the first JSON object, and validates it as `ModelAnswer`.
- Normalize options before prompting by trimming lines and dropping blank lines.
- Parse `/search` request bodies manually as JSON from raw bytes so OCS payloads
  still work when the browser script sends JSON with
  `Content-Type: text/plain;charset=UTF-8`.
- Return JSON from every FastAPI route, including errors.
- Keep OCS truthy success as `code: 1`; failures use `code: 0`.
- LLM provider failures and malformed model output are special: preserve the
  existing answer fallback as a successful OCS shape with `answer: "未知"` and
  `analysis: "服务器处理出错"`.

---

## Testing Requirements

Minimum verification for code changes:

- Run the full quality gate listed above.
- For dependency/config changes, inspect `pyproject.toml`, `uv.lock`, and the
  README install/run instructions together.
- For `/search` behavior changes, add or update FastAPI `TestClient` tests for
  the OCS request/response contract.
- For parser changes, add tests for `<think>` cleanup, Markdown fence cleanup,
  surrounded JSON extraction, and malformed output fallback behavior.
- For response-shape changes, update and review `ocs_config.json` and the README
  OCS handler together.

---

## Code Review Checklist

- Does `/search` still accept `title`, `options`, and `type` from the OCS
  payload?
- Does it still return `code`, `question`, `answer`, and `analysis` on success?
- Are API keys and provider settings still environment-based?
- Are model-output cleanup rules still robust to reasoning tags, Markdown
  fences, and extra surrounding text?
- Are errors logged locally but returned to OCS as JSON?
- Are README and `ocs_config.json` still aligned with route behavior?
- Did Ruff format/check, ty, and pytest pass?

## Scenario: FastAPI OCS Contract and LiteLLM Gateway

### 1. Scope / Trigger

- Trigger: Changes to API routes, request/response schemas, environment
  variables, LLM gateway calls, or model-output parsing.

### 2. Signatures

- `GET /` and `HEAD /` return health status.
- `POST /search` accepts the OCS payload.
- `/search` accepts JSON bodies sent as either normal JSON requests or as
  `text/plain;charset=UTF-8` containing JSON text.
- Runtime command: `uv run python main.py`.
- Direct ASGI command: `uv run uvicorn app.main:app --host 0.0.0.0 --port 5000`.

### 3. Contracts

- Request fields: `title: str`, `options: str = ""`,
  `type: QuestionType = "unknown"`.
- Internal `type` values: `single`, `multiple`, `judgement`, `completion`,
  `unknown`.
- External OCS `type` input may be a known internal value, a common alias, a
  Chinese label such as `单选题`, or an unsupported label. Normalize known labels
  to the internal enum and fall unsupported labels back to `unknown`.
- Success fields: `code: 1`, `question`, `answer`, `analysis`.
- Error fields: `code: 0`, `msg`.
- Primary env keys: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`,
  `LLM_TIMEOUT`, `LLM_JSON_MODE`, `SERVER_HOST`, `SERVER_PORT`.
- Legacy fallback env keys: `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
  `OPENAI_MODEL`, `OPENAI_TIMEOUT`.

### 4. Validation & Error Matrix

- Empty or whitespace `title` -> HTTP 400 with `{"code": 0, "msg": ...}`.
- Unsupported `type` -> HTTP 200 success shape, handled internally as
  `QuestionType.unknown`.
- `text/plain;charset=UTF-8` body containing valid JSON -> same behavior as
  `application/json`.
- Non-JSON body text -> HTTP 400 with `{"code": 0, "msg": ...}`.
- Invalid JSON/body shape -> HTTP 400 with `{"code": 0, "msg": ...}`.
- LLM provider failure -> HTTP 200 success shape with fallback answer.
- Malformed model JSON -> HTTP 200 success shape with fallback answer.

### 5. Good/Base/Bad Cases

- Good: valid OCS payload returns `code: 1`, original question, parsed answer,
  and parsed analysis.
- Base: options are omitted or blank; service prompts with an empty options
  string and still returns a valid OCS shape.
- Compatibility: OCS sends JSON text as `text/plain;charset=UTF-8`; the service
  parses the raw body and validates it as `SearchRequest`.
- Bad-but-tolerated: `type: "essay"` is accepted and handled as unknown so OCS
  does not report a question bank connection failure for an unfamiliar label.

### 6. Tests Required

- `TestClient` health route test for `code` and `msg`.
- `TestClient` `/search` success contract test with option normalization.
- Validation tests for blank `title`, Chinese type aliases, and unsupported
  type fallback.
- Compatibility tests for `text/plain;charset=UTF-8` JSON payloads and malformed
  non-JSON text.
- Parser tests for reasoning tags, Markdown fences, surrounded JSON, and
  fallback behavior.
- LiteLLM gateway tests with mocked `completion()` and mocked JSON mode
  capability detection.

### 7. Wrong vs Correct

#### Wrong

```python
return {"detail": exc.errors()}
```

This leaks FastAPI's default error shape to OCS.

#### Correct

```python
return {"code": 0, "msg": "..."}
```

This preserves the OCS-facing contract even though Pydantic performs the
internal validation.
