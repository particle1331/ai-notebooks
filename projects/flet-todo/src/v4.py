import flet as ft
from typing import Callable

class Task(ft.Column):
    def __init__(self, text: str, status_hook: Callable, delete_hook: Callable):
        super().__init__()
        
        self.delete_hook = delete_hook
        self.checkbox = ft.Checkbox(label=text, on_change=status_hook)
        self.edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            on_click=self.edit_clicked
        )

        self.delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            on_click=self.delete_clicked
        )

        self.save_button = ft.IconButton(
            icon=ft.Icons.SAVE,
            on_click=self.save_clicked
        )

        self.display_view = ft.Row(controls=[
            self.checkbox, self.edit_button, self.delete_button
        ])

        self.edit_field = ft.TextField(
            value=self.checkbox.label, 
            expand=True, 
            on_submit=self.save_clicked
        )

        self.edit_view = ft.Row(
            controls=[
                self.edit_field,
                self.save_button,
            ], 
            visible=False
        )

        self.controls.extend([self.display_view, self.edit_view])

    def delete_clicked(self, e):
        """Remove this task from the todo list using external hook."""
        self.delete_hook(self)

    async def edit_clicked(self, e):
        self.display_view.visible = False
        self.edit_view.visible = True
        self.update()
        await self.edit_field.focus()

    def save_clicked(self, e):
        self.checkbox.label = self.edit_field.value
        self.display_view.visible = True
        self.edit_view.visible = False
        self.update()

    def is_isolated(self):
        return True


class TodoApp(ft.Column):
    TAB_ALL = "all"
    TAB_ACTIVE = "active"
    TAB_COMPLETED = "completed"
    
    def __init__(self, page: ft.Page, width: int):
        super().__init__(width=width)
        self._page = page
        
        self.new_task = ft.TextField(
            hint_text="What needs to be done?", 
            expand=True, 
            on_submit=self.add_clicked   # ENTER triggers on_submit
        )
        
        self.add_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD, 
            on_click=self.add_clicked
        )
        
        self.task_list = ft.ListView(height=250, spacing=10, auto_scroll=True)

        self.filter = ft.Tabs(
            selected_index=0,
            length=3,
            on_change=self.tabs_changed,
            content=ft.TabBar(
                scrollable=False,
                tabs=[
                    ft.Tab(label=TodoApp.TAB_ALL), 
                    ft.Tab(label=TodoApp.TAB_ACTIVE), 
                    ft.Tab(label=TodoApp.TAB_COMPLETED)
                ],
            )
        )

        self.active_count = ft.Text(
            "0 active tasks left.", 
            color=ft.Colors.GREY_400
        )

        self.clear_completed = ft.Button(
            "Clear Completed", 
            on_click=lambda e: self.confirm_clear_completed(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )

        self.controls.extend([
            ft.Row(controls=[self.new_task, self.add_button]), 
            self.filter,
            self.task_list,
            ft.Divider(thickness=0.5, color=ft.Colors.GREY_600),
            ft.Row(
                controls=[self.active_count, self.clear_completed], 
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        ])

    async def add_clicked(self, e):
        task = Task(
            self.new_task.value, 
            status_hook=self.on_status_change, 
            delete_hook=self.confirm_delete_task
        )
        self.task_list.controls.append(task)
        self.new_task.value = ""    # note: blank = show hint text again
        self.on_status_change()     # new task => reflect +1 to active count
        self.update()
        await self.new_task.focus()

    def is_isolated(self):
        return True
    
    def on_status_change(self):
        num_active = sum(1 for task in self.task_list.controls if not self.is_completed(task))
        self.active_count.value = f"{num_active} active tasks left."
        self.update()

    def confirm_delete_task(self, task):
        delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm delete"),
            content=ft.Text("Are you sure you want to delete this task?"),
            actions=[
                ft.Button(
                    "Yes", 
                    on_click=lambda e: (
                        self.delete_task(task), 
                        self.update(), 
                        self._page.pop_dialog()
                    )
                ),
                ft.TextButton(
                    "No", 
                    on_click=lambda e: self._page.pop_dialog()
                ),
            ],
            on_dismiss=lambda e: self.on_status_change(),
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(delete_dialog)
        self._page.update()
    
    def delete_task(self, task: Task):
        self.task_list.controls.remove(task)
        
    def confirm_clear_completed(self):
        delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm delete"),
            content=ft.Text("Are you sure you want to delete completed tasks?"),
            actions=[
                ft.Button(
                    "Yes", 
                    on_click=lambda e: (
                        self.delete_completed_tasks(),
                        self.update(), 
                        self._page.pop_dialog()
                    )
                ),
                ft.TextButton(
                    "No", 
                    on_click=lambda e: self._page.pop_dialog()
                ),
            ],
            on_dismiss=lambda e: self.on_status_change(),
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(delete_dialog)
        self._page.update()

    def delete_completed_tasks(self):
        for task in self.task_list.controls[:]:
            if self.is_completed(task):
                self.task_list.controls.remove(task)
    
    def tabs_changed(self, e):
        self.update()

    def is_completed(self, task: Task):
        return task.checkbox.value

    def before_update(self):
        visible_fn = {
            TodoApp.TAB_ALL: lambda task: True,
            TodoApp.TAB_ACTIVE: lambda task: not self.is_completed(task),
            TodoApp.TAB_COMPLETED: lambda task: self.is_completed(task),
        }
        selected_idx = self.filter.selected_index
        selected_tab = self.filter.content.tabs[selected_idx].label
        for task in self.task_list.controls:
            task.visible = visible_fn[selected_tab](task)

async def main(page: ft.Page):
    todo = TodoApp(page, width=600)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(ft.Text("Todo list 📝", size=50, weight=ft.FontWeight.BOLD), todo)
    await todo.new_task.focus()


if __name__ == "__main__":
    ft.run(main)


# show switching tabs print
# explain task list is same filtering only changes visibility
# status hook for checkbox change need to be called on TodoApp level to update filtering.
