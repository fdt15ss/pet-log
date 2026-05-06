from __future__ import annotations


class ValidationMiddleware:
    def apply(self) -> object:
        raise NotImplementedError
