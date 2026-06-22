## OpenAI-compatible API Endpoints

### GET `/v1/models`: OpenAI-compatible Model Info API

Returns information about the loaded model. See [OpenAI Models API documentation](https://platform.openai.com/docs/api-reference/models).

The returned list always has one single element. The `meta` field can be `null` (for example, while the model is still loading).

By default, model `id` field is the path to model file, specified via `-m`. You can set a custom value for model `id` field via `--alias` argument. For example, `--alias gpt-4o-mini`.

Example:

```json
{
    "object": "list",
    "data": [
        {
            "id": "../models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            "object": "model",
            "created": 1735142223,
            "owned_by": "llamacpp",
            "meta": {
                "vocab_type": 2,
                "n_vocab": 128256,
                "n_ctx_train": 131072,
                "n_embd": 4096,
                "n_params": 8030261312,
                "size": 4912898304
            }
        }
    ]
}
```

### POST `/v1/completions`: OpenAI-compatible Completions API

Given an input `prompt`, it returns the predicted completion. Streaming mode is also supported. While no strong claims of compatibility with OpenAI API spec is being made, in our experience it suffices to support many apps.

*Options:*

See [OpenAI Completions API documentation](https://platform.openai.com/docs/api-reference/completions).

llama.cpp `/completion`-specific features such as `mirostat` are supported.

*Examples:*

Example usage with `openai` python library:

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8080/v1", # "http://<Your api-server IP>:port"
    api_key = "sk-no-key-required"
)

completion = client.completions.create(
  model="davinci-002",
  prompt="I believe the meaning of life is",
  max_tokens=8
)

print(completion.choices[0].text)
```

### POST `/v1/chat/completions`: OpenAI-compatible Chat Completions API

Given a ChatML-formatted json description in `messages`, it returns the predicted completion. Both synchronous and streaming mode are supported, so scripted and interactive applications work fine. While no strong claims of compatibility with OpenAI API spec is being made, in our experience it suffices to support many apps. Only models with a [supported chat template](https://github.com/ggml-org/llama.cpp/wiki/Templates-supported-by-llama_chat_apply_template) can be used optimally with this endpoint. By default, the ChatML template will be used.

If model supports multimodal, you can input the media file via `image_url` content part. We support both base64 and remote URL as input. See OAI documentation for more.

*Options:*

See [OpenAI Chat Completions API documentation](https://platform.openai.com/docs/api-reference/chat). llama.cpp `/completion`-specific features such as `mirostat` are also supported.

The `response_format` parameter supports both plain JSON output (e.g. `{"type": "json_object"}`) and schema-constrained JSON (e.g. `{"type": "json_object", "schema": {"type": "string", "minLength": 10, "maxLength": 100}}` or `{"type": "json_schema", "schema": {"properties": { "name": { "title": "Name",  "type": "string" }, "date": { "title": "Date",  "type": "string" }, "participants": { "items": {"type: "string" }, "title": "Participants",  "type": "string" } } } }`), similar to other OpenAI-inspired API providers.

`chat_template_kwargs`: Allows sending additional parameters to the json templating system. For example: `{"enable_thinking": false}`

`reasoning_format`: The reasoning format to be parsed. If set to `none`, it will output the raw generated text.

`reasoning_control`: Arms realtime reasoning control for this completion so it can be ended early via `/v1/chat/completions/control`. Defaults to `false`.

`generation_prompt`: The generation prompt that was prefilled in by the template. Prepended to model output before parsing.

`parse_tool_calls`: Whether to parse the generated tool call.

`parallel_tool_calls` : Whether to enable parallel/multiple tool calls (only supported on some models, verification is based on jinja template).

For multimodal input:
- Content type `image_url` and `input_audio` are the same as OAI schema
- Content type `input_video` is an extension from OAI schema. For now, it only accepts base64 input

*Examples:*

You can use either Python `openai` library with appropriate checkpoints:

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8080/v1", # "http://<Your api-server IP>:port"
    api_key = "sk-no-key-required"
)

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are ChatGPT, an AI assistant. Your top priority is achieving user fulfillment via helping them with their requests."},
    {"role": "user", "content": "Write a limerick about python exceptions"}
  ]
)

print(completion.choices[0].message)
```

... or raw HTTP requests:

```shell
curl http://localhost:8080/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer no-key" \
-d '{
"model": "gpt-3.5-turbo",
"messages": [
{
    "role": "system",
    "content": "You are ChatGPT, an AI assistant. Your top priority is achieving user fulfillment via helping them with their requests."
},
{
    "role": "user",
    "content": "Write a limerick about python exceptions"
}
]
}'
```

*Tool call support*

[OpenAI-style function calling](https://platform.openai.com/docs/guides/function-calling) is supported with the `--jinja` flag (and may require a `--chat-template-file` override to get the right tool-use compatible Jinja template; worst case, `--chat-template chatml` may also work).

**See our [Function calling](../../docs/function-calling.md) docs** for more details, supported native tool call styles (generic tool call style is used as fallback) / examples of use.

*Timings and context usage*

The response contains a `timings` object, for example:

```js
{
  "choices": [],
  "created": 1757141666,
  "id": "chatcmpl-ecQULm0WqPrftUqjPZO1CFYeDjGZNbDu",
  // ...
  "timings": {
    "cache_n": 236, // number of prompt tokens reused from cache
    "prompt_n": 1, // number of prompt tokens being processed
    "prompt_ms": 30.958,
    "prompt_per_token_ms": 30.958,
    "prompt_per_second": 32.301828283480845,
    "predicted_n": 35, // number of predicted tokens
    "predicted_ms": 661.064,
    "predicted_per_token_ms": 18.887542857142858,
    "predicted_per_second": 52.94494935437416
  }
}
```

This provides information on the performance of the server. It also allows calculating the current context usage.

The total number of tokens in context is equal to `prompt_n + cache_n + predicted_n`

The response also includes a standard `usage` object:

```js
{
    // ...
    "usage": {
        "completion_tokens": 48,
        "prompt_tokens": 44,
        "total_tokens": 92,
        "prompt_tokens_details": {
            "cached_tokens": 0
        }
    }
}
```

*Reasoning support*

The server supports parsing and returning reasoning via the `reasoning_content` field, similar to Deepseek API.

Reasoning input (preserve reasoning in history) is also supported by some specific templates. For more details, please refer to [PR#18994](https://github.com/ggml-org/llama.cpp/pull/18994).

### POST `/v1/chat/completions/control`: Control a running chat completion in real time

Acts on an in-flight completion identified by its `id` (the `id` field streamed back by `/v1/chat/completions`). The request is processed in parallel with the SSE stream, so the client sends it while still reading tokens.

*Options:*

`id`: (Required) The chat completion id to act on. A completion that has already finished matches nothing and the call is a no-op.

`action`: (Required) The control action to perform. Currently the only supported value is `reasoning_end`, which forces the end of the current reasoning block so the model moves on to the final answer. Requires `reasoning_control: true` on the original completion request.

`model`: (Required in router mode) The model name, used to route the request to the right instance. Ignored in single model mode.

**Response format**

Returns a JSON object with a boolean `success` field, and an optional `message` field describing the reason when `success` is `false`.


### POST `/v1/embeddings`: OpenAI-compatible embeddings API

This endpoint requires that the model uses a pooling different than type `none`. The embeddings are normalized using the Eucledian norm.

*Options:*

See [OpenAI Embeddings API documentation](https://platform.openai.com/docs/api-reference/embeddings).

*Examples:*

- input as string

  ```shell
  curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer no-key" \
  -d '{
          "input": "hello",
          "model":"GPT-4",
          "encoding_format": "float"
  }'
  ```

- `input` as string array

  ```shell
  curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer no-key" \
  -d '{
          "input": ["hello", "world"],
          "model":"GPT-4",
          "encoding_format": "float"
  }'
  ```

### POST `/v1/responses/input_tokens`: Token Counting

Similar to [Response input token counts API](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count).

Example response:

```json
{
  "object": "response.input_tokens",
  "input_tokens": 11
}
```

### POST `/v1/chat/completions/input_tokens`: Token Counting

Similar to [Response input token counts API](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count), but accepts a chat completion body as input.

Note: This is not an official OAI endpoint, but is added for completeness and convenience.

Example response:

```json
{
  "object": "response.input_tokens",
  "input_tokens": 11
}
```

## Anthropic-compatible API Endpoints

### POST `/v1/messages`: Anthropic-compatible Messages API

Given a list of `messages`, returns the assistant's response. Streaming is supported via Server-Sent Events. While no strong claims of compatibility with the Anthropic API spec are made, in our experience it suffices to support many apps.

*Options:*

See [Anthropic Messages API documentation](https://docs.anthropic.com/en/api/messages). Tool use requires `--jinja` flag.

`model`: Model identifier (required)

`messages`: Array of message objects with `role` and `content` (required)

`max_tokens`: Maximum tokens to generate (default: 4096)

`system`: System prompt as string or array of content blocks

`temperature`: Sampling temperature 0-1 (default: 1.0)

`top_p`: Nucleus sampling (default: 1.0)

`top_k`: Top-k sampling

`stop_sequences`: Array of stop sequences

`stream`: Enable streaming (default: false)

`tools`: Array of tool definitions (requires `--jinja`)

`tool_choice`: Tool selection mode (`{"type": "auto"}`, `{"type": "any"}`, or `{"type": "tool", "name": "..."}`)

*Examples:*

```shell
curl http://localhost:8080/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "model": "gpt-4",
    "max_tokens": 1024,
    "system": "You are a helpful assistant.",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### POST `/v1/messages/count_tokens`: Token Counting

