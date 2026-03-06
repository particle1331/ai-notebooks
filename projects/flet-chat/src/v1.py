import flet as ft
from dataclasses import dataclass


@dataclass
class Message:
    user: str
    text: str


@ft.component
def AppView():
    page = ft.context.page
    session_id = page.session.id
    history, set_history = ft.use_state([]) 
    message, set_message = ft.use_state("")
    
    def on_message(msg: Message):
        def update_ui():
            set_history(lambda current_history: [*current_history, msg])
            page.update()   # force update
        page.run_thread(update_ui)

    # subscribe once. use_effect expects cleanup function
    def subscribe():
        page.pubsub.subscribe(on_message)
        def cleanup(): 
            page.pubsub.unsubscribe(on_message)
        return cleanup

    # empty deps => run once on mount, and cleanup on unmount
    ft.use_effect(subscribe, [])  

    def send_click(e):
        page.pubsub.send_all(Message(user=session_id, text=message))
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
    ft.run(lambda page: page.render(AppView))
