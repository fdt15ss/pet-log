from __future__ import annotations


class ToolRegistry:
    def list_tools(self) -> tuple[object, ...]:
        raise NotImplementedError
