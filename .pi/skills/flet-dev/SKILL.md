---
name: flet-dev
description: >
  Flet framework reference for v0.83+ (1.0 Beta track). Covers both imperative
  and declarative APIs, correct control names, event handling, state management,
  routing, dialogs, pubsub, and common gotchas. Load this skill when writing or
  reviewing any Flet application code to avoid outdated API usage.
---

# Flet Development Reference (v0.83+)

This project uses **Flet 0.83.0** (`flet[all]>=0.83.0`), which is on the
**1.0 Beta track** (post-v0.70 Alpha rewrite). The API differs significantly
from pre-0.70 Flet that most LLM training data covers. Always follow the
patterns in this document.

Flet project scaffold lives at `projects/flet-basics/` with `[tool.flet.app] path = "src"`.
Notebooks demonstrating Flet are in `notebooks/apps/01-flet.ipynb` through `04-flet.ipynb`.

---

## Key Breaking Changes from Pre-0.70 Flet

These are the mistakes models make most often. **Do not use the old patterns.**

| Old (pre-0.70) | New (0.70+/0.83) |
|---|---|
| `ft.app(target=main)` | `ft.run(main)` |
| `ft.ElevatedButton("text")` | `ft.Button("text")` — all button types unified; use `ft.Button`, `ft.FilledButton`, `ft.FilledTonalButton`, `ft.TextButton`, `ft.IconButton` |
| `page.dialog = dlg; page.open(dlg)` | `page.show_dialog(dlg)` |
| `page.close(dlg)` | `page.pop_dialog()` |
| `page.drawer = drawer` | `page.show_dialog(NavigationDrawer(...))` with `.position` |
| `ft.colors.BLUE` (lowercase module) | `ft.Colors.BLUE` (class with uppercase C) |
| `ft.icons.ADD` (lowercase module) | `ft.Icons.ADD` (class with uppercase I) |
| `page.client_storage` | `page.shared_preferences` |
| `page.set_clipboard(text)` | `page.clipboard.set_async(text)` |
| `page.get_clipboard()` | `page.clipboard.get_async()` |
| `FilePicker` as overlay control | `FilePicker` as service in `page.services`; use `await fp.pick_files_async()` |
| `Audio` as control | `Audio` as service (extension: `flet-audio`) |
| `on_scroll_interval` | `scroll_interval` |
| `time.sleep()` in handlers | `await asyncio.sleep()` — blocking calls freeze the UI |
| Sync control methods | Many control methods are now async (e.g., `await control.focus()`) |
| Event handlers require `e` param | Event handlers can omit `e`: `on_click=lambda: print("clicked")` |
| Manual `page.update()` after every change | Auto-update after event handler completion; `update()` only needed mid-handler |

---

## App Entry Points

### Imperative (simple apps)
```python
import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("Hello"))

ft.run(main)
```

### Imperative async
```python
import flet as ft

async def main(page: ft.Page):
    page.add(ft.Text("Hello"))

ft.run(main)
```

### Declarative (recommended for complex apps)
```python
import flet as ft

@ft.component
def App():
    count, set_count = ft.use_state(0)
    return ft.Row([
        ft.Text(f"{count}"),
        ft.Button("Add", on_click=lambda: set_count(count + 1)),
    ])

ft.run(lambda page: page.render(App))
```

### Declarative with explicit main
```python
def main(page: ft.Page):
    page.render(AppView)

ft.run(main)
```

### Bootstrap with shared state (multi-session)
```python
chatroom = ChatRoom()

def bootstrap(page: ft.Page):
    page.chat = chatroom
    page.render(AppView)

ft.run(bootstrap)
```

### ASGI export (production deployment)
```python
app = ft.app(main, export_asgi_app=True)
# Run: uvicorn src.asgi_app:app --workers 4
```

---

## Controls Reference (verified in v0.83)

### Text & Display
```python
ft.Text("value", size=60)
ft.Text("bold", weight=ft.FontWeight.BOLD)
ft.Text("gray", italic=True, color=ft.Colors.GREY)
ft.Text("select me", selectable=True)
ft.Icon(ft.Icons.CASINO, size=60)
ft.CircleAvatar(content=ft.Text("A"), color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE)
ft.ProgressBar(value)  # 0.0 to 1.0
ft.Divider(thickness=0.5, color=ft.Colors.GREY_600)
```

