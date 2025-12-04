import datetime
import asyncio
import flet as ft

async def main(page: ft.Page):
    async def async_button(e):
        timestamp = datetime.datetime.now()
        await asyncio.sleep(3)
        page.add(ft.Text(f"Button clicked at {timestamp}"))
        page.update()

    page.add(ft.ElevatedButton("async", on_click=async_button))
    page.update()


if __name__ == "__main__":
    ft.app(main)