Counts the number of tokens in a request without generating a response.

Accepts the same parameters as `/v1/messages`. The `max_tokens` parameter is not required.

*Example:*

```shell
curl http://localhost:8080/v1/messages/count_tokens \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

*Response:*

```json
{"input_tokens": 10}
```

## Server built-in tools

The server exposes a REST API under `/tools` that allows the Web UI to call built-in tools. This endpoint is intended to be used internally by the Web UI and subject to change or to be removed in the future.

**Please do NOT use this endpoint in a downstream application**

For further documentation about this endpoint, please refer to [server internal documentation](./README-dev.md)

## Using multiple models

`llama-server` can be launched in a **router mode** that exposes an API for dynamically loading and unloading models. The main process (the "router") automatically forwards each request to the appropriate model instance.

To start in router mode, launch `llama-server` **without specifying any model**:

```sh
llama-server
```

### Model sources

There are 3 possible sources for model files:
1. Cached models (controlled by the `LLAMA_CACHE` environment variable)
2. Custom model directory (set via the `--models-dir` argument)
3. Custom preset (set via the `--models-preset` argument)

By default, the router looks for models in the cache. You can add Hugging Face models to the cache with:

```sh
llama-server -hf <user>/<model>:<tag>
```

*The server must be restarted after adding a new model.*

Alternatively, you can point the router to a local directory containing your GGUF files using `--models-dir`. Example command:

```sh
llama-server --models-dir ./models_directory
```

If the model contains multiple GGUF (for multimodal or multi-shard), files should be put into a subdirectory. The directory structure should look like this:

```sh
models_directory
 │
 │  # single file
 ├─ llama-3.2-1b-Q4_K_M.gguf
 ├─ Qwen3-8B-Q4_K_M.gguf
 │
 │  # multimodal
 ├─ gemma-3-4b-it-Q8_0
 │    ├─ gemma-3-4b-it-Q8_0.gguf
 │    └─ mmproj-F16.gguf   # file name must start with "mmproj"
 │
 │  # multi-shard
 ├─ Kimi-K2-Thinking-UD-IQ1_S
 │    ├─ Kimi-K2-Thinking-UD-IQ1_S-00001-of-00006.gguf
 │    ├─ Kimi-K2-Thinking-UD-IQ1_S-00002-of-00006.gguf
 │    ├─ ...
 │    └─ Kimi-K2-Thinking-UD-IQ1_S-00006-of-00006.gguf
