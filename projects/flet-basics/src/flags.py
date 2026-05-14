import flet as ft

def main(page):
    def add_clicked(e):
        page.add(ft.Checkbox(label=new_task.value))
        new_task.value = ""
        new_task.update()

    new_task = ft.TextField(hint_text="What's needs to be done?", width=300)
    submit_button = ft.Button("Submit", on_click=add_clicked)
    
    new_task.disabled = True
    submit_button.disabled = True

    def make_visible_clicked(e):
        invisible_field.visible = True
        invisible_field.update()

    invisible_field = ft.TextField(hint_text="Invisible field", width=300)
    invisible_field.visible = False
    make_visible_button = ft.Button("Show", on_click=make_visible_clicked)
    
    page.add(ft.Row([new_task, submit_button]))
    page.add(ft.Column([invisible_field, make_visible_button]))


if __name__ == "__main__":
    ft.run(main)
