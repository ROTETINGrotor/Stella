import os
import queue
import threading

import flet as ft

import stella


def main(page: ft.Page):
    page.title = "Stella"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 8
    page.bgcolor = "#0b0f1a"

    # ডাটা ফাইল অ্যাপের নিজস্ব স্টোরেজে রাখা (অ্যান্ড্রয়েডে লেখার অনুমতি থাকে)
    store = os.getenv("FLET_APP_STORAGE_DATA") or os.getcwd()
    os.makedirs(store, exist_ok=True)
    stella.DATABASE_FILE = os.path.join(store, "stella_brain.json")
    stella.BACKUP_FILE = os.path.join(store, "stella_backup.json")

    out = ft.ListView(expand=True, auto_scroll=True, spacing=0)
    box = ft.TextField(
        hint_text="এখানে লিখুন...",
        expand=True,
        autofocus=True,
        border_radius=12,
    )
    answers = queue.Queue()
    state = {"waiting": False, "secret": False}

    def add_line(text, color=None):
        out.controls.append(
            ft.Text(text, size=14, color=color, selectable=True, font_family="monospace")
        )
        page.update()

    # ── স্ক্রিপ্টের print / input / getpass কে UI-তে বসানো ──
    def ui_print(*args, sep=" ", end="\n", **kwargs):
        add_line(sep.join(str(a) for a in args))

    def ui_input(prompt=""):
        if prompt:
            add_line(prompt, color="#7dd3fc")
        state["waiting"] = True
        state["secret"] = False
        return answers.get()

    def ui_secret(prompt=""):
        box.password = True
        box.can_reveal_password = True
        if prompt:
            add_line(prompt, color="#7dd3fc")
        state["waiting"] = True
        state["secret"] = True
        page.update()
        try:
            return answers.get()
        finally:
            box.password = False
            box.can_reveal_password = False
            page.update()

    def ui_clear():
        out.controls.clear()
        page.update()

    stella.print = ui_print
    stella.input = ui_input
    stella.ask_secret = ui_secret
    stella.clear_screen = ui_clear

    def submit(e):
        if not state["waiting"]:
            return
        value = box.value or ""
        box.value = ""
        state["waiting"] = False
        if not state["secret"]:
            add_line("› " + value, color="#a7f3d0")
        else:
            add_line("› ••••", color="#a7f3d0")
        box.focus()
        page.update()
        answers.put(value)

    box.on_submit = submit

    page.add(
        out,
        ft.Row([box, ft.IconButton(icon=ft.Icons.SEND, on_click=submit)]),
    )

    def worker():
        try:
            stella.run_stella()
        except Exception as ex:  # noqa: BLE001
            add_line(f"⚠️ ত্রুটি: {ex}", color="#fca5a5")
        add_line("— সেশন শেষ। অ্যাপটি বন্ধ করে আবার খুলুন —", color="#94a3b8")

    threading.Thread(target=worker, daemon=True).start()


ft.app(target=main)
