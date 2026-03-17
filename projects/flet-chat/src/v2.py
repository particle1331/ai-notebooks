import flet as ft
import threading

from typing import Callable, Optional
from dataclasses import dataclass, field


@dataclass
class ChatRoom:
    active_users: set[str] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add_user(self, name: str):
        with self._lock:
            self.validate_username(name)
            self.active_users.add(name)

    def remove_user(self, name: str):
        with self._lock:
            self.active_users.discard(name)

    def validate_username(self, name: str):
        if name in self.active_users:
            raise ValueError(f'"{name}" is already taken. Please choose another.')
        if not name.strip():
            raise ValueError("Username cannot be empty.")


def JoinDialog(join_click: Callable, chatroom: ChatRoom):
    def wrap_close(handler: Callable):
        def handle(e):
            entered = username.value.strip()
            try:
                chatroom.add_user(entered)

            except ValueError as error: # <3>
                e.page.pop_dialog()
                rejoin_dialog = JoinDialog(join_click, chatroom)
                error_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Invalid Username"),
                    content=ft.Text(str(error)),
                    actions=[
                        ft.Button(
                            "OK", 
                            on_click=lambda ev: (                    
                                ev.page.pop_dialog(),            
                                e.page.show_dialog(rejoin_dialog)
                            )
                        )
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                e.page.show_dialog(error_dialog)
                return
            
            e.page.pop_dialog()
            handler(e, entered)     # <2>
        return handle

    username = ft.TextField(label="Enter your name")

    return ft.AlertDialog(
        modal=True, # <1>
        title=ft.Text("Welcome!"),
        content=ft.Column([username], tight=True),
        actions=[ft.Button("Join", on_click=wrap_close(join_click))], 
        actions_alignment=ft.MainAxisAlignment.END
    )


@dataclass
class Message:
    user: str
    text: str


@ft.component
def AppView():
    page = ft.context.page
    username, set_username = ft.use_state("")
    history, set_history = ft.use_state([])
    message, set_message = ft.use_state("")

    def on_message(msg_obj: Message):
        page.run_thread(lambda: set_history(lambda h: [*h, msg_obj]))
        page.update()

    def join_and_subscribe():
        page.pubsub.subscribe(on_message)

        try:
            stored_username = page.session.store.get("username") or ""
            page.chat.add_user(stored_username)
            set_username(stored_username)
        except ValueError:
            def on_join(e, entered_name):
                set_username(entered_name)
                page.session.store.set("username", entered_name)
                page.pubsub.send_all(
                    Message(
                        user=entered_name, 
                        text=f"{entered_name} joined the chat!"
                    )
                )

            page.show_dialog(JoinDialog(on_join, page.chat))

        def cleanup():
            current_user = page.session.store.get("username") or ""
            page.chat.remove_user(current_user)
            page.pubsub.unsubscribe(on_message)

        return cleanup

    ft.use_effect(join_and_subscribe, [])

    def send_click(e):
        if message.strip() and username:
            page.pubsub.send_all(Message(user=username, text=message))
            set_message("")

    return ft.Column(
        controls=[
            ft.Column(controls=[ft.Text(f"{m.user}: {m.text}") for m in history]),
            ft.Row(controls=[
                ft.TextField(
                    label="New message",
                    value=message,
                    width=400,
                    on_change=lambda e: set_message(e.control.value),
                    on_submit=send_click
                ),
                ft.Button("Send", on_click=send_click)
            ]),
        ]
    )


if __name__ == "__main__":
    # shared state across sessions
    chatroom = ChatRoom()

    def bootstrap(page: ft.Page):
        page.chat = chatroom
        page.render(AppView)

    ft.run(bootstrap)
