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
    def loop(handler: Callable):
        def wrapper(e):
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
                            on_click=lambda _: (                    
                                e.page.pop_dialog(),            
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
        return wrapper

    wrapped = loop(join_click)
    username = ft.TextField(label="Enter your name", on_submit=wrapped)

    return ft.AlertDialog(
        modal=True, # <1>
        title=ft.Text("Welcome!"),
        content=ft.Column([username], tight=True),
        actions=[ft.Button("Join", on_click=wrapped)], 
        actions_alignment=ft.MainAxisAlignment.END
    )


@dataclass
class Message:
    user: str
    text: str


@ft.control
class ChatMessage(ft.Row):
    def __init__(self, msg_obj: Message):
        super().__init__()
        self.msg_obj = msg_obj
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(self.get_initials(self.msg_obj.user)),
                color=ft.Colors.WHITE,
                bgcolor=self.get_avatar_color(self.msg_obj.user),
            ),
            ft.Column(
                tight=True,
                spacing=5,
                controls=[
                    ft.Text(self.msg_obj.user, weight=ft.FontWeight.BOLD),
                    ft.Text(self.msg_obj.text, selectable=True),
                ],
            ),
        ]

    def get_initials(self, username: str):
        if username:
            return username[:1].capitalize()
        else:
            return "?"

    def get_avatar_color(self, username: str):
        colors_lookup = [
            ft.Colors.AMBER,
            ft.Colors.BLUE,
            ft.Colors.BROWN,
            ft.Colors.CYAN,
            ft.Colors.GREEN,
            ft.Colors.INDIGO,
            ft.Colors.LIME,
            ft.Colors.ORANGE,
            ft.Colors.PINK,
            ft.Colors.PURPLE,
            ft.Colors.RED,
            ft.Colors.TEAL,
            ft.Colors.YELLOW,
        ]
        color_idx = hash(username) % len(colors_lookup)
        return colors_lookup[color_idx]


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
                        user="System", 
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

    def build_messages(msg_objs: list[Message]):
        controls = []
        for msg in msg_objs:
            if msg.user == "System":
                c = ft.Text(msg.text, italic=True, color=ft.Colors.GREY)
                controls.append(c)
            else:
                controls.append(ChatMessage(msg))
        return controls

    return ft.Column(
        controls=[
            ft.Column(controls=build_messages(history)),
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
