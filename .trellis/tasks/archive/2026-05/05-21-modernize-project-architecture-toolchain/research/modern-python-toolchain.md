# Modern Python Toolchain Research

## Sources

* Ruff configuration: https://docs.astral.sh/ruff/configuration/
* ty type checking: https://docs.astral.sh/ty/type-checking/
* ty configuration: https://docs.astral.sh/ty/configuration/
* uv dependency management: https://docs.astral.sh/uv/concepts/projects/dependencies/
* FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
* FastAPI settings: https://fastapi.tiangolo.com/advanced/settings/
* Pydantic Settings: https://docs.pydantic.dev/latest/api/pydantic_settings/
* Uvicorn settings: https://www.uvicorn.org/settings/
* OpenAI Structured Outputs:
  https://platform.openai.com/docs/guides/structured-outputs
* OpenAI Chat Completions API reference:
  https://platform.openai.com/docs/api-reference/chat/create
* OpenAI Responses API reference:
  https://platform.openai.com/docs/api-reference/responses
* DeepSeek first API call:
  https://api-docs.deepseek.com/
* DeepSeek Chat Completions:
  https://api-docs.deepseek.com/api/create-chat-completion
* DeepSeek JSON Output:
  https://api-docs.deepseek.com/guides/json_mode/
* OCS AnswererWrapper API:
  https://docs.ocsjs.com/docs/other/api
* LiteLLM getting started:
  https://docs.litellm.ai/
* LiteLLM structured outputs / JSON mode:
  https://docs.litellm.ai/docs/completion/json_mode
* LiteLLM completion input params:
  https://docs.litellm.ai/docs/completion/input
* LiteLLM unsupported parameter handling:
  https://docs.litellm.ai/docs/completion/drop_params
* AISuite docs:
  https://www.tryaisuite.com/docs
* Pydantic AI model overview:
  https://pydantic.dev/docs/ai/models/overview/
* Pydantic AI OpenAI-compatible providers:
  https://pydantic.dev/docs/ai/models/openai/

## Findings

* Ruff supports project configuration in `pyproject.toml` under `[tool.ruff]`
  and can handle both linting and formatting from the same tool.
* Ruff can infer the Python target version from `project.requires-python`, but
  setting an explicit `target-version` keeps behavior clear for this Python
  3.13 project.
* ty runs with `ty check`; in a project environment, using `uv run ty check`
  lets it discover installed dependencies from the uv-managed environment.
* ty supports project configuration in `pyproject.toml` under `[tool.ty]`.
* uv supports separating runtime dependencies from local development tooling via
  standardized `[dependency-groups]`, including a default `dev` group.
* FastAPI's standard testing approach is `pytest` with
  `fastapi.testclient.TestClient`, which requires `httpx`.
* FastAPI documents `pydantic-settings` as the settings-management path for
  typed environment-variable configuration, `.env` support, dependency
  overrides in tests, and cached settings creation.
* Uvicorn supports programmatic startup through `uvicorn.run(...)`; when used
  from a Python entrypoint, the call should live under
  `if __name__ == "__main__"`.
* OpenAI Structured Outputs provide schema adherence and are preferred over JSON
  mode when the target model/API supports them.
* OpenAI recommends the Responses API for new OpenAI-first projects because it
  is the newer primitive for agentic workflows, built-in tools, stateful
  context, multimodal input, and future OpenAI model features.
* OpenAI also explicitly supports incremental migration: user flows that benefit
  from Responses can move first while other flows remain on Chat Completions.
* Responses changes the request/response shape. Structured Outputs move from
  Chat Completions `response_format` to Responses `text.format`, and output is
  represented as typed response items rather than `choices[0].message.content`.
* OpenAI documents Structured Outputs support in both Chat Completions and
  Responses, but support still depends on the model/API surface. Third-party
  OpenAI-compatible providers may support only a subset of OpenAI's current API
  features.
* JSON mode is weaker than Structured Outputs because it ensures valid JSON but
  not schema adherence.
* DeepSeek documents OpenAI-compatible access through the OpenAI SDK by setting
  `base_url="https://api.deepseek.com"`.
