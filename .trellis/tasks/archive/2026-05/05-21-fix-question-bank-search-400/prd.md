# Fix question bank search 400

## Goal

Fix the local OCS answer server so real OCS `/search` requests do not fail with
HTTP 400 when the script sends a question type label outside the current strict
English enum values. The service should preserve the OCS-compatible response
contract while remaining tolerant of the payload shape used by the browser
plugin. If 400s still occur, the terminal logs should include enough safe
request diagnostics to identify the actual payload/content-type/schema problem.

## What I Already Know

* The user sees `题库连接失败` in the OCS browser plugin UI.
* The local server logs show repeated `POST /search HTTP/1.1" 400 Bad Request`.
* `app/main.py` converts request parsing and Pydantic validation errors into
  HTTP 400 with `{"code": 0, "msg": "..."}`.
* `app/schemas.py` currently accepts only `single`, `multiple`, `judgement`,
  `completion`, and `unknown` for `type`.
* The pre-modernization Flask implementation accepted unknown `type` values and
  passed them through to the prompt instead of rejecting the request.
* README and `ocs_config.json` configure OCS to submit `type: "${type}"`, whose
  runtime value may be a Chinese label such as `单选题`.
* The first compatibility fix did not resolve the user's browser-side
  `题库连接失败`, so the next step is richer diagnostic logging for failed OCS
  requests.
* The diagnostic logs show OCS sends a JSON string with
  `Content-Type: text/plain;charset=UTF-8`; FastAPI's annotated body parsing
  rejects that before route logic sees the payload.

## Assumptions

* The main compatibility gap is strict question-type validation, not a network
  or CORS failure, because the server receives the request and returns 400.
* Unknown question types should degrade to `unknown` or a known mapped enum
  rather than rejecting the whole search request.

## Requirements

* `/search` continues accepting `title`, `options`, and `type`.
* Known English OCS type values keep their current behavior.
* Chinese type labels for common OCS question types map to the existing
  `QuestionType` values.
* Unsupported non-empty type values no longer cause HTTP 400; they should be
  treated as `unknown` so the model can still attempt an answer.
* Empty or whitespace-only `title` should still return HTTP 400.
* The success response shape remains `code`, `question`, `answer`, `analysis`.
* `/search` should accept JSON payloads even when OCS sends them as
  `text/plain;charset=UTF-8`.
* Request validation failures should log method/path, client address,
  content-type, content-length, body size, a short body preview, and validation
  error details without logging full headers or secrets.

## Acceptance Criteria

* [ ] A `/search` request with `type: "单选题"` returns HTTP 200 and is handled
      as a single-choice question.
* [ ] A `/search` request with an unsupported type label returns HTTP 200 and
      is handled as unknown.
* [ ] Existing validation for empty titles still returns HTTP 400.
* [ ] A `/search` request with `Content-Type: text/plain;charset=UTF-8` and a
      JSON body returns HTTP 200.
* [ ] A malformed `/search` payload logs diagnostics that can explain why the
      request was rejected.
* [ ] Existing tests pass, and `/search` compatibility tests are added or
      updated.

## Definition of Done

* Tests added or updated for the compatibility behavior.
* `ruff format --check`, `ruff check`, `ty check`, and `pytest` pass, or any
  inability to run them is recorded.
* README/OCS config are unchanged unless the external contract changes.

## Out of Scope

* Adding a persistent question bank cache.
* Changing the OCS script handler contract.
* Debugging unrelated LiteLLM provider credentials or model quality issues.

## Technical Notes

* Main route: `app/main.py`.
* Request schema and question type normalization: `app/schemas.py`.
* Prompt instructions consume `SearchRequest.type` and `SearchRequest.type_label`.
* API tests live in `tests/test_api.py`.
* Relevant specs: `.trellis/spec/backend/index.md`,
  `.trellis/spec/backend/quality-guidelines.md`,
  `.trellis/spec/backend/error-handling.md`,
  `.trellis/spec/backend/directory-structure.md`.
