import asyncio
import flet as ft

HOME_ROUTE = "/"
STORE_ROUTE = "/store"
ORDERS_ROUTE = "/orders"

home_view = lambda page: ft.View(
    route=HOME_ROUTE,
    controls=[
        ft.AppBar(title=ft.Text("Home"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
        ft.Button("Visit Store", on_click=lambda e: asyncio.create_task(page.push_route(STORE_ROUTE))),
        ft.Button("Check Orders", on_click=lambda e: asyncio.create_task(page.push_route(ORDERS_ROUTE))),
    ],
)

store_view = lambda page: ft.View(
    route=STORE_ROUTE,
    controls=[
        ft.AppBar(title=ft.Text("Store"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
        ft.Button("Go Home", on_click=lambda e: asyncio.create_task(page.push_route(HOME_ROUTE))),
    ],
)

orders_view = lambda page: ft.View(
    route=ORDERS_ROUTE,
    controls=[
        ft.AppBar(title=ft.Text("Orders"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
        ft.Button("Go Home", on_click=lambda e: asyncio.create_task(page.push_route(HOME_ROUTE))),
    ],
)


async def main(page: ft.Page):
    def route_change(e):
        routes_map = {
            HOME_ROUTE: home_view,
            STORE_ROUTE: store_view,
            ORDERS_ROUTE: orders_view
        }

        page.views.clear()  # flush prev view
        page.views.append(routes_map.get(e.route, home_view)(page))
        page.update()

    page.on_route_change = route_change
    page.views.append(home_view(page))
    page.update()
    

if __name__ == "__main__":
    ft.run(main)
