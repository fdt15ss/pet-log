from __future__ import annotations


class RetryMiddleware:
    def apply(self) -> object:
        raise NotImplementedError
