import flet as ft
import time

def main(page: ft.Page):
    page.add(
        ft.Row(controls=[
            ft.Text("A", size=60),
            ft.Text("B", size=60),
            ft.Text("C", size=60)
        ])
    )

    timer = ft.Text(size=30)
    page.add(timer)
    time.sleep(10)

    while True:
        timer.data = 3
        for _ in range(3):
            timer.value = f"Removing controls in {timer.data} seconds..."
            timer.data -= 1
            page.update()
            time.sleep(1)

        page.controls[0].controls.pop()
        page.update()
        
        if len(page.controls[0].controls) == 0:
            timer.value = "No more controls!"
            page.update()
            break


if __name__ == "__main__":
    ft.app(main)
