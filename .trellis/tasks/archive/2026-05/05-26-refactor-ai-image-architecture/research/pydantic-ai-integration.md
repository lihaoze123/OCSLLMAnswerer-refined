# Pydantic AI Integration Notes

Sources:

* https://pydantic.dev/docs/ai/core-concepts/output/
* https://pydantic.dev/docs/ai/core-concepts/agent/
* https://pydantic.dev/docs/ai/models/openai/
* https://pydantic.dev/docs/ai/advanced-features/input/
* https://pydantic.dev/docs/ai/overview/install/

## Findings

* Pydantic AI agents can declare `output_type=SomePydanticModel`; the framework uses Pydantic to build the output schema and validate returned model data.
* Structured output is not a guarantee that every model run succeeds. Validation errors can be retried, but exhausting the retry budget raises `UnexpectedModelBehavior`.
* Model/API failures are also explicit exceptions, including provider HTTP errors and content filtering. The application still needs outer fallback behavior.
* Pydantic AI supports OpenAI-compatible providers through `OpenAIChatModel` and `OpenAIProvider(base_url=..., api_key=...)`.
* Pydantic AI also documents a `LiteLLMProvider`, but keeping LiteLLM would preserve a second routing layer. For this task, the agreed scope is to remove LiteLLM.
* Pydantic AI supports image input via `ImageUrl` for provider-side URL fetches and `BinaryContent(data=..., media_type=...)` for local bytes. Since this project needs local fetching for Chaoxing-style images, `BinaryContent` is the better boundary.
* `ModelSettings` supports common request settings like `temperature` and `timeout`.

## Mapping To This Project

* Replace the current `LiteLLMAnswerer` with a Pydantic AI answerer.
* Configure an agent with `output_type=ModelAnswer` to remove hand-written JSON cleanup/extraction code.
* Use direct `Agent.run_sync(...)` unless the FastAPI endpoint is converted to async model calls during implementation.
* Build the Pydantic AI input as ordered text plus `BinaryContent` parts when image URLs are present.
* Keep the outer fallback answer for model/API/validation failures.
