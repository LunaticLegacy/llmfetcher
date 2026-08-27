# llmfetcher/execution/ — Attempt Control INDEX

| File | Responsibility |
|---|---|
| `controller.py` | `ExecutionController`, stop request/mode, resource cancellation registry and steering queue. |
| `__init__.py` | Public execution-control exports. |

This package owns in-process cooperative/forced cancellation mechanics only.
It does not own Session identity, worker thread lifecycle, durable events or
checkpoint persistence; those belong to the Angelus execution layer.

## Class Map

| Source | Class | Semantics |
|---|---|---|
| `controller.py` | `StopMode` | Strategy selector: graceful safe-boundary stop or forced resource cancellation. |
| `controller.py` | `StopRequest` | Immutable reason/mode/timestamp record shared by every canceller. |
| `controller.py` | `ExecutionController` | Attempt-local cancellation, resource and steering authority. |
