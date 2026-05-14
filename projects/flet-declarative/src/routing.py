import flet as ft
import asyncio
from dataclasses import dataclass

@ft.observable
@dataclass
class AppState:
    route: str = "/"

    def go(self, route: str):
        self.route = route
        asyncio.create_task(ft.context.page.push_route(route))


@ft.component
def HomePage(app: AppState) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Text(f"Current route: {app.route}", size=24),
            ft.Button(
                "About",
                on_click=lambda e: app.go("/about"),
            ),
        ]
    )

@ft.component
def AboutPage(app: AppState) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Text(f"Current route: {app.route}", size=24),
            ft.Button(
                "🏠",
                on_click=lambda e: app.go("/"),
            ),
        ]
    )

@ft.component
def NotFoundPage(app: AppState) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Text(f"Current route: {app.route}", size=24),
            ft.Text("404 Not Found", size=24),
            ft.Button(
                "🏠",
                on_click=lambda e: app.go("/"),
            ),
        ]
    )


@ft.component
def AppRoot():
    app, _ = ft.use_state(AppState())
    ft.context.page.on_route_change = lambda e: app.go(e.route)
    return Router(app)

@ft.component
def Router(app: AppState) -> ft.Control:
    match app.route:
        case "/":
            return HomePage(app)
        case "/about":
            return AboutPage(app)
        case _:
            return NotFoundPage(app)


if __name__ == "__main__":
    ft.run(lambda page: page.render(AppRoot))
