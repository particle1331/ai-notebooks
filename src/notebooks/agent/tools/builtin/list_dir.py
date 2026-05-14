"""List directory tool."""

from pathlib import Path

from pydantic import BaseModel, Field

from notebooks.agent.tools.base import Tool, ToolInvocation, ToolKind, ToolResult


class ListDirParams(BaseModel):
    path: str = Field(".", description="Directory path to list (relative to cwd or absolute)")
    include_hidden: bool = Field(False, description="Include hidden files/directories")


class ListDirTool(Tool):
    name = "list_dir"
    description = "List the contents of a directory. Returns file/directory names with type indicators."
    kind = ToolKind.READ
    schema = ListDirParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ListDirParams(**invocation.params)
        p = Path(params.path)
        path = p if p.is_absolute() else (invocation.cwd / p).resolve()

        if not path.exists():
            return ToolResult.error_result(f"Directory not found: {path}")
        if not path.is_dir():
            return ToolResult.error_result(f"Not a directory: {path}")

        entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        if not params.include_hidden:
            entries = [e for e in entries if not e.name.startswith(".")]

        lines = []
        for entry in entries:
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"  {entry.name}{suffix}")

        output = "\n".join(lines) if lines else "(empty directory)"

        return ToolResult.success_result(
            output=output,
            metadata={"path": str(path), "entries": len(entries)},
        )
