import flet as ft

def main(page):
    def add_clicked(e):
        page.add(ft.Checkbox(label=new_task.value))
        new_task.value = ""
        new_task.focus()
        new_task.update()

    new_task = ft.TextField(hint_text="What's needs to be done?", width=300)
    submit_button = ft.ElevatedButton("Submit", on_click=add_clicked)
    page.add(ft.Row([new_task, submit_button]))


if __name__ == "__main__":
    ft.run(main)
