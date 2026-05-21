# Error Handling

> How errors are handled in this project.

---

## Overview

The backend uses simple local `try`/`except` blocks and JSON responses rather
than custom exception classes. Errors are logged to the console with colorized
helpers in `main.py`, and API failures return OCS-friendly JSON instead of HTML
error pages.

The external response contract matters more than exception type purity: OCS
expects successful lookups to return `code: 1`, while failures return `code: 0`
plus a `msg` field.

---

## Error Types

No custom error classes are defined.

Current error categories:

- Missing configuration: if `OPENAI_API_KEY` is absent, startup prints a warning
  but the Flask app still starts.
- Bad request JSON: `/search` uses `request.get_json(force=True, silent=True)`
  and falls back to `json.loads(request.data)`.
- Missing question title: `/search` returns `{"code": 0, "msg": "..."}` with
  HTTP 400.
- LLM call or LLM JSON parse failure: `get_chatgpt_answer()` logs the error and
  returns an answer fallback rather than raising to the route.
- Unexpected route failure: `/search` logs the exception and returns HTTP 500
  with `{"code": 0, "msg": str(e)}`.

---

## Error Handling Patterns

- Keep request parsing failures inside the route and return a JSON error.
- Keep OpenAI-compatible API failures inside `get_chatgpt_answer()` so callers
  receive a fallback object with `answer` and `analysis`.
- Use `log_error()` for operational failures. The current logger prints
  `[ERROR]`, a timestamp, and the message.
- Preserve the route-level catch-all around `/search` until more specific error
  handling exists, because it prevents Flask from returning HTML to OCS.

Example from `main.py`: bad JSON falls back from Flask parsing to `json.loads`,
then returns a `code: 0` JSON response with HTTP 400 if both fail.

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

inside the internal fallback object returned by `get_chatgpt_answer()`.

Do not change the top-level `/search` success fields without updating
`ocs_config.json` and the README OCS handler example.

---

## Common Mistakes

- Do not let malformed model output propagate as a 500 when an answer fallback
  is acceptable.
- Do not return Flask HTML error pages from API routes.
- Do not expose secrets or full request headers in `msg` values or logs.
- Do not change `code` semantics casually; `ocs_config.json` checks `code === 1`
  before using a response.