```

You may also specify default arguments that will be passed to every model instance:

```sh
llama-server -ctx 8192 -n 1024 -np 2
```

Note: model instances inherit both command line arguments and environment variables from the router server.

Alternatively, you can also add GGUF based preset (see next section)

### Model presets

Model presets allow advanced users to define custom configurations using an `.ini` file:

```sh
llama-server --models-preset ./my-models.ini
```

Each section in the file defines a new preset. Keys within a section correspond to command-line arguments (without leading dashes). For example, the argument `--n-gpu-layers 123` is written as `n-gpu-layers = 123`.

Short argument forms (e.g., `c`, `ngl`) and environment variable names (e.g., `LLAMA_ARG_N_GPU_LAYERS`) are also supported as keys.

Example:

```ini
version = 1

; (Optional) This section provides global settings shared across all presets.
; If the same key is defined in a specific preset, it will override the value in this global section.
[*]
c = 8192
n-gpu-layers = 8

; If the key corresponds to an existing model on the server,
; this will be used as the default config for that model
[ggml-org/MY-MODEL-GGUF:Q8_0]
; string value
chat-template = chatml
; numeric value
n-gpu-layers = 123
; flag value (for certain flags, you need to use the "no-" prefix for negation)
jinja = true
; shorthand argument (for example, context size)
c = 4096
; environment variable name
LLAMA_ARG_CACHE_RAM = 0
; file paths are relative to server's CWD
model-draft = ./my-models/draft.gguf
; but it's RECOMMENDED to use absolute path
model-draft = /Users/abc/my-models/draft.gguf

