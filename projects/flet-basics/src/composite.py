import flet as ft

class Task(ft.Row):
    def __init__(self, text):
        super().__init__()
        self.text_view      = ft.Text(text)
        self.edit_button    = ft.IconButton(icon=ft.Icons.EDIT, on_click=self.edit)
        self.edit_view      = ft.TextField(text, visible=False)
        self.save_button    = ft.IconButton(visible=False, icon=ft.Icons.SAVE, on_click=self.save)
        self.controls = [
            ft.Checkbox(),
            self.text_view,
            self.edit_button,
            self.edit_view,
            self.save_button,
        ]

    def edit(self, e):
        self.text_view.visible      = False
        self.edit_button.visible    = False
        self.edit_view.visible      = True
        self.save_button.visible    = True
        self.update()

    def save(self, e):
        self.text_view.visible      = True
        self.edit_button.visible    = True
        self.edit_view.visible      = False
        self.save_button.visible    = False
        self.text_view.value        = self.edit_view.value
        self.update()

    def is_isolated(self):
        return True


def main(page: ft.Page):
    page.add(
        Task(text="Do laundry"),
        Task(text="Cook dinner"),
    )


if __name__ == "__main__":
    ft.app(main)
