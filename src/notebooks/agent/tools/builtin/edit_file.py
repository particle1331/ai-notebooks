"""Edit file tool — surgical search-and-replace edits."""

from pathlib import Path

from pydantic import BaseModel, Field

from notebooks.agent.tools.base import FileDiff, Tool, ToolConfirmation, ToolInvocation, ToolKind, ToolResult


def _resolve_path(cwd: Path, path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (cwd / p).resolve()


class EditParams(BaseModel):
    path: str = Field(..., description="Path to the file to edit")
    old_string: str = Field("", description="Exact text to find and replace. Empty for new files.")
    new_string: str = Field(..., description="Text to replace old_string with. Can be empty to delete.")
    replace_all: bool = Field(False, description="Replace all occurrences (default: false)")


class EditTool(Tool):
    name = "edit"
    description = (
        "Edit a file by replacing text. old_string must match exactly "
        "(including whitespace) and be unique unless replace_all is true."
    )
    kind = ToolKind.WRITE
    schema = EditParams

    async def get_confirmation(self, invocation: ToolInvocation) -> ToolConfirmation | None:
        params = EditParams(**invocation.params)
        path = _resolve_path(invocation.cwd, params.path)
        is_new = not path.exists()
        old_content = "" if is_new else path.read_text(encoding="utf-8")

        if is_new:
            new_content = params.new_string
        elif params.replace_all:
            new_content = old_content.replace(params.old_string, params.new_string)
        else:
            new_content = old_content.replace(params.old_string, params.new_string, 1)

        return ToolConfirmation(
            tool_name=self.name,
            params=invocation.params,
            description=f"{'Create' if is_new else 'Edit'} file: {path}",
            diff=FileDiff(path=path, old_content=old_content, new_content=new_content, is_new_file=is_new),
            affected_paths=[path],
        )

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = EditParams(**invocation.params)
        path = _resolve_path(invocation.cwd, params.path)

        # New file creation
        if not path.exists():
            if params.old_string:
                return ToolResult.error_result(
                    f"File does not exist: {path}. Use empty old_string for new files."
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(params.new_string, encoding="utf-8")
            lines = len(params.new_string.splitlines())
            return ToolResult.success_result(
                f"Created {path} ({lines} lines)",
                diff=FileDiff(path=path, old_content="", new_content=params.new_string, is_new_file=True),
                metadata={"path": str(path), "is_new_file": True, "lines": lines},
            )

        old_content = path.read_text(encoding="utf-8")

        if not params.old_string:
            return ToolResult.error_result(
                "old_string is empty but file exists. Use write_file to overwrite."
            )

        count = old_content.count(params.old_string)
        if count == 0:
            return ToolResult.error_result(f"old_string not found in {path}.")
        if count > 1 and not params.replace_all:
            return ToolResult.error_result(
                f"old_string found {count} times. Provide more context or set replace_all=true."
            )

        if params.replace_all:
            new_content = old_content.replace(params.old_string, params.new_string)
            replace_count = count
        else:
            new_content = old_content.replace(params.old_string, params.new_string, 1)
            replace_count = 1

        if new_content == old_content:
            return ToolResult.error_result("No change — old_string equals new_string.")

        path.write_text(new_content, encoding="utf-8")
        line_diff = len(new_content.splitlines()) - len(old_content.splitlines())
        diff_msg = f" (+{line_diff} lines)" if line_diff > 0 else (f" ({line_diff} lines)" if line_diff < 0 else "")

        return ToolResult.success_result(
            f"Edited {path}: replaced {replace_count} occurrence(s){diff_msg}",
            diff=FileDiff(path=path, old_content=old_content, new_content=new_content),
            metadata={"path": str(path), "replaced_count": replace_count, "line_diff": line_diff},
        )
