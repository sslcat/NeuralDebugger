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
