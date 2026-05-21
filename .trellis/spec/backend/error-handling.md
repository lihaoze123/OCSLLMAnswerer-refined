# Error Handling

> How errors are handled in this project.

---

## Overview

The backend uses FastAPI exception handlers, local `try`/`except` blocks around
route and LLM boundaries, and JSON responses. Errors are logged through
standard-library `logging` helpers in `app/logging.py`, and API failures return
OCS-friendly JSON instead of FastAPI's default `detail` response when the route
is OCS-facing.

The external response contract matters more than exception type purity: OCS
expects successful lookups to return `code: 1`, while failures return `code: 0`
plus a `msg` field.

---

## Error Types

No custom error classes are defined.

Current error categories:

- Missing configuration: `LLM_MODEL`/`OPENAI_MODEL` has no hard-coded default.
  LLM calls fail into the answer fallback if the model is not configured.
- Bad request JSON or schema validation: FastAPI/Pydantic raises
  `RequestValidationError`, which `app/main.py` converts to OCS error JSON.
  `/search` manually parses raw request bytes as JSON first so OCS
  `text/plain;charset=UTF-8` JSON payloads do not fail before schema validation.
- Missing question title: `/search` returns `{"code": 0, "msg": "..."}` with
  HTTP 400.
- Unsupported question type label: `/search` normalizes it to
  `QuestionType.unknown` and continues with the normal HTTP 200 success shape,
  because rejecting OCS plugin lookups as 400 appears to users as a question
  bank connection failure.
- LLM call or LLM JSON parse failure: `LiteLLMAnswerer.answer()` logs the error
  and returns an answer fallback rather than raising to the route.
- Unexpected route failure: `/search` logs the exception and returns HTTP 500
  with `{"code": 0, "msg": str(e)}`.

---

## Error Handling Patterns

- Convert `RequestValidationError` to `{"code": 0, "msg": "..."}` for OCS
  compatibility.
- Keep `/search` tolerant of OCS content-type behavior by parsing the raw body as
  JSON before `SearchRequest` validation. Do not reintroduce an annotated
  `SearchRequest` body parameter unless text/plain JSON compatibility is covered
  another way.
- Log OCS-facing `RequestValidationError` failures with request diagnostics
  before returning the error shape. Include safe metadata and a bounded body
  preview, but not full request headers.
- Keep LiteLLM/API failures inside `LiteLLMAnswerer.answer()` so callers receive
  a fallback `ModelAnswer`.
- Use `log_error()` for operational failures.
- Preserve the route-level catch-all around `/search` because it prevents
  framework error shapes from reaching OCS.

---

## API Error Responses

Current response shapes:

```json
{"code": 0, "msg": "error message"}
```

for request/server errors, and:

```json
{"answer": "<localized unknown answer>", "analysis": "<localized processing error>"}
```

inside the internal fallback object returned by `LiteLLMAnswerer.answer()`.

Do not change the top-level `/search` success fields without updating
`ocs_config.json`, the README OCS handler example, and `tests/test_api.py`.

---

## Common Mistakes

- Do not let malformed model output propagate as a 500 when an answer fallback
  is acceptable.
- Do not return FastAPI `{"detail": ...}` or HTML error pages from OCS-facing
  API routes.
- Do not reject unfamiliar OCS `type` labels at the schema boundary. Normalize
  known aliases and fall unknown labels back to `QuestionType.unknown`.
- Do not expose secrets or full request headers in `msg` values or logs.
- Do not change `code` semantics casually; `ocs_config.json` checks `code === 1`
  before using a response.
