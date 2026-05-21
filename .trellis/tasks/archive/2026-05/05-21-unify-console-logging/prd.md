# Unify console logging

## Goal

Make the local OCS answer server terminal output consistent and readable during
normal use. The operator should see the app's request/answer diagnostics in one
Rich-styled format, without duplicate Uvicorn access lines or noisy LiteLLM
optional-provider startup warnings.

## What I Already Know

* The user sees mixed terminal output: app Rich logs, Uvicorn access logs, and
  LiteLLM optional dependency warnings.
* The app already has a console logging module in `app/logging.py` using
  standard-library `logging` plus `RichHandler`.
* The root `main.py` starts Uvicorn via `uvicorn.run(...)`.
* The useful local operator logs are the app logs: startup, request details,
  validation diagnostics, answer, and analysis.
* Uvicorn access logs duplicate the HTTP status after the app already logs the
  request/answer flow.

## Requirements

* Keep app logs (`log_info`, `log_request`, `log_response`,
  `log_validation_error`, `log_error`) in the existing Rich style.
* Suppress Uvicorn access logs in the recommended `uv run python main.py`
  startup path.
* Keep Uvicorn server lifecycle/error logs readable through the same logging
  style where practical.
* Suppress LiteLLM optional-provider startup warnings such as missing `botocore`;
  real LLM call failures should still be logged by `app.llm` through
  `log_error`.
* Avoid adding a new logging framework or persistent logging.

## Acceptance Criteria

* [x] `uvicorn.run` is configured so access logs are disabled for the root
      startup entrypoint.
* [x] Third-party loggers are configured without duplicating handlers across
      repeated `configure_logging()` calls.
* [x] Tests cover the Uvicorn startup logging configuration.
* [x] Existing API behavior remains unchanged.

## Definition of Done

* `uv run ruff format --check`, `uv run ruff check`, `uv run ty check`, and
  `uv run pytest` pass.
* Backend logging spec updated if the logging contract changes.

## Out of Scope

* File logging, JSON logging, log rotation, or cloud logging.
* Changing answer generation or OCS request parsing behavior.

## Technical Notes

* Main files: `main.py`, `app/logging.py`.
* Relevant tests can live under `tests/`.
* Relevant spec: `.trellis/spec/backend/logging-guidelines.md`.
