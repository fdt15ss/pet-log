from __future__ import annotations


class LoggingMiddleware:
    def apply(self) -> object:
        raise NotImplementedError