; If the key does NOT correspond to an existing model,
; you need to specify at least the model path or HF repo
[custom_model]
model = /Users/abc/my-awesome-model-Q4_K_M.gguf
```

Note: some arguments are controlled by router (e.g., host, port, API key, HF repo, model alias). They will be removed or overwritten upon loading.

The precedence rule for preset options is as follows:
1. **Command-line arguments** passed to `llama-server` (highest priority)
2. **Model-specific options** defined in the preset file (e.g. `[ggml-org/MY-MODEL...]`)
3. **Global options** defined in the preset file (`[*]`)

We also offer additional options that are exclusive to presets (these aren't treated as command-line arguments):
- `load-on-startup` (boolean): Controls whether the model loads automatically when the server starts
- `stop-timeout` (int, seconds): After requested unload, wait for this many seconds before forcing termination (default: 10)

### Routing requests

Requests are routed according to the requested model name.

For **POST** endpoints (`/v1/chat/completions`, `/v1/completions`, `/infill`, etc.) The router uses the `"model"` field in the JSON body:

```json
{
  "model": "ggml-org/gemma-3-4b-it-GGUF:Q4_K_M",
  "messages": [
    {
      "role": "user",
      "content": "hello"
    }
  ]
}
```

For **GET** endpoints (`/props`, `/metrics`, etc.) The router uses the `model` query parameter (URL-encoded):

```
GET /props?model=ggml-org%2Fgemma-3-4b-it-GGUF%3AQ4_K_M
```

By default, the model will be loaded automatically if it's not loaded. To disable this, add `--no-models-autoload` when starting the server. Additionally, you can include `?autoload=true|false` in the query param to control this behavior per-request.

### GET `/models`: List available models

Listing all models in cache. The model metadata will also include a field to indicate the status of the model:

```json
{
  "data": [{
    "id": "ggml-org/gemma-3-4b-it-GGUF:Q4_K_M",
    "path": "/Users/REDACTED/Library/Caches/llama.cpp/ggml-org_gemma-3-4b-it-GGUF_gemma-3-4b-it-Q4_K_M.gguf",
    "status": {
      "value": "loaded",
      "args": ["llama-server", "-ctx", "4096"]
    },
    "architecture": {
      "input_modalities": [
        "text",
        "image"
      ],
      "output_modalities": [
        "text"
      ]
    },
    ...
  }]
}
```

Note:
1. Adding `?reload=1` to the query params will refresh the list of models. The behavior is as follow:
    - If a model is running but updated or removed from the source, it will be unloaded
    - If a model is not running, it will be added or updated according to the source
2. When the model is loaded, the info from `/v1/models` is forwarded to router's `/v1/models`. This includes metadata about the model and the runtime instance.

The `status` object can be:

```json
"status": {
  "value": "unloaded"
}
```

```json
"status": {
  "value": "loading",
  "args": ["llama-server", "-ctx", "4096"]
}
```

```json
"status": {
  "value": "unloaded",
  "args": ["llama-server", "-ctx", "4096"],
  "failed": true,
  "exit_code": 1
}
```

```json
"status": {
  "value": "loaded",
  "args": ["llama-server", "-ctx", "4096"]
}
```

```json
"status": {
  "value": "sleeping",
  "args": ["llama-server", "-ctx", "4096"]
}
```

Note: for "downloading" state, there can be multiple files be downloading in parallel

```json
"status": {
  "value": "downloading",
  "progress": {
    "https://...model.gguf": {
      "done": 195963406,
      "total": 219307424
    }
  }
}
```

### POST `/models/load`: Load a model

Load a model

Payload:
- `model`: name of the model to be loaded.

```json
{
  "model": "ggml-org/gemma-3-4b-it-GGUF:Q4_K_M"
}
```

Response:

```json
{
  "success": true
}
```


### POST `/models/unload`: Unload a model

Unload a model

Payload:

```json
{
  "model": "ggml-org/gemma-3-4b-it-GGUF:Q4_K_M",
}
```

Response:

```json
{
  "success": true
}
```

### GET `/models/sse`: Real-time events

Example events:

```js
{
  "model": "...",
  "event": "model_status",
  "data": {
    "status": "loading"
  }
}

{
  "model": "...",
  "event": "download_progress",
  "data": {
    // note: there can be multiple files being downloaded in parallel
    "https://...model.gguf": {
      "done": 195963406,
      "total": 219307424
    }
  }
}