### Input
```python
ft.TextField(hint_text="...", width=300)
ft.TextField(label="Name", expand=True, on_submit=handler, autofocus=True)
ft.TextField(value=val, on_change=lambda e: set_val(e.control.value))
ft.TextField(ref=my_ref)  # declarative ref
ft.Checkbox(label="Done", on_change=handler)
ft.Dropdown(width=150, options=[ft.dropdown.Option(key="Red"), ...])
```

### Buttons
```python
ft.Button("Submit", on_click=handler)
ft.Button(content=ft.Icon(ft.Icons.SEND), on_click=handler)
ft.Button("Styled", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
ft.TextButton("Cancel", on_click=handler)
ft.IconButton(icon=ft.Icons.EDIT, on_click=handler)
ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=handler)
ft.FloatingActionButton(content=ft.Icon(ft.Icons.CASINO, size=60), on_click=handler, height=60, width=60)
```

### Layout
```python
ft.Row(controls=[...])
ft.Row([...], alignment=ft.MainAxisAlignment.END)
ft.Row([...], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

ft.Column(width=600, controls=[...])
ft.Column([...], tight=True, spacing=5)
ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[...])

ft.Container(child, alignment=ft.Alignment.CENTER, expand=True)
ft.Container(content=inner, border=ft.Border.all(1, ft.Colors.OUTLINE),
             border_radius=5, padding=10, expand=True)
ft.Container(width=45, height=45, bgcolor="#3B3B3B")

ft.ListView(height=250, spacing=10, auto_scroll=True)
ft.ListView(controls=[...], expand=True, spacing=10,
            auto_scroll=True, scroll=ft.ScrollMode.ALWAYS)
```

### Navigation
```python
ft.View(route="/store", controls=[...])
ft.AppBar(title=ft.Text("Home"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST)
ft.Tabs(selected_index=0, length=3, on_change=handler,
        content=ft.TabBar(scrollable=False, tabs=[ft.Tab(label="all"), ...]))
```

### Dialogs
```python
page.show_dialog(
    ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirm"),
        content=ft.Text("Are you sure?"),
        actions=[
            ft.Button("Yes", on_click=yes_handler),
            ft.TextButton("No", on_click=lambda e: page.pop_dialog()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=dismiss_handler,
    )
)
# To close: page.pop_dialog()
```

---

## State Management

### Imperative: direct mutation + update()
```python
# After v0.70: auto-update runs after event handler completes.
# Explicit update() only needed for mid-handler UI refresh.
def button_click(e):
    label.value = "Updated"
    # page.update() — NOT needed at end of handler anymore
    # But IS needed if you want to show intermediate state:
    label.value = "Loading..."
    page.update()  # show "Loading..." immediately
    # ... do work ...
    label.value = "Done"
    # auto-update shows "Done" when handler returns

# List manipulation
page.controls[0].controls.append(new_item)
self.task_list.controls.remove(task)
```

### Imperative: control properties
```python
control.data      # internal program data (not displayed)
control.value     # UI-facing displayed value
control.visible   # show/hide (shifts layout)
control.disabled  # disable interaction (propagates to children)
```

### Imperative: isolated controls
```python
class Task(ft.Row):
    def is_isolated(self):
        return True  # self.update() won't trigger parent reconciliation
```

### Imperative: lifecycle methods
```python
def did_mount(self):       # after added to page
    self.page.run_task(self.background_work)

def will_unmount(self):    # before removal

def before_update(self):   # every update — DO NOT call update() here!
```

### Declarative: hooks
```python
@ft.component
def MyComponent():
    # State — persists across re-renders
    value, set_value = ft.use_state(initial)
    set_value(new_val)                          # replace
    set_value(lambda old: old + 1)              # updater function

    # Effect — side effects on mount/deps change
    def subscribe():
        # setup
        return cleanup_fn  # MUST return cleanup
    ft.use_effect(subscribe, [])  # [] = run once on mount

    # Ref — stable handle to a control across re-renders
    field_ref = ft.use_ref()
    ft.TextField(ref=field_ref)
    await field_ref.current.focus()  # .current gets latest instance

    return ft.Text(f"{value}")
```

### Declarative: observables
```python
from dataclasses import dataclass, field

@ft.observable
@dataclass
class AppState:
    counter: float = 0.0
    tasks: list = field(default_factory=list)

# Triggers re-render automatically:
state.counter += 0.1        # immutable types: works
state.tasks.append(item)    # Flet wraps list methods: works

# DOES NOT trigger re-render:
state.tasks += [item]       # augmented assignment on mutable: BROKEN
# Fix: use reassignment
state.tasks = state.tasks + [item]

# Manual notification for deep/nested changes:
state.notify()

# Subscribe to changes:
state.subscribe(lambda source, field: print(f"Changed: {field}"))
```

