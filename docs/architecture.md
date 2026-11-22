# Architecture

I serve the workbench and API from one loopback FastAPI service. An analysis request carries Python source and an observed exception or failing expectation. Pydantic rejects extra fields, blank requests and excessive text. The worker checks token length again after applying the pinned chat template.

```text
Browser → POST /api/analyze → validation → single model worker
                                            ↓
                                 Qwen base or PEFT adapter
                                            ↓
                        JSON schema → diagnosis and active mode
```

I launch the model in a separate, persistent Python subprocess on first use. It loads once, processes one request at a time, and emits newline-delimited JSON. An overlapping request gets HTTP 429. A hard request timeout kills the subprocess, and a later request starts a fresh worker. The status endpoint distinguishes the configured backend from the actually loaded model. The adapter loader checks model identity, reloads a clean base on failure, and reports the fallback. Benchmark runs use strict adapter loading.

The application never executes submitted Python or proposed corrections. The browser renders every submitted and generated string as text. Clipboard access requires a browser-supported local or secure context. I keep requests in memory and avoid logging source text. Uvicorn's default access log contains route, status, and timing information external to the model worker.

I use JSONL for the offline corpora and experiment outputs so individual cases can be inspected without framework-specific tooling. Training reads the train and validation files. The offline benchmark owns the held-out file and capability-isolated patch interpreter. The Runpod watchdog has its own process, credentials and time budget. It runs outside the pod and outside the training process.

I designed this service for a single local user. Bind to loopback. It has no multi-tenant authentication or public-service abuse controls.

For a directly evidenced call that tests a bound string strip method, the worker supplies a labeled Python semantics check for the prose. It examines the AST and a literal-string failing call. The model still supplies the patch. The offline benchmark evaluates raw generations and bypasses this presentation rule.

## Local trust boundary

I verify the base configuration, weights, tokenizer and generation settings against the pinned revision before loading. The adapter path is chosen by the person running the server. The request schema accepts only code and traceback. I use a local safetensors checkpoint and construct the LoRA architecture from the project's training settings. Unexpected adapter configurations or missing files activate the base fallback. I treat the checkout, its manifests and the local administrator as trusted.

I use the WASI guest for historical fixture generation as well as v2 corpus verification and offline patch scoring. The HTTP service never imports a submitted module or runs a proposed correction. The worker tokenizes the submission; the narrow truthiness check reads its AST. [Sandbox limits and tests](evaluation.md)

## Hybrid inference

I use one Transformers backbone with an unmerged PEFT adapter. The adapter generates a category value first. I then enter PEFT's disable_adapter context and run a fresh base-model repair with the complete code and observed failure. Each stage has its own prompt and generation cache. The worker already serializes requests, so another user cannot interleave adapter state changes during a repair. Leaving the context restores the adapter even if generation raises.

The display-only path uses the original base repair prompt. The conditioned path adds a structured classifier_hint field to the user message and tells the base model to verify it. When the short classification output is unusable, the base repair supplies its own category. When a valid hint would exceed the token budget, the worker retains the complete original request and omits the hint. A missing or unloadable adapter activates the existing base backend.

POST /api/analyze retains the original diagnosis schema. A hybrid response also includes a hybrid object containing classifier_category, conditioned, and fallback. The UI shows the active configuration and what happened on that request. The existing Python semantics check runs on the resulting prose after inference. The offline experiment records the original repair text and classifier completion before any presentation corrections.
