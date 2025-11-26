import flet as ft

def main(page):
    def add_clicked(e):
        page.add(ft.Checkbox(label=new_task.value))
        new_task.value = ""
        new_task.focus()
        new_task.update()

    new_task = ft.TextField(hint_text="What's needs to be done?", width=300)
    submit_button = ft.ElevatedButton("Submit", on_click=add_clicked)
    
    submit_button.disabled = True
    new_task.disabled = True

    def make_visible_clicked(e):
        invisible_field.visible = True
        invisible_field.update()

    invisible_field = ft.TextField(hint_text="Invisible field", width=300)
    invisible_field.visible = False
    make_visible_button = ft.ElevatedButton("???", on_click=make_visible_clicked)
    
    page.add(ft.Row([new_task, submit_button]))
    page.add(ft.Row([invisible_field, make_visible_button]))


if __name__ == "__main__":
    ft.app(main)
