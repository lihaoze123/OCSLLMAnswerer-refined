# ZError Image and Model Architecture Notes

Reference: https://github.com/Miaozeqiu/ZError

## Relevant Files

* `/tmp/ZError/src/utils/questionImage.ts`
* `/tmp/ZError/src/views/Home.vue`
* `/tmp/ZError/src-tauri/src/commands.rs`
* `/tmp/ZError/src-tauri/src/server.rs`
* `/tmp/ZError/src/services/modelConfig.ts`

## Findings

ZError treats image questions as a distinct path rather than a generic chat-completion message decoration.

* URL detection exists before model dispatch. When title/options contain a URL, ZError marks the request as a URL question and uses a visual analysis flow.
* Image URL parsing is encapsulated in `questionImage.ts`. The parser returns ordered matches with raw URL, normalized URL, start/end offsets, and trailing text so text and images can be reconstructed in order.
* The image URL parser has a local fallback and a remote-replaceable algorithm from the model catalog. For this Python backend, dynamic remote JavaScript execution should not be copied directly, but the parser boundary is useful.
* Image fetching happens locally before calling the vision model. ZError converts images to `data:image/...;base64,...`, not just remote URLs.
* Fetching tries multiple request strategies: full browser-like headers, simpler headers, and mobile headers. It chooses referers for Chaoxing and Zhihuishu.
* Fetched images are cached on disk by URL hash.
* Before sending to vision models, ZError normalizes data URLs by applying a white background and enforcing a minimum image size. It also retries once if provider errors indicate the image is too small.
* ZError separates model categories: text, vision, and summary. The selected vision model is only used when the question contains an image URL.
* For URL questions, ZError builds multimodal content by preserving interleaved text and image order. It fails the visual analysis if any image cannot be downloaded.
* ZError has broader app features outside this Python service's current shape: local question database/cache, UI model management, multi-model comparison, SSE-style frontend/backend model-call bridge, and pending-correction workflow.

## Mapping To This Project

Good ideas to port:

* Split image URL extraction into a dedicated parser module with match/span/parts APIs.
* Convert image URLs to local image content before model call.
* Preserve original text/image ordering in the Pydantic AI prompt input.
* Add disk or memory image cache to avoid re-downloading identical images.
* Use provider-aware request headers/referers for Chaoxing and other education platforms.
* Normalize image bytes before model submission when possible.
* Separate text model and vision model configuration if the user wants text-only and image-aware models to differ.

Ideas to avoid or postpone:

* Executing remote algorithm JavaScript in the Python service.
* Recreating ZError's full Tauri/Vue UI.
* Recreating its SSE model-call bridge. This backend can call Pydantic AI directly.
* Adding a full local question bank/database unless explicitly scoped.

## Design Implications

The image refactor should likely introduce a small backend pipeline:

1. Parse question text/options into ordered text/image parts.
2. Fetch and normalize remote images locally.
3. Convert fetched images into Pydantic AI image input parts.
4. Route to a vision-capable model when images are present.
5. Keep text-only questions on the normal model path.

The biggest unresolved scope decision is whether this task also adds ZError-like local answer caching/question bank behavior, or limits itself to the model/image backend architecture.
