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

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [control.py](control.py#L66) | `ExecutionController.stop_request` | `None` | `StopRequest \| None` | Return the current request, if any, without mutating its state. |
| [control.py](control.py#L71) | `ExecutionController.request_stop` | `mode: StopMode, reason: str` | `StopRequest` | Request graceful stop or escalate it to forced resource cancellation. |
| [control.py](control.py#L118) | `ExecutionController.register_force_canceller` | `cancel: Callable[[StopRequest], None]` | `Callable[[], None]` | Register one active resource closer and return its unregister handle. |
| [control.py](control.py#L155) | `ExecutionController.wait_for_stop` | `timeout: float \| None` | `StopRequest \| None` | Wait for a stop request and return the current request when present. |
| [control.py](control.py#L168) | `ExecutionController.should_stop` | `None` | `bool` | Return whether any stop strategy has been requested. |
| [control.py](control.py#L177) | `ExecutionController.force_stopped` | `None` | `threading.Event` | Expose an event for existing streaming loops during migration. |
| [control.py](control.py#L185) | `ExecutionController.steer` | `message: str` | `None` | Queue one non-empty steering message for the next safe boundary. |
| [control.py](control.py#L190) | `ExecutionController.drain_steers` | `None` | `list[str]` | Return and consume queued steering messages in FIFO order. |
| [control.py](control.py#L200) | `current_execution_controller` | `None` | `ExecutionController \| None` | Return the controller bound to the currently executing tool worker. |
| [control.py](control.py#L206) | `bind_execution_controller` | `controller: ExecutionController \| None` | `Any` | Bind one controller to a worker without exposing it as tool input. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [control.py](control.py#L22) | `StopMode` | `None` | `StrEnum` | The strategy used to reach the single ``stopped`` terminal result. |
| [control.py](control.py#L30) | `StopRequest` | `mode: StopMode, reason: str, requested_at: float` | `object` | Immutable stop intent shared by every execution boundary. |
| [control.py](control.py#L45) | `ExecutionController` | `None` | `object` | Coordinate one execution's stop strategy, steering, and live resources. |

<!-- END GENERATED SYMBOL MAP -->
