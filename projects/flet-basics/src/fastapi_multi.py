import flet as ft
import flet.fastapi as flet_fastapi


def root_main(page: ft.Page):
    page.add(ft.Text("This is root app!"))


def sub_main(page: ft.Page):
    page.add(ft.Text("This is sub app!"))


app = flet_fastapi.FastAPI()


app.mount("/sub-app", flet_fastapi.app(sub_main))
app.mount("/", flet_fastapi.app(root_main))
