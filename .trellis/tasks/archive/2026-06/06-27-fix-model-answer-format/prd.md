# Fix Model Answer Format

## Goal

Prevent nested JSON from leaking into the OCS-facing `answer` field when a model returns a structured-looking JSON object inside `answer` instead of the actual answer text.

## What I Already Know

* User screenshot shows terminal logs like `答案: {"answer":"对","analysis":"..."}` for a 判断题, which is the wrong OCS answer format.
* The expected `answer` for 判断题 should be a plain answer such as `对` or `错`, not a serialized JSON object.
* `app.schemas.ModelAnswer.answer` is typed as `str`, so a JSON object encoded as a string is currently accepted.
* `app.llm.PydanticAIAnswerer` trusts a `ModelAnswer` instance directly and only validates non-`ModelAnswer` outputs.
* The current prompt asks for a JSON object, and some providers can nest that JSON object into the `answer` field.

## Requirements

* If `ModelAnswer.answer` contains a JSON object string with `answer` and `analysis`, unwrap it into a normal `ModelAnswer`.
* Preserve valid plain answers such as `A`, `A#C`, `对`, `错`, and free-text completion answers.
* Preserve the existing fallback behavior for malformed AI output.
* Keep the `/search` OCS response shape unchanged: `code`, `question`, `answer`, `analysis`.
* Add regression coverage for nested JSON in the `answer` field.

## Acceptance Criteria

* [x] A model output with `answer='{"answer":"对","analysis":"..."}'` returns API/log answer `对`.
* [x] The nested `analysis` value is used when present.
* [x] Plain non-JSON answers remain unchanged.
* [x] Existing API and LLM tests pass.
* [x] Project quality gate passes.

## Definition of Done

* Tests added/updated.
* Lint, type-check, and tests run successfully.
* Spec update considered if this introduces a persistent convention.

## Technical Approach

Add normalization at the `ModelAnswer` boundary so every path that validates or receives a model answer benefits from the same cleanup. The normalization should parse only object-shaped JSON strings in the `answer` field and validate them as `ModelAnswer`; arbitrary prose or malformed JSON should remain subject to existing validation/fallback behavior.

## Out of Scope

* Changing prompt wording beyond what is needed for this bug.
* Changing provider configuration, model selection, or OCS response schema.
* Adding broad model-output repair for Markdown/prose wrappers.

## Technical Notes

* Relevant files: `app/schemas.py`, `app/llm.py`, `tests/test_llm.py`, `tests/test_api.py`.
* Relevant screenshot symptom: terminal logs show the full JSON object under `答案`.
