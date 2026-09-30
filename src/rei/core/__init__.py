from typing import Any

__all__ = ["Orchestrator", "PipelineError", "TurnResult", "Executor", "ExecutorError"]


def __getattr__(name: str) -> Any:
    # Lazy re-exports: importing rei.core.cancellation (used by rei.models)
    # must not pull in the orchestrator, which itself imports rei.models.
    if name in ("Orchestrator", "PipelineError", "TurnResult"):
        from rei.core import orchestrator
        return getattr(orchestrator, name)
    if name in ("Executor", "ExecutorError"):
        from rei.core import executor
        return getattr(executor, name)
    raise AttributeError(f"module 'rei.core' has no attribute {name!r}")
