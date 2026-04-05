"""Todo list tool — manage a simple task list backed by a JSON file."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from notebooks.agent.tools.base import Tool, ToolInvocation, ToolKind, ToolResult

_DEFAULT_TODO_PATH = Path.home() / ".cda" / "todos.json"


@dataclass
class TodoItem:
    id: int
    text: str
    done: bool = False


def _load_todos(path: Path) -> list[TodoItem]:
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return [TodoItem(**item) for item in raw]
        except Exception:
            return []
    return []


def _save_todos(path: Path, todos: list[TodoItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(t) for t in todos], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _next_id(todos: list[TodoItem]) -> int:
    return max((t.id for t in todos), default=0) + 1


class TodoParams(BaseModel):
    action: str = Field(
        ...,
        description=(
            "Operation to perform: "
            "'add' (create a task), "
            "'done' (mark task complete by id), "
            "'delete' (remove task by id), "
            "'list' (show all tasks), "
            "'clear' (delete all tasks)"
        ),
    )
    text: str | None = Field(None, description="Task description (required for 'add')")
    id: int | None = Field(None, description="Task ID (required for 'done' and 'delete')")


class TodoTool(Tool):
    name = "todo"
    kind = ToolKind.MEMORY
    description = (
        "Manage a persistent todo list. "
        "Use 'add' to create tasks, 'done' to mark them complete, "
        "'list' to review them, 'delete' to remove, 'clear' to reset."
    )
    schema = TodoParams

    def _store_path(self) -> Path:
        return _DEFAULT_TODO_PATH

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = TodoParams(**invocation.params)
        path = self._store_path()
        todos = _load_todos(path)

        action = params.action.lower().strip()

        if action == "add":
            if not params.text:
                return ToolResult.error_result("'text' is required for action='add'")
            item = TodoItem(id=_next_id(todos), text=params.text, done=False)
            todos.append(item)
            _save_todos(path, todos)
            return ToolResult.success_result(
                f"Added task #{item.id}: {item.text}",
                metadata={"id": item.id},
            )

        elif action == "done":
            if params.id is None:
                return ToolResult.error_result("'id' is required for action='done'")
            for item in todos:
                if item.id == params.id:
                    item.done = True
                    _save_todos(path, todos)
                    return ToolResult.success_result(f"Marked done: #{item.id} {item.text}")
            return ToolResult.error_result(f"Task #{params.id} not found")

        elif action == "delete":
            if params.id is None:
                return ToolResult.error_result("'id' is required for action='delete'")
            before = len(todos)
            todos = [t for t in todos if t.id != params.id]
            if len(todos) == before:
                return ToolResult.error_result(f"Task #{params.id} not found")
            _save_todos(path, todos)
            return ToolResult.success_result(f"Deleted task #{params.id}")

        elif action == "list":
            if not todos:
                return ToolResult.success_result("(no tasks)")
            lines = []
            for item in todos:
                marker = "✓" if item.done else "○"
                lines.append(f"[{marker}] #{item.id}: {item.text}")
            pending = sum(1 for t in todos if not t.done)
            lines.append(f"\n{pending}/{len(todos)} pending")
            return ToolResult.success_result(
                "\n".join(lines),
                metadata={"total": len(todos), "pending": pending},
            )

        elif action == "clear":
            count = len(todos)
            _save_todos(path, [])
            return ToolResult.success_result(
                f"Cleared {count} task{'s' if count != 1 else ''}"
            )

        else:
            return ToolResult.error_result(
                f"Unknown action: {params.action!r}. "
                "Valid actions: add, done, delete, list, clear"
            )
