import flet as ft
import asyncio
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

@ft.component
def Greeting(text: str) -> ft.Container:
    return ft.Container(
        ft.Text(text, size=60),
        alignment=ft.Alignment.CENTER,
        expand=True
    )

@ft.component
def RollButton(on_click):
    return ft.Row(
        controls=[
            ft.FloatingActionButton(
                content=ft.Icon(ft.Icons.CASINO, size=60),
                on_click=on_click,
                height=60, width=60
            )
        ],
        alignment=ft.MainAxisAlignment.END
    )


@ft.component
def AppView() -> ft.Column:
    n = len(hello_world)
    greeting, set_greeting = ft.use_state(hello_world[0])
    
    async def roll_greeting(e):
        set_greeting("")
        await asyncio.sleep(0.2)
        set_greeting(hello_world[randint(0, n - 1)])
    
    return ft.Column(
        controls=[
            Greeting(text=greeting),
            RollButton(on_click=roll_greeting),
        ],
        alignment=ft.Alignment.CENTER,
        expand=True
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(AppView))
