import flet as ft

from typing import Callable, Optional
from dataclasses import dataclass, field

TaskID = ft.IdCounter()

@dataclass
class Task:
    name: str
    is_completed: bool = False
    id: int = field(default_factory=TaskID)


ALL = "all"
ACTIVE = "active"
COMPLETED = "completed"

@ft.observable
@dataclass
class TodoAppState:
    tasks: list[Task] = field(default_factory=list)
    task_filters: list[str] = field(default_factory=lambda: [ALL, ACTIVE, COMPLETED])
    selected_filter_idx: int = 0

    def add_task(self, task: Task):
        self.tasks.append(task)
    
    def delete_task(self, task: Task):
        self.tasks = [t for t in self.tasks if t.id != task.id]

    def update_task(self, task: Task, new_name: str):
        for idx, t in enumerate(self.tasks):
            if t.id == task.id:
                break
        self.tasks[idx] = Task(
            name=new_name, 
            is_completed=t.is_completed, 
            id=t.id
        )
    
    def toggle_task_status(self, task: Task):
        for idx, t in enumerate(self.tasks):
            if t.id == task.id:
                break
        self.tasks[idx] = Task(
            name=t.name, 
            is_completed=not t.is_completed, 
            id=t.id
        )

    def switch_filter(self, filter_idx: int):
        self.selected_filter_idx = filter_idx

    @property
    def visible_tasks(self) -> list[Task]:
        tab = self.task_filters[self.selected_filter_idx]
        is_visible = {
            ALL: lambda task: True,
            COMPLETED: lambda task: task.is_completed,
            ACTIVE: lambda task: not task.is_completed
        }
        return [t for t in self.tasks if is_visible[tab](t)]

    @property
    def active_tasks_number(self) -> int:
        return len([task for task in self.tasks if not task.is_completed])        


# NOTE: non-reactive => suffices to have this as usual fn that returns a control
# If it needs things like ft.use_state, then it should be wrapped as @ft.component 
# to support a reactive context.
def DialogModal(
    text: Optional[str] = "",
    decline_handler: Optional[Callable] = None,
    confirm_handler: Optional[Callable] = None,
):
    def wrap_close(handler: Optional[Callable]):
        if handler is None:
            return lambda e: e.page.pop_dialog()
        return lambda e: (handler(e), e.page.pop_dialog())

    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirm delete"),
        content=ft.Text(text),
        actions=[
            ft.Button("Yes", on_click=wrap_close(confirm_handler)),
            ft.TextButton("No", on_click=wrap_close(decline_handler)),
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )


@ft.component
def TaskView(app: TodoAppState, task: Task) -> ft.Row:

    is_editing, set_is_editing = ft.use_state(False)
    _name, set_name = ft.use_state(task.name)

    def start_edit():
        set_name(task.name)
        set_is_editing(True)

    def cancel_edit():
        set_is_editing(False)

    def save_edit():
        app.update_task(task, new_name=_name)
        set_is_editing(False)

    def confirm_delete():
        dialog = DialogModal(
            text="Are you sure you want to delete this task?",
            confirm_handler=lambda e: app.delete_task(task)
        )
        ft.context.page.show_dialog(dialog)

    if is_editing:
        return ft.Row([
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
        ])
    else:
        return ft.Row([
            ft.Checkbox(
                value=task.is_completed,
                label=task.name,
                on_change=lambda e: app.toggle_task_status(task)
            ), 
            ft.IconButton(
                icon=ft.Icons.EDIT, 
                on_click=start_edit
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE, 
                on_click=confirm_delete
            )
        ])


@ft.component
def TodoAppView() -> ft.Column:
    todo, _ = ft.use_state(TodoAppState())

    # add new task
    new_task_name, set_new_task_name = ft.use_state("")
    new_task_field_ref = ft.use_ref()

    async def add_task():
        task = Task(name=new_task_name, is_completed=False)
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

    # status filter tabs
    filter_tabs = ft.Tabs(
        selected_index=todo.selected_filter_idx,
        length=3,
        on_change=lambda e: todo.switch_filter(e.control.selected_index),
        content=ft.TabBar(
            scrollable=False,
            tabs=[ft.Tab(label=tab) for tab in todo.task_filters],
        )
    )

    # footer
    def delete_completed():
        for task in todo.tasks[:]:
            if task.is_completed:
                todo.delete_task(task)

    def confirm_delete_completed():
        dialog = DialogModal(
            text="Are you sure you want to delete completed tasks?",
            confirm_handler=lambda e: delete_completed()
        )
        ft.context.page.show_dialog(dialog)

    # build ui
    return ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            Header(),
            new_task_field,
            filter_tabs,
            ft.ListView(
                controls=[
                    TaskView(app=todo, task=t) 
                    for t in todo.visible_tasks
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
def Footer(count_active_tasks: int, delete_completed_handler: Callable):
    return ft.Row(
        [
            ft.Text(f"{count_active_tasks} active tasks left.", color=ft.Colors.GREY_400),
            ft.Button(
                "Clear Completed", 
                on_click=delete_completed_handler,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )


def main(page: ft.Page):
    page.render(TodoAppView)


if __name__ == "__main__":
    ft.run(main)
