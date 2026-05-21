# Logging Guidelines

> How logging is done in this project.

---

## Overview

Logging is console-based and implemented with Python standard-library
`logging` plus Rich's `RichHandler`. `app/logging.py` defines small helpers for
consistent local operator messages.

The logs are intended for a local OCS answer server operator watching requests,
answers, and parsing failures in the terminal.

---

## Log Levels

Current helpers:

- `log_info(msg)`: startup and general operational messages.
- `log_error(msg)`: LiteLLM/provider failures, JSON parse failures, and
  unexpected route exceptions.
- `log_request(title, options, q_type)`: structured-ish request display for each
  OCS lookup.
- `log_response(answer, analysis)`: answer and analysis display after model
  processing.

There is no debug-level logging, file logging, JSON logging, or log rotation.

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

---

## What to Log

- Server startup, including the host/port.
- Each incoming OCS question title, question type, and normalized options.
- The selected answer and short analysis returned to OCS.
- LiteLLM/provider API errors and model-response parse failures.
- Unexpected route exceptions before returning a JSON error response.

---

## What NOT to Log

- Never log `LLM_API_KEY`, `OPENAI_API_KEY`, full environment variables, request
  headers, or provider credentials.
- Avoid logging full raw model responses if they may contain sensitive prompt
  content; log concise parsing failures instead.
- Be careful with question content. The current app logs titles/options for local
  debugging, but any cloud/server deployment should revisit this before storing
  or forwarding logs.
- Do not add noisy per-token or per-line logs around prompt construction unless
  debugging a specific issue.
