import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("Hello ASGI!"))

app = ft.app(main, export_asgi_app=True)
