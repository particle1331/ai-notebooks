import flet as ft

def main(page: ft.Page):
    def route_change(e: ft.RouteChangeEvent):           # <1>
        page.add(ft.Text(f"New route: {e.route}"))

    page.on_route_change = route_change                 # <2>
    page.add(ft.Text(f"Initial route: {page.route}"))    

if __name__ == "__main__":
    ft.app(main)
