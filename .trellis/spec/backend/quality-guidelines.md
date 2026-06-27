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
- Do not bypass the Pydantic AI gateway with raw provider SDK calls unless the
  structured-output and fallback contracts are redesigned in the same task.

---

## Required Patterns

- Keep provider configuration environment-driven through `AI_*` keys. The
  current supported shape is a single OpenAI-compatible provider with separate
  text and vision model fields.
- Keep question-type behavior centralized around `QuestionType`,
  `QUESTION_TYPE_ALIASES`, `TYPE_LABELS`, and `build_special_instruction()`.
  OCS-facing request parsing should accept common English aliases, Chinese type
  labels, and unknown labels without rejecting the lookup.
- Use Pydantic AI prompted structured output
  (`output_type=PromptedOutput(ModelAnswer)`) for model answers instead of
  hand-written JSON cleanup/parsing. Do not pass bare `ModelAnswer` as the
  output type in this app: Pydantic AI maps a bare Pydantic model to tool-based
  output, which can force `tool_choice` and break DeepSeek thinking-capable
  models such as `deepseek-v4-pro`.
- Normalize nested structured answers at the Pydantic AI gateway boundary. Some
  OpenAI-compatible providers may return a valid `ModelAnswer` whose `answer`
  field is itself a JSON object string like
  `{"answer":"对","analysis":"..."}`. Before `/search` logs or returns the
  answer, unwrap that nested object so OCS receives only the final answer text.
- Keep the live `/search` AI path async end-to-end. `app.main` awaits
  `Answerer.answer()`, and `app.llm.PydanticAIAnswerer` must call
  `await agent.run(...)`. Do not call Pydantic AI `run_sync(...)` from the
  FastAPI request path because the server already has an event loop running.
- Normalize options before prompting by trimming lines and dropping blank lines.
- Keep prompt construction compatible with both text-only and image questions.
  Text-only requests pass a plain prompt string to Pydantic AI. Image requests
  use `app.question_images` to preserve ordered text/image parts, download each
  image through `app.images`, and send local bytes as Pydantic AI
  `BinaryContent`.
- Keep `CHAOXING_COOKIE` optional and secret-backed. Use it only for local
  Chaoxing image fetches, never log it, and do not require it for text-only or
  public-image questions.
- Local Chaoxing image fetches intentionally use `verify=False` in `app.images`
  to avoid local campus-network/proxy certificate-chain failures. Keep this
  scoped to local Chaoxing image downloads; do not disable SSL verification for
  Pydantic AI/OpenAI API calls.
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
- For Pydantic AI gateway changes, add tests for model success, missing-model
  fallback, structured-output fallback, model routing, and multimodal input
  construction.
- For prompt changes involving images, add tests that image URLs are extracted
  from both `title` and `options`, adjacent Chinese text is not captured as part
  of the URL, duplicate image URLs are not repeated, and no-image requests still
  build plain text user content.
- For response-shape changes, update and review `ocs_config.json` and the README
  OCS handler together.

---

## Code Review Checklist

- Does `/search` still accept `title`, `options`, and `type` from the OCS
  payload?
- Does it still return `code`, `question`, `answer`, and `analysis` on success?
- Are API keys and provider settings still environment-based?
- Does Pydantic AI structured output still validate as `ModelAnswer`, and do
  model/output failures still return the fallback answer?
- Does the Pydantic AI answer agent still use `PromptedOutput(ModelAnswer)` so
  DeepSeek thinking models are not sent forced output-tool choices?
- Are errors logged locally but returned to OCS as JSON?
- Are README and `ocs_config.json` still aligned with route behavior?
- Did Ruff format/check, ty, and pytest pass?

## Scenario: FastAPI OCS Contract and Pydantic AI Gateway

### 1. Scope / Trigger

- Trigger: Changes to API routes, request/response schemas, environment
  variables, Pydantic AI gateway calls, image input handling, or structured
  model output.

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
- Multimodal prompt behavior: image URLs embedded in `title` or `options` are
  parsed by `app.question_images`, downloaded locally by `app.images`, and
  inserted as Pydantic AI `BinaryContent` while preserving surrounding text
  order. No-image questions keep string user content.
- Image behavior: any image URL in the question makes the request require
  `AI_VISION_MODEL`. Images are fetched locally with browser-like fallback
  request strategies, max-size enforcement, and media-type detection. If a
  required image cannot be fetched/prepared, the answerer returns the fallback
  answer instead of asking the model to guess without the image.
- Internal `type` values: `single`, `multiple`, `judgement`, `completion`,
  `unknown`.
