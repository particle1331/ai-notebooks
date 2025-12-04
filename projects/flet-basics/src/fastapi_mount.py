from contextlib import asynccontextmanager

import flet as ft
import flet.fastapi as flet_fastapi
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    flet_fastapi.app_manager.start()
    yield
    flet_fastapi.app_manager.shutdown()

async def ui(page: ft.Page):
    page.add(ft.Text("Hello, Flet!"))


app = FastAPI(lifespan=lifespan)
app.mount("/flet-app", flet_fastapi.app(ui))
