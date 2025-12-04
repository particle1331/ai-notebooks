import asyncio
import flet as ft

class Countdown(ft.Text):
    def __init__(self, seconds):
        super().__init__()
        self.seconds = seconds

    def did_mount(self):
        self.running = True
        self.page.run_task(self.update_timer)

    def will_unmount(self):
        self.running = False 

    async def update_timer(self):
        while self.running:
            mins, secs = divmod(self.seconds, 60)
            self.value = "{:02d}:{:02d}".format(mins, secs)
            self.value += " 🛑" * int(self.seconds == 0)
            self.update()

            if self.seconds == 0:
                self.running = False
            else:
                await asyncio.sleep(1)
                self.seconds -= 1
            

def main(page: ft.Page):
    page.add(Countdown(10), Countdown(5))


if __name__ == "__main__":
    ft.app(main)
