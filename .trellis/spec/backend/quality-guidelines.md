# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

This is a small Python Flask service targeting Python >=3.13. The main quality
bar is preserving the OCS integration contract while keeping prompt/response
handling readable and failure-tolerant.

There is no configured test runner, formatter, linter, or type checker in
`pyproject.toml` yet. For now, validation is manual: syntax-check Python files,
exercise the Flask routes when behavior changes, and inspect JSON response
shapes against `ocs_config.json` and the README example.

---

## Forbidden Patterns

- Do not hard-code API keys, base URLs, model names, or provider credentials.
  Read them from environment variables with `os.getenv`.
- Do not change `/search` success response fields (`code`, `question`,
  `answer`, `analysis`) without updating `ocs_config.json` and README examples.
- Do not return Markdown, prose wrappers, or raw model output to OCS; keep the
  parsed answer/analysis JSON contract.
- Do not add database, cache, or persistent logging behavior without documenting
  privacy and deployment consequences.
- Do not replace the existing OpenAI-compatible client with a provider-specific
  SDK unless multi-provider compatibility is no longer a requirement.

---

## Required Patterns

- Keep OpenAI-compatible configuration environment-driven:
  `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, and optional `OPENAI_MODEL`.
- Keep question-type behavior centralized around `TYPE_MAPPING` and
  `get_chatgpt_answer()`.
- Strip reasoning wrappers and Markdown fences before parsing model JSON. The
  current code removes `<think>...</think>`, trims fenced `json` blocks,
  extracts the first JSON object, and then calls `json.loads`.
- Normalize options before prompting by trimming lines and dropping blank lines.
- Return JSON from every Flask route, including errors.
- Keep OCS truthy success as `code: 1`; failures use `code: 0`.

---

## Testing Requirements

No automated tests are currently present.

Minimum verification for code changes:

- Run `python3 -m py_compile main.py` after editing Python.
- For dependency/config changes, inspect `pyproject.toml` and confirm the README
  install/run instructions are still accurate.
- For `/search` behavior changes, manually test representative payloads for
  single choice, multiple choice, judgement, and completion questions.
- For response-shape changes, update and review `ocs_config.json` and the README
  OCS handler together.

If the project grows, add focused route tests using Flask's test client before
large refactors.

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
- Was `python3 -m py_compile main.py` run for Python edits?
