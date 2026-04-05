"""Grep tool — search file contents by regex pattern."""

import re
from pathlib import Path

from pydantic import BaseModel, Field

from notebooks.agent.tools.base import Tool, ToolInvocation, ToolKind, ToolResult


class GrepParams(BaseModel):
    pattern: str = Field(..., description="Regex pattern to search for")
    path: str = Field(".", description="File or directory to search in")
    include: str | None = Field(None, description="Glob pattern to filter files (e.g. '*.py')")
    case_insensitive: bool = Field(False, description="Case-insensitive search")


class GrepTool(Tool):
    name = "grep"
    description = "Search file contents using regex. Returns matching lines with file paths and line numbers."
    kind = ToolKind.READ
    schema = GrepParams

    MAX_MATCHES = 200

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = GrepParams(**invocation.params)
        p = Path(params.path)
        path = p if p.is_absolute() else (invocation.cwd / p).resolve()

        flags = re.IGNORECASE if params.case_insensitive else 0
        try:
            regex = re.compile(params.pattern, flags)
        except re.error as e:
            return ToolResult.error_result(f"Invalid regex: {e}")

        matches: list[str] = []
        files_searched = 0

        if path.is_file():
            files = [path]
        elif path.is_dir():
            if params.include:
                files = sorted(path.rglob(params.include))
            else:
                files = sorted(path.rglob("*"))
            files = [f for f in files if f.is_file()]
        else:
            return ToolResult.error_result(f"Path not found: {path}")

        for file in files:
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            files_searched += 1
            for i, line in enumerate(content.splitlines(), 1):
                if regex.search(line):
                    rel = file.relative_to(invocation.cwd) if file.is_relative_to(invocation.cwd) else file
                    matches.append(f"{rel}:{i}: {line.rstrip()}")
                    if len(matches) >= self.MAX_MATCHES:
                        break
            if len(matches) >= self.MAX_MATCHES:
                break

        if not matches:
            return ToolResult.success_result(
                f"No matches for '{params.pattern}' in {files_searched} files.",
                metadata={"matches": 0, "files_searched": files_searched},
            )

        output = "\n".join(matches)
        truncated = len(matches) >= self.MAX_MATCHES

        if truncated:
            output += f"\n... (showing first {self.MAX_MATCHES} matches)"

        return ToolResult.success_result(
            output=output,
            truncated=truncated,
            metadata={"matches": len(matches), "files_searched": files_searched},
        )
