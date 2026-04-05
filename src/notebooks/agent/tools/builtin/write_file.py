"""Write file tool."""

from pathlib import Path

from pydantic import BaseModel, Field

from notebooks.agent.tools.base import FileDiff, Tool, ToolConfirmation, ToolInvocation, ToolKind, ToolResult


def _resolve_path(cwd: Path, path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (cwd / p).resolve()


class WriteFileParams(BaseModel):
    path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")
    create_directories: bool = Field(True, description="Create parent directories if needed")


class WriteFileTool(Tool):
    name = "write_file"
    description = "Create or overwrite a file with the given content."
    kind = ToolKind.WRITE
    schema = WriteFileParams

    async def get_confirmation(self, invocation: ToolInvocation) -> ToolConfirmation | None:
        params = WriteFileParams(**invocation.params)
        path = _resolve_path(invocation.cwd, params.path)
        old_content = path.read_text(encoding="utf-8") if path.exists() else ""
        return ToolConfirmation(
            tool_name=self.name,
            params=invocation.params,
            description=f"{'Overwrite' if path.exists() else 'Create'} file: {path}",
            diff=FileDiff(path=path, old_content=old_content, new_content=params.content, is_new_file=not path.exists()),
            affected_paths=[path],
        )

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = WriteFileParams(**invocation.params)
        path = _resolve_path(invocation.cwd, params.path)

        old_content = ""
        is_new = not path.exists()

        if not is_new:
            old_content = path.read_text(encoding="utf-8")

        if params.create_directories:
            path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(params.content, encoding="utf-8")
        line_count = len(params.content.splitlines())

        return ToolResult.success_result(
            f"{'Created' if is_new else 'Wrote'} {path} ({line_count} lines)",
            diff=FileDiff(path=path, old_content=old_content, new_content=params.content, is_new_file=is_new),
            metadata={"path": str(path), "is_new_file": is_new, "lines": line_count},
        )
