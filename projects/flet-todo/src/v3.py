import flet as ft
from typing import Callable

class TaskItem(ft.Column):
    def __init__(self, text: str, delete_hook: Callable):
        super().__init__()
        self.delete_hook = delete_hook
        self.checkbox = ft.Checkbox(label=text)
        
        # icons
        self.edit_icon = ft.IconButton(icon=ft.Icons.EDIT, on_click=self.edit_clicked)
        self.save_icon = ft.IconButton(icon=ft.Icons.SAVE, on_click=self.save_clicked)
        self.delete_icon = ft.IconButton(icon=ft.Icons.DELETE, on_click=self.delete_clicked)

        # views
        self.text_view = ft.Row([self.checkbox, self.edit_icon, self.delete_icon])
        self.text_edit = ft.TextField(self.checkbox.label, expand=True, on_submit=self.save_clicked)
        self.edit_view = ft.Row([self.text_edit, self.save_icon], visible=False)

        self.controls.extend([self.text_view, self.edit_view])

    def delete_clicked(self, e):
        """Remove this task from the todo list using external hook."""
        self.delete_hook(self)

    def edit_clicked(self, e):
        self.text_view.visible = False
        self.edit_view.visible = True
        self.update()

    def save_clicked(self, e):
        self.checkbox.label = self.text_edit.value
        self.text_view.visible = True
        self.edit_view.visible = False
        self.update()

    def is_isolated(self):
        return True


class TodoApp(ft.Column):
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
        self.task_list = ft.Column()
        self.controls.extend([
            ft.Row(controls=[self.new_task, self.add_button]), 
            self.task_list
        ])

    def add_clicked(self, e):
        task = TaskItem(self.new_task.value, delete_hook=self.delete_task)
        self.task_list.controls.append(task)
        self.new_task.value = ""    # blank = show hint text again
        self.update()

    def is_isolated(self):
        return True
    
    def delete_task(self, task: TaskItem):
        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm delete"),
            content=ft.Text("Are you sure you want to delete this task?"),
            actions=[
                ft.Button(
                    "Yes", 
                    on_click=lambda e: (
                        self.task_list.controls.remove(task), 
                        self.update(), 
                        self._page.pop_dialog()
                    )
                ),
                ft.TextButton(
                    "No", 
                    on_click=lambda e: self._page.pop_dialog()
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dlg_modal)
        self._page.update()
        

def main(page: ft.Page):
    todo = TodoApp(page, width=600)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(ft.Text("Todo list 📝", size=50, weight=ft.FontWeight.BOLD), todo)

if __name__ == "__main__":
    ft.run(main)
