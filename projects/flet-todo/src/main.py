import flet as ft

def main(page: ft.Page):
    def add_clicked(e):
        task_list.controls.append(ft.Checkbox(label=new_task.value))
        new_task.value = ""
        full_col.update()

    new_task = ft.TextField(
        hint_text="What's needs to be done?", 
        expand=True, 
        on_submit=add_clicked   # ENTER triggers on_submit
    )
    add_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, 
        on_click=add_clicked
    )
    
    new_task_row = ft.Row(controls=[new_task, add_button])
    task_list = ft.Column()
    full_col = ft.Column(width=600, controls=[new_task_row, task_list])
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(full_col)

ft.app(main)
