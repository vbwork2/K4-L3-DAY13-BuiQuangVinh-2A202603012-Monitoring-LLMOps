from __future__ import annotations

import os
from contextlib import contextmanager
from contextlib import nullcontext
from typing import Any

if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
    os.environ.setdefault("LANGFUSE_TRACING_ENABLED", "false")


class _NoopClient:
    def update_current_span(self, **kwargs: Any) -> None:
        return None

    def update_current_generation(self, **kwargs: Any) -> None:
        return None

    def start_as_current_observation(self, **kwargs: Any):
        return nullcontext(None)


try:
    from langfuse import get_client, observe, propagate_attributes

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - used only before dependencies are installed
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyClient:
        def update_current_span(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

        def start_as_current_observation(self, **kwargs: Any):
            return nullcontext(_DummyObservation())

    class _DummyObservation:
        def update(self, **kwargs: Any) -> None:
            return None

    def get_client():
        return _DummyClient()

    @contextmanager
    def propagate_attributes(**kwargs: Any):
        yield


def get_langfuse_client():
    return get_client() if tracing_enabled() else _NoopClient()


def start_observation(client: Any, **kwargs: Any):
    start = getattr(client, "start_as_current_observation", None)
    return start(**kwargs) if start else nullcontext(None)


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    ) and os.getenv("LANGFUSE_TRACING_ENABLED", "true").lower() != "false"
