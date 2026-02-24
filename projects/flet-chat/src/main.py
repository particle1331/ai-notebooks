from dataclasses import dataclass, field
import flet as ft


@dataclass
class Message:
    user: str
    text: str


@ft.observable
@dataclass
class AppState:
    messages: list[Message] = field(default_factory=list)

    def add_message(self, message: Message):
        self.messages.append(message)


@ft.component
def AppView():
    app, _ = ft.use_state(AppState())
    new_text, set_new_text = ft.use_state("")

    def subscribe():
        ft.context.page.pubsub.subscribe(app.add_message)

        def cleanup():
            ft.context.page.pubsub.unsubscribe(app.add_message)

        return cleanup

    ft.use_effect(subscribe, [])

    def send_click(e):
        if not new_text.strip():
            return

        m = Message(user=ft.context.page.session.id, text=new_text)
        ft.context.page.pubsub.send_all(m)
        set_new_text("")

    return ft.Column(
        controls=[
            ft.Column(
                controls=[
                    ft.Text(f"{m.user}: {m.text}")
                    for m in app.messages
                ],
                expand=True,
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        value=new_text,
                        on_change=lambda e: set_new_text(e.control.value),
                        expand=True,
                    ),
                    ft.Button("Send", on_click=send_click),
                ]
            ),
        ],
        expand=True,
    )


ft.run(lambda page: page.render(AppView))
