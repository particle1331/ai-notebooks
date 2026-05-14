import flet as ft
import time
from random import randint


hello_world = [
    "Hello, world!",
    "¡Hola, mundo!",
    "Bonjour, monde !",
    "Hallo, Welt!",
    "Ciao, mondo!",
    "Olá, mundo!",
    "こんにちは、世界！",
    "안녕하세요, 세계!",
    "你好，世界！",
    "مرحباً، يا عالم!",
]


def main(page: ft.Page):
    default = hello_world[0]
    greeting = ft.Text(default, size=60, data=default)
    n = len(hello_world)
    
    def roll_greeting(e):
        # Force update rolling animation
        greeting.value = ""
        page.update()
        time.sleep(0.2)
        
        # Force update final result
        greeting.data = hello_world[randint(0, n - 1)]
        greeting.value = str(greeting.data)
        page.update()


    page.floating_action_button = ft.FloatingActionButton(
        content=ft.Icon(ft.Icons.CASINO, size=60),
        on_click=roll_greeting,
        height=60, width=60
    )

    page.add(
        ft.Container(
            greeting,
            alignment=ft.Alignment.CENTER,
            expand=True
        )
    )


if __name__ == "__main__":
    ft.run(main)
