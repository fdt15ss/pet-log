from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.tools import BaseTool

from middleware.logging import build_agent_debug_middleware
from tools.profile_tools import build_get_pet_profile_tool
from tools.record_tools import build_list_recent_records_tool, build_save_pet_record_tool


@dataclass(frozen=True)
class ToolRegistry:
    tools: tuple[BaseTool, ...]

    def __post_init__(self) -> None:
        tool_names = tuple(tool.name for tool in self.tools)
        duplicate_names = {
            tool_name
            for tool_name in tool_names
            if tool_names.count(tool_name) > 1
        }
        if duplicate_names:
            names = ", ".join(sorted(duplicate_names))
            raise ValueError(f"Duplicate tool names are not allowed: {names}")

    def list_tools(self) -> tuple[object, ...]:
        return self.tools


@dataclass(frozen=True)
class PetLogToolDependencies:
    profile_repository: Any
    record_repository: Any


@dataclass(frozen=True)
class PetLogNodeRuntime:
    tools: tuple[BaseTool, ...]
    middleware: tuple[object, ...]


def build_context_tools(dependencies: PetLogToolDependencies) -> tuple[BaseTool, ...]:
    return (
        build_get_pet_profile_tool(dependencies.profile_repository),
        build_list_recent_records_tool(dependencies.record_repository),
    )


def build_record_write_tools(dependencies: PetLogToolDependencies) -> tuple[BaseTool, ...]:
    return (build_save_pet_record_tool(dependencies.record_repository),)


def build_pet_log_node_wiring(
    dependencies: PetLogToolDependencies,
) -> dict[str, PetLogNodeRuntime]:
    return {
        "structure_record": PetLogNodeRuntime(tools=(), middleware=()),
        "load_context": PetLogNodeRuntime(
            tools=build_context_tools(dependencies),
            middleware=(build_agent_debug_middleware("load_context"),),
        ),
        "save_records": PetLogNodeRuntime(
            tools=build_record_write_tools(dependencies),
            middleware=(build_agent_debug_middleware("save_records"),),
        ),
    }