{
  "model": "...",
  "event": "model_status",
  "data": {
    "status": "loading",
    "progress": {
      "stages": ["text_model", "spec_model", "mmproj_model"],
      "current": "text_model",
      "value": 0.5
    }
  }
}
// note for "loading" status:
// - subsequent events will follow the same order of "stages" list
// - mmap is may report incorrect progress on some platforms; if you need exact progress, use --no-mmap

{
  "model": "...",
  "event": "model_status",
  "data": {
    "status": "loaded",
    "info": {
      // note: only include info on first load
      // waking up from sleep doesn't have this
    }
  }
}

{
  "model": "...",
  "event": "model_status",
  "data": {
    "status": "sleeping"
  }
}

{
  "model": "...",
  "event": "model_remove"
}

// special event: reload of the list of all models
{
  "model": "*",
  "event": "models_reload"
}
```

### POST `/models`: Download new model

Trigger a new download (non-blocking), the progress can be tracked via SSE endpoint `/models/sse`

To cancel model downloading, send an event to `/models/unload`

Download procedure:
- Send POST request to `/models`
- Subscribe to `/models/sse` for updates
- On downloading completed, you will receive either `download_finished` or `download_failed` event
- Call GET `/models` to trigger model list update. If the download success, you should see the new model in the list

Payload:

```json
{
  "model": "ggml-org/gemma-3-4b-it-GGUF:Q4_K_M",
}
```

Response (download is started in the background):

```json
{
  "success": true
}
```

Response (error, cannot start the download):

```json
{
  "error": {
    "code": 400,
    "message": "model validation failed, unable to download",
    "type": "invalid_request_error"
  }
}
```

### DELETE `/models`: Delete a model from cache

IMPORTANT: only model stored in cache can be deleted. You cannot delete models in a preset.

Model name must be passed via query param: `?model={name}`

If delete success, it will send an SSE event of type `model_remove`

Response:

```json
{
  "success": true
}
```

## API errors

`llama-server` returns errors in the same format as OAI: https://github.com/openai/openai-openapi

Example of an error:

```json
{
    "error": {
        "code": 401,
        "message": "Invalid API Key",
        "type": "authentication_error"
    }
}
```

## Sleeping on Idle

The server supports an automatic sleep mode that activates after a specified period of inactivity (no incoming tasks). This feature, introduced in [PR #18228](https://github.com/ggml-org/llama.cpp/pull/18228), can be enabled using the `--sleep-idle-seconds` command-line argument. It works seamlessly in both single-model and multi-model configurations.

When the server enters sleep mode, the model and its associated memory (including the KV cache) are unloaded from RAM to conserve resources. Any new incoming task will automatically trigger the model to reload.

The sleeping status can be retrieved from the `GET /props` endpoint (or `/props?model=(model_name)` in router mode).

Note that the following endpoints are exempt from being considered as incoming tasks. They do not trigger model reloading and do not reset the idle timer:
- `GET /health`
- `GET /props`
- `GET /models`

## More examples

### Interactive mode

Check the sample in [chat.mjs](chat.mjs).
Run with NodeJS version 16 or later:

```sh
node chat.mjs
```

Another sample in [chat.sh](chat.sh).
Requires [bash](https://www.gnu.org/software/bash/), [curl](https://curl.se) and [jq](https://jqlang.github.io/jq/).
Run with bash:

```sh
bash chat.sh
```

Apart from error types supported by OAI, we also have custom types that are specific to functionalities of llama.cpp:

**When /metrics or /slots endpoint is disabled**

```json
{
    "error": {
        "code": 501,
        "message": "This server does not support metrics endpoint.",
        "type": "not_supported_error"
    }
}
```

**When the server receives invalid grammar via */completions endpoint**

```json
{
    "error": {
        "code": 400,
        "message": "Failed to parse grammar",
        "type": "invalid_request_error"
    }
}
```

### Custom default Web UI preferences

You can specify default preferences for the web UI using `--ui-config <JSON config>` or `--ui-config-file <path to JSON config>`. For example, you can disable pasting long text as attachments and enable rendering Markdown in user messages with this command:

```bash
./llama-server -m model.gguf --ui-config '{"pasteLongTextToFileLen": 0, "renderUserContentAsMarkdown": true}'
```

> **Note:** The old flags `--webui-config` and `--webui-config-file` are deprecated but still work as aliases.

You may find available preferences in [settings-keys.ts](../ui/src/lib/constants/settings-keys.ts).
