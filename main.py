import os
import queue
import threading

import flet as ft


def _code_ok():
    """(ঠিক আছে?, কারণ) ফেরত দেয়। বিল্ডের সময় তৈরি _seal.py-র সাথে কোড মেলায়।"""
    import hashlib
    import sys

    base = os.path.dirname(os.path.abspath(__file__))
    if base not in sys.path:
        sys.path.insert(0, base)
    try:
        from _seal import SEAL
    except Exception as ex:
        try:
            files = ", ".join(sorted(os.listdir(base))[:15])
        except Exception:
            files = "?"
        return False, f"_seal পড়া যায়নি: {type(ex).__name__}: {ex}\nফোল্ডার: {base}\nফাইল: {files}"
    h = hashlib.sha256()
    for name in ("stella.py", "eternal.py"):
        try:
            with open(os.path.join(base, name), "rb") as f:
                h.update(hashlib.sha256(f.read().replace(b"\r\n", b"\n")).digest())
        except Exception as ex:
            return False, f"{name} পড়া যায়নি: {type(ex).__name__}: {ex}"
    got = h.hexdigest()
    if got != SEAL:
        return False, f"ফিঙ্গারপ্রিন্ট মেলেনি\nপাওয়া: {got[:12]}\nআশা: {SEAL[:12]}"
    return True, ""


def main(page: ft.Page):
    ok, why = _code_ok()
    if not ok:
        page.bgcolor = "#0b0f1a"
        page.padding = 16
        page.add(ft.Text(
            "🚫 অ্যাপের কোড পরিবর্তিত বা অসম্পূর্ণ। নিরাপত্তার কারণে চালু হবে না।\n\n"
            + why,
            color="#fca5a5", size=14, selectable=True))
        return
    import stella

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


if hasattr(ft, "run"):
    ft.run(main)
else:
    ft.app(target=main)