- External OCS `type` input may be a known internal value, a common alias, a
  Chinese label such as `单选题`, or an unsupported label. Normalize known labels
  to the internal enum and fall unsupported labels back to `unknown`.
- Success fields: `code: 1`, `question`, `answer`, `analysis`.
- Error fields: `code: 0`, `msg`.
- Primary env keys: `AI_PROVIDER`, `AI_API_KEY`, `AI_BASE_URL`,
  `AI_TEXT_MODEL`, `AI_VISION_MODEL`, `AI_TIMEOUT`, `AI_TEMPERATURE`,
  `CHAOXING_COOKIE`, `SERVER_HOST`, `SERVER_PORT`.
- Legacy `LLM_*` / `OPENAI_*` provider keys are intentionally not fallback
  aliases.

### 4. Validation & Error Matrix

- Empty or whitespace `title` -> HTTP 400 with `{"code": 0, "msg": ...}`.
- Unsupported `type` -> HTTP 200 success shape, handled internally as
  `QuestionType.unknown`.
- `text/plain;charset=UTF-8` body containing valid JSON -> same behavior as
  `application/json`.
- Non-JSON body text -> HTTP 400 with `{"code": 0, "msg": ...}`.
- Invalid JSON/body shape -> HTTP 400 with `{"code": 0, "msg": ...}`.
- AI provider failure -> HTTP 200 success shape with fallback answer.
- Pydantic AI structured output failure/retry exhaustion -> HTTP 200 success
  shape with fallback answer.
- Image question with missing `AI_VISION_MODEL` -> HTTP 200 success shape with
  fallback answer.
- Image HTTP/network/content-type failure -> log a concise local error and
  return the fallback answer.
- Chaoxing image certificate verification failure -> should not occur because
  local Chaoxing image fetches use `verify=False`.

### 5. Good/Base/Bad Cases

- Good: valid OCS payload returns `code: 1`, original question, parsed answer,
  and parsed analysis.
- Base: options are omitted or blank; service prompts with an empty options
  string and still returns a valid OCS shape.
- Image: title/options contain `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, or
  `.bmp` URLs; prompt construction preserves the text and adds local
  `BinaryContent` for vision-capable models.
- Protected image: Chaoxing image URL plus `CHAOXING_COOKIE` is fetched locally
  before Pydantic AI is called, avoiding provider-side 403 fetches.
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
- Pydantic AI gateway tests with mocked agent factory for success and fallback.
- Model routing tests for text vs. vision model selection.
- Prompt tests asserting no-image content remains a string and image-question
  prompts include the image count instruction.
- Image parser tests for adjacent Chinese text, duplicate URLs, spans, and
  ordered text/image parts.
- Image downloader tests for known-domain referers, Chaoxing cookie headers,
  SSL verification scoping, media-type magic-byte detection, and size limits.

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

#### Wrong

```python
return Agent(model, output_type=ModelAnswer)
```

This makes Pydantic AI use tool-based structured output for the answer schema.
For DeepSeek thinking-capable models, that may send an unsupported forced
`tool_choice` and cause the AI gateway to return the fallback answer.

#### Correct

```python
return Agent(
    model,
    output_type=PromptedOutput(ModelAnswer),
    instructions=SYSTEM_INSTRUCTIONS,
    retries=2,
)
```

This keeps Pydantic AI validation while avoiding output-tool `tool_choice`
requests that DeepSeek thinking mode rejects.

#### Wrong

```python
ImageUrl(url=chaoxing_url)
```

This lets the model provider download a protected URL without the local browser
session and can fail with HTTP 403.

#### Correct

```python
BinaryContent(data=image.data, media_type=image.media_type)
```

Download image URLs locally, preserve text/image ordering, and send local bytes
to Pydantic AI. If a required image cannot be fetched, return the fallback
answer instead of silently skipping it.

#### Wrong

```python
result = agent.run_sync(user_prompt)
```

Calling Pydantic AI's synchronous runner from `/search` can fail with
`This event loop is already running` because FastAPI is already executing inside
an event loop.

#### Correct

```python
result = await agent.run(user_prompt)
```

Keep the route, answerer, and Pydantic AI call async so provider or
structured-output failures flow into the existing fallback answer instead of an
event-loop runtime error.

#### Wrong

```json
{"code": 1, "answer": "{\"answer\":\"对\",\"analysis\":\"...\"}", "analysis": "..."}
```

This leaks the model's nested JSON into OCS as the selected answer.

#### Correct

```json
{"code": 1, "answer": "对", "analysis": "..."}
```

If `ModelAnswer.answer` contains a JSON object with `answer` and `analysis`,
normalize it in `app.llm` before logging or returning the response.
