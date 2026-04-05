"""Read file tool."""

from pathlib import Path

from pydantic import BaseModel, Field

from notebooks.agent.tools.base import Tool, ToolInvocation, ToolKind, ToolResult


def _resolve_path(cwd: Path, path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (cwd / p).resolve()


def _is_binary_file(path: Path, sample_size: int = 8192) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(sample_size)
        return b"\x00" in chunk
    except Exception:
        return False


class ReadFileParams(BaseModel):
    path: str = Field(..., description="Path to the file to read (relative to cwd or absolute)")
    offset: int = Field(1, ge=1, description="Line number to start from (1-based)")
    limit: int | None = Field(None, ge=1, description="Maximum number of lines to read")


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Read the contents of a text file. Returns content with line numbers. "
        "For large files, use offset and limit to read specific portions."
    )
    kind = ToolKind.READ
    schema = ReadFileParams

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ReadFileParams(**invocation.params)
        path = _resolve_path(invocation.cwd, params.path)

        if not path.exists():
            return ToolResult.error_result(f"File not found: {path}")
        if not path.is_file():
            return ToolResult.error_result(f"Not a file: {path}")
        if path.stat().st_size > self.MAX_FILE_SIZE:
            return ToolResult.error_result(f"File too large: {path.stat().st_size} bytes")
        if _is_binary_file(path):
            return ToolResult.error_result(f"Cannot read binary file: {path.name}")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

        lines = content.splitlines()
        total = len(lines)
        start = max(0, params.offset - 1)
        end = min(start + params.limit, total) if params.limit else total

        formatted = [f"{i:6}|{line}" for i, line in enumerate(lines[start:end], start=start + 1)]
        output = "\n".join(formatted) if formatted else "File is empty."

        header = ""
        if start > 0 or end < total:
            header = f"Showing lines {start + 1}-{end} of {total}\n\n"

        return ToolResult.success_result(
            output=header + output,
            metadata={"path": str(path), "total_lines": total, "shown_start": start + 1, "shown_end": end},
        )
