import flet as ft

def main(page: ft.Page):
    colored_square = ft.Container(
        width=45,
        height=45,
        bgcolor="#3B3B3B"
    )

    def button_clicked(e):
        output_text.value = f"Dropdown value is: {dropdown.value} {dropdown.selected_data}"
        colored_square.bgcolor = dropdown.selected_data
        page.update()

    output_text = ft.Text()
    submit_button = ft.ElevatedButton(text="Submit", on_click=button_clicked)

    dropdown = ft.Dropdown(
        width=150,
        options=[
            ft.dropdown.Option("Red",   data="#FF0000"),
            ft.dropdown.Option("Green", data="#00FF00"),
            ft.dropdown.Option("Blue",  data="#0000FF"),
        ],
    )

    # Attach a small helper property to the dropdown
    @property
    def selected_data(self):
        selected = next((opt for opt in self.options if opt.key == self.value), None)
        return selected.data if selected else None

    # Add the property dynamically
    dropdown.__class__.selected_data = selected_data

    page.add(
        ft.Row([dropdown, colored_square]), 
        submit_button, 
        output_text
    )

ft.app(main)
