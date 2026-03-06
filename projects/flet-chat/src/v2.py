import flet as ft
from dataclasses import dataclass
from typing import Optional, Callable


def JoinDialog(join_click: Callable):
    def wrap_close(handler: Callable):
        # Pass both the event AND the username to the handler
        return lambda e: (handler(e, user_name.value), e.page.pop_dialog())

    user_name = ft.TextField(label="Enter your name")

    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Welcome!"),
        content=ft.Column([user_name], tight=True),
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
    session_id = page.session.id
    username, set_username = ft.use_state("")  # Will be populated from session store
    history, set_history = ft.use_state([]) 
    message, set_message = ft.use_state("")
    
    def on_message(msg: Message):
        def update_ui():
            set_history(lambda current_history: [*current_history, msg])
            page.update()
        page.run_thread(update_ui)

    def subscribe_and_join():
        """Subscribe to messages and show join dialog if username not set."""
        page.pubsub.subscribe(on_message)
        
        stored_username = page.session.store.get("user_name")
        if stored_username:
            # sync session store and state
            set_username(stored_username)
        else:
            def on_join(e, entered_name):
                if entered_name.strip():
                    set_username(entered_name)
                    page.session.store.set("user_name", entered_name)  # Persist username
                    page.pubsub.send_all(Message(user=entered_name, text="joined the chat!"))
            
            page.show_dialog(JoinDialog(on_join))
        
        def cleanup(): 
            page.pubsub.unsubscribe(on_message)
        return cleanup

    # Single use_effect for both subscription and dialog
    ft.use_effect(subscribe_and_join, [])  

    def send_click(e):
        if message.strip() and username:
            page.pubsub.send_all(Message(user=username, text=message))
            set_message("")

    # Show a temporary message if user hasn't joined yet
    if not username:
        return ft.Column(controls=[
            ft.Text("Please join the chat using the dialog...")
        ])
    
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