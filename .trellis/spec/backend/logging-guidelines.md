# Logging Guidelines

> How logging is done in this project.

---

## Overview

Logging is console-based and implemented with Python standard-library
`logging` plus Rich's `RichHandler`. `app/logging.py` defines small helpers for
consistent local operator messages.

The logs are intended for a local OCS answer server operator watching requests,
answers, and parsing failures in the terminal. The recommended startup path
(`uv run python main.py`) keeps console output in one Rich-styled format and
disables Uvicorn access logs to avoid duplicate request lines.

---

## Log Levels

Current helpers:

- `log_info(msg)`: startup and general operational messages.
- `log_error(msg)`: LiteLLM/provider failures, JSON parse failures, and
  unexpected route exceptions.
- `log_validation_error(...)`: OCS-facing request validation failures, including
  method/path, client address, content-type, content-length, body size, a short
  body preview, and sanitized validation error details.
- `log_request(title, options, q_type)`: structured-ish request display for each
  OCS lookup.
- `log_response(answer, analysis)`: answer and analysis display after model
  processing.

There is no debug-level logging, file logging, JSON logging, or log rotation.

`configure_logging()` also owns the known third-party console loggers used by
the local runtime:

- `uvicorn` and `uvicorn.error` use the same Rich handler for lifecycle/error
  logs.
- `uvicorn.access` is disabled; app request logs are the source of truth for OCS
  request/answer flow.
- `LiteLLM` and `litellm` are set to `ERROR` to suppress optional-provider
  startup warnings such as missing `botocore`. Actual model call failures are
  still logged by `app.llm` through `log_error()`.

---

## Structured Logging

The format is human-readable terminal output, not machine-parseable structured
logging. RichHandler owns terminal formatting, timestamps, and level styling.
Keep this local-operator UX unless the product scope changes toward hosted
operations.

Example pattern from `log_info()`:

```python
logger.info(message)
```

Keep new console logs behind the helper functions unless a route-specific
multi-line display like `log_request()` is needed.

When changing the root `main.py` Uvicorn startup path, keep
`access_log=False` and `log_config=None` so Uvicorn does not reinstall its own
default logging format over the app's logging setup.

---

## What to Log

- Server startup, including the host/port.
- Each incoming OCS question title, question type, and normalized options.
- OCS `/search` validation failures with safe request diagnostics, so browser
  plugin "question bank connection failed" reports can be traced to the actual
  payload/content-type/schema issue.
- The selected answer and short analysis returned to OCS.
- LiteLLM/provider API errors and model-response parse failures.
- Chaoxing image download failures, with concise status/reason only and without
  logging `CHAOXING_COOKIE`.
- Unexpected route exceptions before returning a JSON error response.
- Uvicorn server lifecycle/error messages, when emitted, through the same Rich
  handler.

---

## What NOT to Log

- Never log `LLM_API_KEY`, `OPENAI_API_KEY`, full environment variables, request
  headers, `CHAOXING_COOKIE`, or provider credentials.
- Do not log full request headers when diagnosing validation failures. Log only
  the specific safe fields needed for local debugging, such as content type and
  content length.
- Keep raw request body logging bounded to a short preview. The current
  validation logger limits the decoded body preview to 500 characters and logs
  the total byte count separately.
- Avoid logging full raw model responses if they may contain sensitive prompt
  content; log concise parsing failures instead.
- Be careful with question content. The current app logs titles/options for local
  debugging, but any cloud/server deployment should revisit this before storing
  or forwarding logs.
- Do not add noisy per-token or per-line logs around prompt construction unless
  debugging a specific issue.
- Do not re-enable Uvicorn access logs in the recommended startup path unless
  the app request logs are also redesigned; otherwise operators see duplicate
  request lines in mismatched formats.
