# Paid GPU preflight · blocked

I have completed the local baseline and one-update full-model LoRA pipeline checks on CPU and GPU. I have created zero NeuralDebugger Runpod resources. Project-attributable Runpod spending from these actions is $0. An authenticated provider billing statement is unavailable. The local release has no GitHub remote.

## Candidate and cost model

At 15:59:13 UTC on November 22, 2026, the Runpod public GraphQL catalog returned a low-stock Secure Cloud NVIDIA A40 (48 GB) at $0.59 per GPU-hour. It was the cheapest returned single-GPU on-demand quote among cards with at least 8 GB and positive availability in that snapshot. An earlier $0.24 quote for a 16 GB RTX 2000 Ada disappeared on refresh. The A40 is a candidate for this quote only. A current datacenter, slot, image digest and account-specific price still require confirmation. [Recorded inventory](../results/inventory.json)

I would use one on-demand GPU, the official PyTorch 2.8 CUDA 12.8 template, a 30 GB temporary container disk, zero persistent volume disk and no network or global volumes. I would confirm this exact shape from the creation response and provider read-back. The estimate uses $0.10/GB-month and a conservative 28-day month. Compute plus storage is approximately $0.59447/hour. Runpod documents per-second compute and container billing and zero transfer fees. [Runpod pricing](https://docs.runpod.io/pods/pricing)

| Stage | Elapsed allowance | Estimated compute + storage |
|---|---:|---:|
| Dedicated termination rehearsal | 5 min hard operational deadline | $0.050 |
| Setup, cloud smoke, main LoRA run, transfer and verification | 30 min planning estimate | $0.297 |
| Total expected including rehearsal | 35 min | $0.347 |
| Rehearsal plus maximum 90 min experiment | 95 min | $0.942 |

The time estimate includes idle provisioning, environment setup, download and recovery. It is a planning assumption. I set a $12 operational envelope and reserve $8 of the $20 absolute project ceiling. The controller's separate training cost trigger is $0.90, in addition to its 90-minute deadline. There is no reason to approach $12 for this pilot. Any retry requires a new accounting check including accrued compute, disks, pending usage and prior rehearsal. No automatic reprovisioning is implemented.

## Evidence and open gates

- Data integrity passed for 23 training, 4 validation and 12 held-out source programs. The immutable baseline repaired 10/12 functions and passed 32/36 checks. Automatic category and mechanism scores were both 7/12. [Baseline](../results/base-v1/summary.json)
- Local adapter training, saving, tensor-file checksum verification, reloading, numerical effect and base fallback passed. The cloud configuration uses rank 8, alpha 16, query/value projections, AdamW, three epochs and a maximum of 18 updates. The full-model RTX 4070 SUPER smoke used 3.77 GiB peak PyTorch allocation and completed its update plus validation in 0.86 seconds. Both local smoke adapters are excluded from the product default.
- Public pricing is available. No NeuralDebugger-authorized Runpod API key, authenticated CLI or connected Runpod MCP was available. A Windows credential target is scoped to a different project. I left it untouched.
- I exercised deletion, timeout, stale progress, provider identity mismatch, ambiguous storage and read-back branches against local test doubles. Live shutdown permission, actual provider deletion, out-of-band alerts and account charges remain unverified. A mocked HTTP 204 or a public quote cannot satisfy this gate.
- An estimated cost cutoff cannot enforce a provider lifetime spending cap. Controller-host outage, API failure, delayed accounting and an overlong cleanup interval can all increase charges. Before provisioning I need independently verified provider-side financial safeguards sufficient for the absolute cap, an authorized credential and an already-available, supervised independent controller host with tested alert delivery.
- I need explicit approval of a refreshed, specific preflight **before any billable action**, including a teardown rehearsal. If the prerequisite for approval is a live deletion, that requires a separately authorized, existing disposable project-owned resource or an expressly approved bounded rehearsal. The main training job must wait for verified live termination and confirmed storage cleanup.

## Operating the controller

The watcher lives off-pod. Give its process a scoped Runpod credential via its host secret manager. Keep the pod credential-free. Run the watcher under a service manager configured to restart it with the same durable receipt and alert on failure. Host loss is a separate failure mode. The local Windows workstation alone has no verified always-on or notification guarantee.

1. Run `python -m ops.watchdog arm RECEIPT_DIR --phase rehearsal` to snapshot storage, generate a unique ownership name, and start polling before a create request. An independent provisioning operator must use that exact name, cap, and approved shape. Repeat for training with a fresh directory and training phase only after closing the rehearsal receipt.
2. Require identity and creation-time read-back, a matching GPU and hourly quote, no persistent mounts, an unlocked pod, and the provider's terminate action. The receipt binds this controller to the project pod. Verify SSH access and the digest-pinned PyTorch environment.
3. Run the cloud smoke first. Verify its adapter and logs locally and reconcile elapsed spend. Continue to main training only if the smoke succeeded, the verified remaining budget covers worst-case completion, and the approved quote and deadline still hold.
4. The outer SSH job should stream advancing training-step JSON, copy the selected epoch, hashes, best pointer and metric log locally, and return a nonzero exit on any failure. Wrap it with `python -m ops.supervise RECEIPT_DIR LOCAL_ADAPTER -- COMMAND ...`. The supervisor signals recovered only after verifying a main adapter on local disk. Exceptions and interrupts signal failure. A stalled job trips after six minutes. The independent watchdog remains active even if the supervisor exits unexpectedly.
5. For an emergency, signal the watched directory with an `abort` file. If the watcher is unavailable, run `python -m ops.watchdog emergency RECEIPT_DIR` from a second authorized host with the same receipt, or terminate the matching pod in the Runpod console. A stopped pod can retain a billable disk. Verify permanent termination by exact ID and re-list network and global storage.
6. The controller writes timestamped events and HTTP status codes, writes an immediate local alert on unconfirmed shutdown, retries after failures, and creates a closed marker only after provider read-back and a storage comparison. The operator must route alerts to a monitored channel and test delivery. Review newly appearing volume IDs manually to protect unrelated resources. Reconcile the pod billing line and any delayed charges after deletion, and archive the final receipt.

No paid Runpod result, main training curve, production adapter, or paired fine-tuned result exists at this gate.
