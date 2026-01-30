import flet as ft

from copy import copy
from typing import Callable, Optional, Literal
from dataclasses import dataclass, field

TaskID = ft.IdCounter()


@dataclass
class Task(ft.Observable):
    name: str
    completed: bool = False
    id: int = field(default_factory=TaskID)
    
    def update(self, name: str):
        self.name = name

    def toggle_status(self):
        self.completed = not self.completed


@dataclass
class TodoAppState(ft.Observable):
    # NOTE: only re-assignment triggers observers in flet! => tuple
    tasks: tuple[Task] = field(default_factory=tuple)
    task_filters: list[str] = field(default_factory=lambda: ["all", "active", "completed"])
    selected_filter: int = 0

    def add_task(self, task: Task):
        self.tasks = self.tasks + (task,)
    
    def delete_task(self, task: Task):
        self.tasks = tuple([t for t in self.tasks if t is not task])

    def list_visible_tasks(self) -> list[Task]:
        tab = self.task_filters[self.selected_filter]
        is_visible = lambda t: (tab == "all") \
            or (tab == "completed" and t.completed) \
            or (tab == "active" and not t.completed)
        return [t for t in self.tasks if is_visible(t)]

    @property
    def active_tasks_number(self) -> int:
        return len([task for task in self.tasks if not task.completed])        


@ft.component
def TaskView(
    task: Task, 
    on_delete: Callable, 
    on_toggle_status: Callable
) -> ft.Row:
    
    is_editing, set_is_editing = ft.use_state(False)
    _name, set_name = ft.use_state(task.name)

    def start_edit():
        set_name(task.name)
        set_is_editing(True)

    def cancel_edit():
        set_is_editing(False)

    def save_edit():
        task.update(name=_name)
        set_is_editing(False)

    def toggle_status(e):
        task.toggle_status()
        on_toggle_status(task)

    def delete():
        on_delete(task)

    checkbox = ft.Checkbox(
        value=task.completed,
        label=task.name,
        disabled=is_editing,
        on_change=toggle_status
    )

    if not is_editing:
        return ft.Row(
            controls=[
                checkbox,
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    on_click=start_edit
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    on_click=delete
                )
            ]
        )

    else:
        return ft.Row(
            controls=[
                ft.TextField(
                    value=_name,
                    expand=True, 
                    on_change=lambda e: set_name(e.control.value),
                    on_submit=save_edit,
                    autofocus=True
                ),
                ft.IconButton(
                    icon=ft.Icons.SAVE,
                    on_click=save_edit
                ),
                ft.IconButton(
                    icon=ft.Icons.STOP,
                    on_click=cancel_edit
                )
            ]
        )

# NOTE: non-reactive => suffices to have this as a usual function that returns a control
# If it internally uses things like ft.use_state then it should be wrapped as @ft.component
def DialogModal(
    text: Optional[str] = "",
    decline_hook: Optional[Callable] = None,
    confirm_hook: Optional[Callable] = None,
):
    def wrap_close(hook):
        if hook is None:
            return lambda e: e.page.pop_dialog()
        return lambda e: (hook(e), e.page.pop_dialog())

    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirm delete"),
        content=ft.Text(text),
        actions=[
            ft.Button("No", on_click=wrap_close(decline_hook)),
            ft.Button("Yes", on_click=wrap_close(confirm_hook)),
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )


@ft.component
def TodoAppView() -> ft.Column:
    todo, _ = ft.use_state(TodoAppState())
    
    # -- delete one task
    def confirm_delete(task):
        dialog = DialogModal(
            text="Are you sure you want to delete this task?",
            confirm_hook=lambda e: todo.delete_task(task)
        )
        ft.context.page.show_dialog(dialog)

    # -- add new task
    new_task_name, set_new_task_name = ft.use_state("")
    new_task_field_ref = ft.use_ref()

    async def add_task():
        task = Task(name=new_task_name, completed=False)
        todo.add_task(task)
        set_new_task_name("")
        await new_task_field_ref.current.focus()  # refocus after adding task

    new_task_field = ft.Row(controls=[
        ft.TextField(
            ref=new_task_field_ref,
            hint_text="What needs to be done?",
            value=new_task_name,
            expand=True, 
            on_submit=add_task,
            on_change=lambda e: set_new_task_name(e.control.value),
            autofocus=True   # only works on first render
        ),
        ft.FloatingActionButton(
            icon=ft.Icons.ADD, 
            on_click=add_task
        )
    ])

    # -- status filter tabs
    filter_tabs = ft.Tabs(
        selected_index=todo.selected_filter,
        length=3,
        on_change=lambda e: setattr(todo, "selected_filter", e.control.selected_index),
        content=ft.TabBar(
            scrollable=False,
            tabs=[ft.Tab(label=tab) for tab in todo.task_filters],
        )
    )

    # -- footer
    def delete_completed():
        for task in todo.tasks[:]:
            if task.completed:
                todo.delete_task(task)

    def confirm_delete_completed():
        dialog = DialogModal(
            text="Are you sure you want to delete completed tasks?",
            confirm_hook=lambda e: delete_completed()
        )
        ft.context.page.show_dialog(dialog)

    # -- build ui
    return ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            Header(),
            new_task_field,
            filter_tabs,
            ft.ListView(
                controls=[
                    TaskView(
                        task=t, 
                        on_delete=confirm_delete, 
                        on_toggle_status=lambda e: todo.notify()
                    ) 
                    for t in todo.list_visible_tasks()
                ],
                height=250, 
                spacing=10, 
                scroll=ft.ScrollMode.ALWAYS,
                auto_scroll=True,
            ),
            ft.Divider(thickness=0.5, color=ft.Colors.GREY_600),
            Footer(todo.active_tasks_number, confirm_delete_completed)
        ],
    )

@ft.component
def Header():
    return ft.Text("Todo list 📝", size=50, weight=ft.FontWeight.BOLD)

@ft.component
def Footer(count_active_tasks: int, delete_completed_hook: Callable):
    clear_completed = ft.Button(
        "Clear Completed", 
        on_click=delete_completed_hook,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )
    return ft.Row(
        [
            ft.Text(f"{count_active_tasks} active tasks left.", color=ft.Colors.GREY_400),
            clear_completed
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )


def main(page: ft.Page):
    page.render(TodoAppView)


if __name__ == "__main__":
    ft.run(main)
