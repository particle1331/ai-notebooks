"""Glob tool — find files by name pattern."""

from pathlib import Path

from pydantic import BaseModel, Field

from notebooks.agent.tools.base import Tool, ToolInvocation, ToolKind, ToolResult


class GlobParams(BaseModel):
    pattern: str = Field(..., description="Glob pattern to match (e.g. '**/*.py')")
    path: str = Field(".", description="Directory to search in")


class GlobTool(Tool):
    name = "glob"
    description = "Find files matching a glob pattern. Returns matching file paths."
    kind = ToolKind.READ
    schema = GlobParams

    MAX_RESULTS = 500

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = GlobParams(**invocation.params)
        p = Path(params.path)
        path = p if p.is_absolute() else (invocation.cwd / p).resolve()

        if not path.exists():
            return ToolResult.error_result(f"Directory not found: {path}")
        if not path.is_dir():
            return ToolResult.error_result(f"Not a directory: {path}")

        results = sorted(path.rglob(params.pattern))
        total = len(results)
        results = results[: self.MAX_RESULTS]

        lines = []
        for r in results:
            rel = r.relative_to(invocation.cwd) if r.is_relative_to(invocation.cwd) else r
            suffix = "/" if r.is_dir() else ""
            lines.append(f"{rel}{suffix}")

        output = "\n".join(lines) if lines else f"No files matching '{params.pattern}'."
        truncated = total > self.MAX_RESULTS

        if truncated:
            output += f"\n... ({total} total, showing first {self.MAX_RESULTS})"

        return ToolResult.success_result(
            output=output,
            truncated=truncated,
            metadata={"matches": min(total, self.MAX_RESULTS), "total": total},
        )
