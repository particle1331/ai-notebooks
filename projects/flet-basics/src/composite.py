import flet as ft

class Task(ft.Row):
    def __init__(self, text):
        super().__init__()
        self.text_view = ft.Text(text)
        self.edit_icon = ft.IconButton(icon=ft.Icons.EDIT, on_click=self.edit)
        self.text_edit = ft.TextField(text, visible=False)
        self.save_icon = ft.IconButton(visible=False, icon=ft.Icons.SAVE, on_click=self.save)
        self.controls = [
            ft.Checkbox(),
            self.text_view, 
            self.edit_icon,
            self.text_edit, 
            self.save_icon,
        ]

    def edit(self, e):
        self.text_view.visible = False
        self.edit_icon.visible = False
        self.text_edit.visible = True
        self.save_icon.visible = True
        self.update()

    def save(self, e):
        self.text_view.visible = True
        self.edit_icon.visible = True
        self.text_edit.visible = False
        self.save_icon.visible = False
        self.text_view.value   = self.text_edit.value
        self.update()

    def is_isolated(self):
        return True


def main(page: ft.Page):
    page.add(
        Task(text="Do laundry"),
        Task(text="Cook dinner"),
    )


if __name__ == "__main__":
    ft.run(main)