* DeepSeek's documented chat endpoint is `/chat/completions`, and its JSON
  Output mode uses `response_format={"type": "json_object"}` rather than the
  Responses API.
* DeepSeek JSON Output requires the prompt to include the word "json" and an
  example of the desired JSON format. The docs warn that JSON Output may
  occasionally return empty content, so the integration still needs parser
  validation and fallback behavior.
* OCS AnswererWrapper handlers are user-defined JavaScript strings. The common
  successful answer shape is `[question, answer]`, usually guarded by
  `res.code === 1`.
* OCS also documents an error-display pattern for not-found cases:
  the handler can return `[res.msg, undefined]` when `code !== 1`.
* LiteLLM provides both a Python SDK and a Proxy Server described as an LLM
  gateway. The Python SDK exposes a unified OpenAI-style `completion(...)`
  interface, consistent chat-completion-shaped responses, retry/fallback routing
  support, provider exception mapping, and observability callbacks.
* LiteLLM documents `completion(...)` for unified Chat Completions across many
  providers and `responses(...)` for advanced models that support Responses-like
  capabilities.
* LiteLLM supports Chat Completions JSON mode by passing
  `response_format={"type": "json_object"}` to `completion(...)`.
* LiteLLM documents `get_supported_openai_params(...)` as the way to check
  whether a model/provider supports `response_format`.
* LiteLLM raises by default for unsupported OpenAI params; unsupported params
  can be dropped by `drop_params=True` or selectively removed with
  `additional_drop_params`.
* LiteLLM's Proxy Server is a separate central gateway service with auth hooks,
  cost tracking, rate limiting, virtual keys, and an admin/dashboard-style
  operating model.
* AISuite provides a unified Python/TypeScript interface across 20+ providers,
  but its docs emphasize simplicity and provider switching rather than gateway
  operations such as rate limiting, cost tracking, or proxy deployment.
* Pydantic AI is model/provider agnostic and supports OpenAI-compatible
  providers including DeepSeek. It is more of an agent/model framework than a
  lightweight gateway wrapper for this OCS request/answer service.

## Implications For This Project

* Runtime dependencies should include FastAPI, uvicorn, LiteLLM,
  pydantic-settings, and Rich for modern logging output.
* Development dependencies should include `ruff`, `ty`, `pytest`, and `httpx`.
* If package choices prioritize current FastAPI/Python best practice over
  minimal dependencies, configuration should use `pydantic-settings` instead of
  a hand-rolled dataclass loader.
* Quality commands should be documented as `uv run ruff format`,
  `uv run ruff check`, `uv run ty check`, and `uv run pytest`.
* Compatibility tests should use FastAPI `TestClient` to verify `/`, `/search`,
  strict OCS response shapes, and error response shapes without opening a real
  socket.
* Parser tests should exercise reasoning-tag cleanup, Markdown fence cleanup,
  surrounding-text JSON extraction, and malformed JSON fallback behavior.
* Since the project now prioritizes minimal architecture and broad compatibility
  with mainstream OpenAI-compatible providers, Chat Completions is the safest
  default common denominator.
* OpenAI official models remain important, but Responses API should not be the
  default if doing so narrows compatibility with providers that only implement
  the Chat Completions surface.
* Responses API can be revisited later for OpenAI-specific features, but this
  refactor should avoid Responses-specific assumptions in routes, schemas,
  prompts, or tests.
* JSON mode should be enabled automatically only when LiteLLM reports that the
  configured model/provider supports `response_format`. If unsupported, omit
  `response_format` and rely on prompt instructions plus parser validation.
* This project currently uses a simple `res.code === 1 ? [res.question,
  res.answer] : undefined` style handler. Preserving the current handler favors
  returning the old fallback answer shape for LLM parse/provider failures rather
  than switching those failures to `code: 0` in this refactor.
* If the project should use a generic AI gateway library, LiteLLM Python SDK is
  the best fit for a local small API service: it avoids operating a second
  proxy process while preserving a gateway-style provider abstraction. LiteLLM
  Proxy is more appropriate if multiple apps/users need shared keys, budgets,
  auth, or rate limiting.