### Declarative: unique IDs
```python
TaskID = ft.IdCounter()

@dataclass
class Task:
    id: int = field(default_factory=TaskID)
```

### Declarative: page access inside components
```python
page = ft.context.page
page.show_dialog(...)
page.pop_dialog()
page.session.id
page.session.store.get("username")
page.session.store.set("username", name)
```

### Declarative: custom imperative controls in declarative apps
```python
@ft.control
class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        # ... build control tree
```

---

## Event Handling

```python
# Sync callback
def handler(e):
    e.control.value  # the control that fired the event

# Async callback (required for focus, sleep, etc.)
async def handler(e):
    await asyncio.sleep(1)
    await e.control.focus()

# Lambda (inline) — e param is optional in v0.70+
ft.Button("Go", on_click=lambda: do_something())
ft.Button("Go", on_click=lambda e: do_something(e))

# Common events:
# on_click      — buttons, containers
# on_change     — TextField (every keystroke), Checkbox (toggle), Tabs, Dropdown
# on_submit     — TextField (ENTER key)
# on_dismiss    — AlertDialog
```

---

## Routing

### Imperative
```python
page.on_route_change = route_change
await page.push_route("/store")

# Template routing for params
troute = ft.TemplateRoute(route)
if troute.match("/books/:id"):
    book_id = troute.id
```

### Declarative with observable
```python
@ft.observable
@dataclass
class AppState:
    route: str = "/"
    async def go(self, route: str):
        self.route = route
        await ft.context.page.push_route(route)

@ft.component
def Router(app: AppState):
    match app.route:
        case "/":       return HomePage(app)
        case "/about":  return AboutPage(app)
```

---

## PubSub (Multi-Session Messaging)

```python
page.pubsub.subscribe(on_message)       # on_message(msg_obj)
page.pubsub.unsubscribe(on_message)
page.pubsub.send_all(Message(user="alice", text="hello"))
```

---

## Session API

```python
page.session.id                          # unique session ID
page.session.store.get("username")       # get from store
page.session.store.set("username", val)  # set in store
```

---

## Async Patterns

```python
# Background tasks — must be async
self.page.run_task(self.update_timer)

# Run sync code on page's thread (for thread safety)
page.run_thread(lambda: set_history(lambda h: [*h, msg]))

# NEVER use time.sleep() — freezes UI
# ALWAYS use await asyncio.sleep()

# No async lambdas in Python — write named async functions
async def handle_click(e):
    await asyncio.sleep(1)
button.on_click = handle_click
```

---

## Common Gotchas

1. **`control.focus()` must be awaited** — `await field.focus()`
2. **No async lambdas** — must write named async functions for async handlers
3. **`time.sleep()` freezes UI** — use `await asyncio.sleep()` in async handlers
4. **`before_update()` must NOT call `update()`** — infinite loop
5. **Observable `+=` on lists/dicts does NOT trigger re-render** — use `state.items = state.items + [x]`
6. **Observable tracking is shallow** — nested changes need `.notify()`
7. **`visible=False` shifts layout** — siblings reposition
8. **`disabled`/`visible` propagate to all children recursively**
9. **`/admin` vs `/admin/` are different routes**
10. **UI updates are not thread-safe** — use `page.run_thread()` from background threads
11. **Session lifetime defaults to 3600s** — browser refresh may reattach within window
12. **Multi-worker deployments need external state** (Redis, DB) — sessions are worker-local
13. **`ft.Colors.GREY`** not `ft.colors.GREY` or `ft.Colors.GRAY` — case and spelling matter
14. **`autofocus=True`** only works on first render in declarative components
15. **When removing items from list during iteration, iterate over a copy**: `for item in items[:]`
16. **Declarative `set_state` is async** — yield control between rapid updates for intermediate renders
17. **`@ft.component` can return a single control OR a list of controls**
18. **`page.update()` is auto-called after event handlers** in v0.70+ — only call explicitly for mid-handler refresh

---

## CLI Commands

```bash
flet run app.py                  # run desktop app
flet run --web app.py            # run in browser
flet run --web --port 8000 app.py
flet run -d app.py               # hot reload
flet run -d -r app.py            # hot reload + watch subdirs
uv run flet create               # scaffold new project
```

---

## Project Structure

```
projects/flet-basics/
├── pyproject.toml      # [tool.flet.app] path = "src"
├── src/
│   └── main.py         # entry point
```

`pyproject.toml` must have `path = "src"` under `[tool.flet.app]` for `flet run` to find the app.
