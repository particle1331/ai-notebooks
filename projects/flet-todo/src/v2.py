import flet as ft

class TodoApp(ft.Column):
    def __init__(self, width: int):
        super().__init__(width=width)
        self.new_task = ft.TextField(
            hint_text="What needs to be done?", 
            expand=True, 
            on_submit=self.add_clicked   # ENTER triggers on_submit
        )
        self.add_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD, 
            on_click=self.add_clicked
        )
        self.new_task_row = ft.Row(controls=[self.new_task, self.add_button])
        self.task_list = ft.Column()
        self.controls.extend([self.new_task_row, self.task_list])

    def add_clicked(self, e):
        self.task_list.controls.append(ft.Checkbox(label=self.new_task.value))
        self.new_task.value = ""    # blank = show hint text again
        self.update()


def main(page: ft.Page):
    todo = TodoApp(width=600)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(todo)


if __name__ == "__main__":
    ft.app(main)
