import flet as ft

def main(page: ft.Page):
    DEFAULT_GRAY = "#3B3B3B"
    bg_colors = {
        "Red":   "#FF0000",
        "Green": "#00FF00",
        "Blue":  "#0000FF",
    }
    
    square = ft.Container(
        width=45,
        height=45,
        bgcolor=DEFAULT_GRAY
    )

    def button_clicked(e):
        square.bgcolor = bg_colors.get(dropdown.value, DEFAULT_GRAY)
        page.update()

    output_text = ft.Text()
    submit_button = ft.Button("Submit", on_click=button_clicked)
    dropdown = ft.Dropdown(
        width=150,
        options=[
            ft.dropdown.Option(key="Red"),
            ft.dropdown.Option(key="Green"),
            ft.dropdown.Option(key="Blue"),
        ],
    )

    page.add(
        ft.Row([dropdown, square]), 
        submit_button, 
        output_text
    )

if __name__ == "__main__":
    ft.run(main)
