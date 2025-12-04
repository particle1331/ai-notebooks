import flet as ft

def main(page: ft.Page):
    def route_change(e):
        troute = ft.TemplateRoute(page.route)
        if troute.match("/books/:id"):
            page.add(ft.Text(f"Book ID: {troute.id}"))
        elif troute.match("/account/:account_id/orders/:order_id"):
            page.add(ft.Text(f"Account: {troute.account_id}. Order: {troute.order_id}"))
        else:
            page.add(ft.Text("Unknown route"))
    
    page.on_route_change = route_change
    page.add(ft.Text(f"Initial route: {page.route}"))


if __name__ == "__main__":
    ft.app(main)
