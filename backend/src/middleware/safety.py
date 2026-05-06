from __future__ import annotations


class SafetyMiddleware:
    def apply(self) -> object:
        raise NotImplementedError
