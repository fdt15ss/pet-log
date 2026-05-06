from __future__ import annotations


class TracingMiddleware:
    def apply(self) -> object:
        raise NotImplementedError
