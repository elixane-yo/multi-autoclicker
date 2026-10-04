import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import random
import threading
import time
import pyautogui
import keyboard

pyautogui.FAILSAFE = False

PROFILES_FILE = "clicker_profiles.json"


def rand_offset(value, spread):
    if spread <= 0:
        return int(value)
    return int(value) + random.randint(-spread, spread)


def rand_delay(base, spread_pct):
    if spread_pct <= 0:
        return base
    delta = base * spread_pct / 100.0
    return max(0.0, base + random.uniform(-delta, delta))


def scroll_at(x, y, amount, horizontal=False, duration=0.0):
    pyautogui.moveTo(x, y)
    if duration > 0:
        steps = max(1, abs(int(amount)))
        per_step = amount / steps
        delay = duration / steps
        step_val = int(per_step) if abs(per_step) >= 1 else (1 if per_step > 0 else -1)
        for _ in range(steps):
            if horizontal:
                pyautogui.hscroll(step_val)
            else:
                pyautogui.scroll(step_val)
            time.sleep(delay)
    else:
        val = int(amount)
        if horizontal:
            pyautogui.hscroll(val)
        else:
            pyautogui.scroll(val)


def drag(x1, y1, x2, y2, duration=0.5, button="left"):
    pyautogui.moveTo(x1, y1)
    pyautogui.mouseDown(button=button)
    time.sleep(random.uniform(0.03, 0.12))
    pyautogui.moveTo(x2, y2, duration=duration)
    time.sleep(random.uniform(0.03, 0.12))
    pyautogui.mouseUp(button=button)


def human_click(x, y, kind="click"):
    approach_x = x + random.randint(-3, 3)
    approach_y = y + random.randint(-3, 3)
    pyautogui.moveTo(approach_x, approach_y, duration=random.uniform(0.05, 0.2))
    time.sleep(random.uniform(0.02, 0.08))
    pyautogui.moveTo(x, y, duration=random.uniform(0.02, 0.08))

    hold = random.uniform(0.03, 0.12)
    if kind == "click":
        pyautogui.mouseDown()
        time.sleep(hold)
        pyautogui.mouseUp()
    elif kind == "rclick":
        pyautogui.mouseDown(button="right")
        time.sleep(hold)
        pyautogui.mouseUp(button="right")
    elif kind == "dclick":
        pyautogui.mouseDown()
        time.sleep(hold)
        pyautogui.mouseUp()
        time.sleep(random.uniform(0.05, 0.15))
        pyautogui.mouseDown()
        time.sleep(hold)
        pyautogui.mouseUp()


def perform_action(action, anti):
    kind = action[0]
    spread = anti["coord_spread"] if anti["enabled"] else 0

    if kind == "click":
        x, y = rand_offset(action[1], spread), rand_offset(action[2], spread)
        human_click(x, y, "click")
        return f"клик ({x}, {y})"
    elif kind == "rclick":
        x, y = rand_offset(action[1], spread), rand_offset(action[2], spread)
        human_click(x, y, "rclick")
        return f"правый клик ({x}, {y})"
    elif kind == "dclick":
        x, y = rand_offset(action[1], spread), rand_offset(action[2], spread)
        human_click(x, y, "dclick")
        return f"двойной клик ({x}, {y})"
    elif kind == "key":
        keyboard.press_and_release(action[1])
        return f"клавиша [{action[1]}]"
    elif kind == "hotkey":
        keys = action[1:]
        keyboard.press_and_release("+".join(keys))
        return f"комбинация [{' + '.join(keys)}]"
    elif kind == "text":
        delay_per_char = random.uniform(0.03, 0.09) if anti["enabled"] else 0.01
        keyboard.write(action[1], delay=delay_per_char)
        return f"текст [{action[1]}]"
    elif kind == "scroll":
        x, y = rand_offset(action[1], spread), rand_offset(action[2], spread)
        amount = action[3]
        if anti["enabled"] and abs(amount) > 2:
            amount = amount + random.randint(-1, 1)
        duration = action[4] if len(action) > 4 else 0.0
        scroll_at(x, y, amount, duration=duration)
        return f"скролл в ({x}, {y}) на {amount}"
    elif kind == "hscroll":
        x, y = rand_offset(action[1], spread), rand_offset(action[2], spread)
        amount = action[3]
        duration = action[4] if len(action) > 4 else 0.0
        scroll_at(x, y, amount, horizontal=True, duration=duration)
        return f"гориз. скролл в ({x}, {y}) на {amount}"
    elif kind == "drag":
        x1, y1 = rand_offset(action[1], spread), rand_offset(action[2], spread)
        x2, y2 = rand_offset(action[3], spread), rand_offset(action[4], spread)
        duration = action[5] if len(action) > 5 else 0.5
        drag(x1, y1, x2, y2, duration=duration)
        return f"перетаскивание ({x1},{y1}) → ({x2},{y2})"
    return f"неизвестное действие: {action}"


def action_to_string(action):
    kind = action[0]
    if kind == "click":
        return f"🖱 Клик ({action[1]}, {action[2]})"
    if kind == "rclick":
        return f"🖱 Правый клик ({action[1]}, {action[2]})"
    if kind == "dclick":
        return f"🖱 Двойной клик ({action[1]}, {action[2]})"
    if kind == "key":
        return f"⌨ Клавиша [{action[1]}]"
    if kind == "hotkey":
        return f"⌨ Комбинация [{' + '.join(action[1:])}]"
    if kind == "text":
        return f"📝 Текст [{action[1]}]"
    if kind == "wait":
        return f"⏳ Пауза {action[1]} сек"
    if kind == "scroll":
        extra = f" за {action[4]} сек" if len(action) > 4 else ""
        return f"🖲 Скролл ({action[1]}, {action[2]}) на {action[3]}{extra}"
    if kind == "hscroll":
        extra = f" за {action[4]} сек" if len(action) > 4 else ""
        return f"🖲 Гориз. скролл ({action[1]}, {action[2]}) на {action[3]}{extra}"
    if kind == "drag":
        extra = f" за {action[5]} сек" if len(action) > 5 else ""
        return f"↔ Перетаскивание ({action[1]},{action[2]}) → ({action[3]},{action[4]}){extra}"
    return str(action)


class ProfileStore:
    def __init__(self, path=PROFILES_FILE):
        self.path = path
        self.profiles = {}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
            except Exception:
                self.profiles = {}
        if not self.profiles:
            self.profiles = {"Default": self._empty_profile()}

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Не удалось сохранить профили:", e)

    @staticmethod
    def _empty_profile():
        return {
            "actions": [],
            "delay": "0.5",
            "start_delay": "3",
            "loop": True,
            "max_cycles": 0,
            "stop_key": "f7",
            "anti_enabled": True,
            "coord_spread": 3,
            "delay_spread": 20,
        }

    def get(self, name):
        return self.profiles.get(name, self._empty_profile())

    def set(self, name, data):
        self.profiles[name] = data
        self.save()

    def delete(self, name):
        if name in self.profiles:
            del self.profiles[name]
            self.save()

    def names(self):
        return list(self.profiles.keys())


class ClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Мультиавтокликер")
        self.root.geometry("900x700")
        self.root.iconbitmap(r"C:\Users\elixane\Downloads\asss\ico.ico")

        self.actions = []
        self.running = False
        self.should_exit = False
        self.worker = None

        self.store = ProfileStore()
        self.current_profile = self.store.names()[0]

        self._build_ui()
        self._load_profile_into_ui(self.current_profile)

    def _build_ui(self):
        preset_bar = ttk.LabelFrame(self.root, text="Пресеты")
        preset_bar.pack(fill="x", padx=8, pady=4)

        ttk.Label(preset_bar, text="Профиль:").pack(side="left", padx=4)
        self.profile_var = tk.StringVar(value=self.current_profile)
        self.profile_combo = ttk.Combobox(
            preset_bar, textvariable=self.profile_var,
            values=self.store.names(), width=22, state="readonly"
        )
        self.profile_combo.pack(side="left", padx=4)
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_switch)

        ttk.Button(preset_bar, text="💾 Сохранить", command=self.save_profile).pack(side="left", padx=4)
        ttk.Button(preset_bar, text="➕ Новый", command=self.new_profile).pack(side="left", padx=4)
        ttk.Button(preset_bar, text="📋 Дублировать", command=self.duplicate_profile).pack(side="left", padx=4)
        ttk.Button(preset_bar, text="🗑 Удалить", command=self.delete_profile).pack(side="left", padx=4)
        ttk.Button(preset_bar, text="📤 Экспорт", command=self.export_profile).pack(side="left", padx=4)
        ttk.Button(preset_bar, text="📥 Импорт", command=self.import_profile).pack(side="left", padx=4)

        top = ttk.LabelFrame(self.root, text="Добавить действие")
        top.pack(fill="x", padx=8, pady=4)

        ttk.Button(top, text="🖱 Клик", width=12,
                   command=lambda: self.open_add_click("click")).grid(row=0, column=0, padx=3, pady=3)
        ttk.Button(top, text="🖱 Правый клик", width=14,
                   command=lambda: self.open_add_click("rclick")).grid(row=0, column=1, padx=3, pady=3)
        ttk.Button(top, text="🖱 Двойной клик", width=14,
                   command=lambda: self.open_add_click("dclick")).grid(row=0, column=2, padx=3, pady=3)

        ttk.Button(top, text="⌨ Клавиша", width=12,
                   command=self.open_add_key).grid(row=1, column=0, padx=3, pady=3)
        ttk.Button(top, text="⌨ Комбинация", width=14,
                   command=self.open_add_hotkey).grid(row=1, column=1, padx=3, pady=3)
        ttk.Button(top, text="📝 Текст", width=14,
                   command=self.open_add_text).grid(row=1, column=2, padx=3, pady=3)

        ttk.Button(top, text="⏳ Пауза", width=12,
                   command=self.open_add_wait).grid(row=2, column=0, padx=3, pady=3)
        ttk.Button(top, text="🖲 Скролл", width=14,
                   command=self.open_add_scroll).grid(row=2, column=1, padx=3, pady=3)
        ttk.Button(top, text="↔ Перетаскивание", width=14,
                   command=self.open_add_drag).grid(row=2, column=2, padx=3, pady=3)

        mid = ttk.LabelFrame(self.root, text="Список действий")
        mid.pack(fill="both", expand=True, padx=8, pady=4)

        self.listbox = tk.Listbox(mid, font=("Consolas", 10), selectmode="extended")
        self.listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)

        sb = ttk.Scrollbar(mid, command=self.listbox.yview)
        sb.pack(side="left", fill="y", pady=4)
        self.listbox.config(yscrollcommand=sb.set)

        side = ttk.Frame(mid)
        side.pack(side="left", fill="y", padx=4, pady=4)
        ttk.Button(side, text="⬆ Вверх", width=12, command=self.move_up).pack(pady=2)
        ttk.Button(side, text="⬇ Вниз", width=12, command=self.move_down).pack(pady=2)
        ttk.Button(side, text="🗑 Удалить", width=12, command=self.delete_selected).pack(pady=2)
        ttk.Button(side, text="✏ Изменить", width=12, command=self.edit_selected).pack(pady=2)
        ttk.Button(side, text="🧹 Очистить", width=12, command=self.clear_all).pack(pady=2)

        settings_container = ttk.Frame(self.root)
        settings_container.pack(fill="x", padx=8, pady=4)

        gen = ttk.LabelFrame(settings_container, text="Основные")
        gen.pack(side="left", fill="both", expand=True, padx=(0, 4))

        ttk.Label(gen, text="Задержка между действиями (сек):").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.delay_var = tk.StringVar(value="0.5")
        ttk.Entry(gen, textvariable=self.delay_var, width=8).grid(row=0, column=1, sticky="w")

        ttk.Label(gen, text="Задержка перед стартом (сек):").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.start_delay_var = tk.StringVar(value="3")
        ttk.Entry(gen, textvariable=self.start_delay_var, width=8).grid(row=1, column=1, sticky="w")

        ttk.Label(gen, text="Стоп-клавиша:").grid(row=2, column=0, sticky="w", padx=4, pady=3)
        self.stop_key_var = tk.StringVar(value="f7")
        ttk.Entry(gen, textvariable=self.stop_key_var, width=8).grid(row=2, column=1, sticky="w")

        self.loop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(gen, text="Повторять по кругу", variable=self.loop_var,
                        command=self._on_loop_toggle).grid(row=3, column=0, columnspan=2, sticky="w", padx=4, pady=3)

        ttk.Label(gen, text="Макс. циклов (0 = без лимита):").grid(row=4, column=0, sticky="w", padx=4, pady=3)
        self.max_cycles_var = tk.StringVar(value="0")
        self.max_cycles_entry = ttk.Entry(gen, textvariable=self.max_cycles_var, width=8)
        self.max_cycles_entry.grid(row=4, column=1, sticky="w")

        anti = ttk.LabelFrame(settings_container, text="🎲 Антидетект")
        anti.pack(side="left", fill="both", expand=True, padx=(4, 0))

        self.anti_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(anti, text="Включить", variable=self.anti_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=4, pady=3)

        ttk.Label(anti, text="Разброс координат (± пикс):").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.coord_spread_var = tk.StringVar(value="3")
        ttk.Entry(anti, textvariable=self.coord_spread_var, width=8).grid(row=1, column=1, sticky="w")

        ttk.Label(anti, text="Разброс задержек (± %):").grid(row=2, column=0, sticky="w", padx=4, pady=3)
        self.delay_spread_var = tk.StringVar(value="20")
        ttk.Entry(anti, textvariable=self.delay_spread_var, width=8).grid(row=2, column=1, sticky="w")

        ttk.Label(anti, text="(клики с дрожанием, плавный ввод текста)", foreground="gray").grid(
            row=3, column=0, columnspan=2, sticky="w", padx=4, pady=3)

        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=8, pady=6)

        self.start_btn = ttk.Button(bottom, text="▶ СТАРТ", command=self.start_clicker)
        self.start_btn.pack(side="left", padx=2)
        self.stop_btn = ttk.Button(bottom, text="⏹ СТОП", command=self.stop_clicker, state="disabled")
        self.stop_btn.pack(side="left", padx=2)

        self.cycle_label_var = tk.StringVar(value="")
        ttk.Label(bottom, textvariable=self.cycle_label_var).pack(side="left", padx=20)

        self.status_var = tk.StringVar(value="Готово")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w").pack(
            fill="x", side="bottom")

    def _on_loop_toggle(self):
        state = "normal" if self.loop_var.get() else "disabled"
        self.max_cycles_entry.config(state=state)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for a in self.actions:
            self.listbox.insert(tk.END, action_to_string(a))

    def _get_selected_indices(self):
        return list(self.listbox.curselection())

    def move_up(self):
        for i in self._get_selected_indices():
            if i > 0:
                self.actions[i - 1], self.actions[i] = self.actions[i], self.actions[i - 1]
        self._refresh_list()

    def move_down(self):
        for i in reversed(self._get_selected_indices()):
            if i < len(self.actions) - 1:
                self.actions[i + 1], self.actions[i] = self.actions[i], self.actions[i + 1]
        self._refresh_list()

    def delete_selected(self):
        for i in reversed(self._get_selected_indices()):
            del self.actions[i]
        self._refresh_list()

    def clear_all(self):
        if messagebox.askyesno("Очистить", "Удалить все действия?"):
            self.actions.clear()
            self._refresh_list()

    def edit_selected(self):
        sel = self._get_selected_indices()
        if not sel:
            messagebox.showinfo("Инфо", "Выбери действие для редактирования")
            return
        idx = sel[0]
        action = self.actions[idx]
        new_action = self._open_dialog_for_kind(action[0], action)
        if new_action is not None:
            self.actions[idx] = new_action
            self._refresh_list()

    def _open_dialog_for_kind(self, kind, existing=None):
        if kind in ("click", "rclick", "dclick"):
            return self._dialog_click(kind, existing)
        if kind == "key":
            return self._dialog_key(existing)
        if kind == "hotkey":
            return self._dialog_hotkey(existing)
        if kind == "text":
            return self._dialog_text(existing)
        if kind == "wait":
            return self._dialog_wait(existing)
        if kind == "scroll":
            return self._dialog_scroll(existing, horizontal=False)
        if kind == "hscroll":
            return self._dialog_scroll(existing, horizontal=True)
        if kind == "drag":
            return self._dialog_drag(existing)
        return None

    def _capture_coordinates(self, callback):
        self.status_var.set("РЕЖИМ ЗАХВАТА: наведи мышь и нажми F8 (Esc — отмена)")

        def worker():
            while True:
                if keyboard.is_pressed("f8"):
                    x, y = pyautogui.position()
                    while keyboard.is_pressed("f8"):
                        time.sleep(0.05)
                    self.root.after(0, lambda: self._finish_capture(callback, x, y))
                    return
                if keyboard.is_pressed("esc"):
                    while keyboard.is_pressed("esc"):
                        time.sleep(0.05)
                    self.root.after(0, lambda: self._finish_capture(callback, None, None))
                    return
                time.sleep(0.03)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_capture(self, callback, x, y):
        if x is None:
            self.status_var.set("Захват отменён")
        else:
            self.status_var.set(f"Захвачено: ({x}, {y})")
            callback(x, y)

    def _dialog_click(self, kind, existing=None):
        dlg = tk.Toplevel(self.root)
        titles = {"click": "Клик", "rclick": "Правый клик", "dclick": "Двойной клик"}
        dlg.title(f"Добавить: {titles[kind]}")
        dlg.geometry("340x180")
        dlg.transient(self.root)
        dlg.grab_set()

        x_var = tk.StringVar(value=str(existing[1]) if existing else "")
        y_var = tk.StringVar(value=str(existing[2]) if existing else "")

        ttk.Label(dlg, text="X:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ttk.Entry(dlg, textvariable=x_var, width=12).grid(row=0, column=1, padx=8)
        ttk.Label(dlg, text="Y:").grid(row=0, column=2, padx=8, sticky="w")
        ttk.Entry(dlg, textvariable=y_var, width=12).grid(row=0, column=3, padx=8)

        result = {"ok": False}

        def capture():
            dlg.withdraw()

            def on_captured(x, y):
                x_var.set(str(x))
                y_var.set(str(y))
                dlg.deiconify()
            self.root.after(300, lambda: self._capture_coordinates(on_captured))

        def ok():
            try:
                x, y = int(x_var.get()), int(y_var.get())
            except ValueError:
                messagebox.showerror("Ошибка", "X и Y должны быть числами")
                return
            result["action"] = (kind, x, y)
            result["ok"] = True
            dlg.destroy()

        ttk.Button(dlg, text="🎯 Поймать точку (F8)", command=capture).grid(row=1, column=0, columnspan=4, pady=8)
        ttk.Button(dlg, text="OK", command=ok).grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(dlg, text="Отмена", command=dlg.destroy).grid(row=2, column=2, columnspan=2, pady=8)

        dlg.wait_window()
        return result.get("action") if result["ok"] else None

    def _dialog_key(self, existing=None):
        dlg = tk.Toplevel(self.root)
        dlg.title("Добавить: Клавиша")
        dlg.geometry("320x130")
        dlg.transient(self.root)
        dlg.grab_set()

        key_var = tk.StringVar(value=existing[1] if existing else "")
        ttk.Label(dlg, text="Клавиша (space, enter, a, f1...):").pack(pady=6)
        ttk.Entry(dlg, textvariable=key_var, width=20).pack()

        result = {"ok": False}

        def ok():
            if not key_var.get().strip():
                messagebox.showerror("Ошибка", "Введи клавишу")
                return
            result["action"] = ("key", key_var.get().strip())
            result["ok"] = True
            dlg.destroy()

        ttk.Button(dlg, text="OK", command=ok).pack(side="left", padx=30, pady=10)
        ttk.Button(dlg, text="Отмена", command=dlg.destroy).pack(side="right", padx=30, pady=10)
        dlg.wait_window()
        return result.get("action") if result["ok"] else None

    def _dialog_hotkey(self, existing=None):
        dlg = tk.Toplevel(self.root)
        dlg.title("Добавить: Комбинация клавиш")
        dlg.geometry("360x160")
        dlg.transient(self.root)
        dlg.grab_set()

        keys_str = " + ".join(existing[1:]) if existing else ""
        var = tk.StringVar(value=keys_str)
        ttk.Label(dlg, text="Клавиши через пробел (например: ctrl alt delete):").pack(pady=6)
        ttk.Entry(dlg, textvariable=var, width=30).pack()

        result = {"ok": False}

        def ok():
            parts = var.get().strip().split()
            if not parts:
                messagebox.showerror("Ошибка", "Введи клавиши")
                return
            result["action"] = ("hotkey", *parts)
            result["ok"] = True
            dlg.destroy()

        ttk.Button(dlg, text="OK", command=ok).pack(side="left", padx=30, pady=10)
        ttk.Button(dlg, text="Отмена", command=dlg.destroy).pack(side="right", padx=30, pady=10)
        dlg.wait_window()
        return result.get("action") if result["ok"] else None

    def _dialog_text(self, existing=None):
        dlg = tk.Toplevel(self.root)
        dlg.title("Добавить: Текст")
        dlg.geometry("360x160")
        dlg.transient(self.root)
        dlg.grab_set()

        var = tk.StringVar(value=existing[1] if existing else "")
        ttk.Label(dlg, text="Текст для ввода:").pack(pady=6)
        ttk.Entry(dlg, textvariable=var, width=35).pack()

        result = {"ok": False}

        def ok():
            result["action"] = ("text", var.get())
            result["ok"] = True
            dlg.destroy()

        ttk.Button(dlg, text="OK", command=ok).pack(side="left", padx=30, pady=10)
        ttk.Button(dlg, text="Отмена", command=dlg.destroy).pack(side="right", padx=30, pady=10)
        dlg.wait_window()
        return result.get("action") if result["ok"] else None

    def _dialog_wait(self, existing=None):
        dlg = tk.Toplevel(self.root)
        dlg.title("Добавить: Пауза")
        dlg.geometry("320x130")
        dlg.transient(self.root)
        dlg.grab_set()

        var = tk.StringVar(value=str(existing[1]) if existing else "1.0")
        ttk.Label(dlg, text="Секунды:").pack(pady=6)
        ttk.Entry(dlg, textvariable=var, width=15).pack()

        result = {"ok": False}

        def ok():
            try:
                sec = float(var.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Введи число")
                return
            result["action"] = ("wait", sec)
            result["ok"] = True
            dlg.destroy()

        ttk.Button(dlg, text="OK", command=ok).pack(side="left", padx=30, pady=10)
        ttk.Button(dlg, text="Отмена", command=dlg.destroy).pack(side="right", padx=30, pady=10)
        dlg.wait_window()
        return result.get("action") if result["ok"] else None

    def _dialog_scroll(self, existing=None, horizontal=False):
        dlg = tk.Toplevel(self.root)
        dlg.title("Добавить: " + ("Гориз. скролл" if horizontal else "Скролл"))
        dlg.geometry("380x230")
        dlg.transient(self.root)
        dlg.grab_set()

        x_var = tk.StringVar(value=str(existing[1]) if existing else "")
        y_var = tk.StringVar(value=str(existing[2]) if existing else "")
        amt_var = tk.StringVar(value=str(existing[3]) if existing else "-5")
        dur_var = tk.StringVar(value=str(existing[4]) if existing and len(existing) > 4 else "0")

        ttk.Label(dlg, text="X:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(dlg, textvariable=x_var, width=10).grid(row=0, column=1)
        ttk.Label(dlg, text="Y:").grid(row=0, column=2, padx=6, sticky="w")
        ttk.Entry(dlg, textvariable=y_var, width=10).grid(row=0, column=3)

        ttk.Label(dlg, text="Сколько (вверх +, вниз −):").grid(row=1, column=0, columnspan=2, padx=6, pady=6, sticky="w")
        ttk.Entry(dlg, textvariable=amt_var, width=10).grid(row=1, column=2)

        ttk.Label(dlg, text="Плавно за N сек (0 = мгновенно):").grid(row=2, column=0, columnspan=2, padx=6, pady=6, sticky="w")
        ttk.Entry(dlg, textvariable=dur_var, width=10).grid(row=2, column=2)

        result = {"ok": False}

        def capture():
            dlg.withdraw()

            def on_captured(x, y):
                x_var.set(str(x))
                y_var.set(str(y))
                dlg.deiconify()
            self.root.after(300, lambda: self._capture_coordinates(on_captured))

        def ok():
            try:
                x, y = int(x_var.get()), int(y_var.get())
                amount = int(amt_var.get())
                dur = float(dur_var.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Проверь числа")
                return
            kind = "hscroll" if horizontal else "scroll"
            result["action"] = (kind, x, y, amount, dur) if dur > 0 else (kind, x, y, amount)
            result["ok"] = True
            dlg.destroy()

        ttk.Button(dlg, text="🎯 Поймать точку (F8)", command=capture).grid(row=3, column=0, columnspan=4, pady=6)
        ttk.Button(dlg, text="OK", command=ok).grid(row=4, column=0, columnspan=2, pady=6)
        ttk.Button(dlg, text="Отмена", command=dlg.destroy).grid(row=4, column=2, columnspan=2, pady=6)

        dlg.wait_window()
        return result.get("action") if result["ok"] else None

    def _dialog_drag(self, existing=None):
        dlg = tk.Toplevel(self.root)
        dlg.title("Добавить: Перетаскивание")
        dlg.geometry("420x260")
        dlg.transient(self.root)
        dlg.grab_set()

        x1 = tk.StringVar(value=str(existing[1]) if existing else "")
        y1 = tk.StringVar(value=str(existing[2]) if existing else "")
        x2 = tk.StringVar(value=str(existing[3]) if existing else "")
        y2 = tk.StringVar(value=str(existing[4]) if existing else "")
        dur = tk.StringVar(value=str(existing[5]) if existing and len(existing) > 5 else "0.5")

        ttk.Label(dlg, text="Откуда X:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(dlg, textvariable=x1, width=10).grid(row=0, column=1)
        ttk.Label(dlg, text="Y:").grid(row=0, column=2, sticky="w")
        ttk.Entry(dlg, textvariable=y1, width=10).grid(row=0, column=3)

        ttk.Label(dlg, text="Куда X:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(dlg, textvariable=x2, width=10).grid(row=1, column=1)
        ttk.Label(dlg, text="Y:").grid(row=1, column=2, sticky="w")
        ttk.Entry(dlg, textvariable=y2, width=10).grid(row=1, column=3)

        ttk.Label(dlg, text="Длительность (сек):").grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=4)
        ttk.Entry(dlg, textvariable=dur, width=10).grid(row=2, column=2)

        result = {"ok": False}

        def capture_from():
            dlg.withdraw()

            def on_captured(x, y):
                x1.set(str(x))
                y1.set(str(y))
                dlg.deiconify()
            self.root.after(300, lambda: self._capture_coordinates(on_captured))

        def capture_to():
            dlg.withdraw()

            def on_captured(x, y):
                x2.set(str(x))
                y2.set(str(y))
                dlg.deiconify()
            self.root.after(300, lambda: self._capture_coordinates(on_captured))

        def ok():
            try:
                vals = (int(x1.get()), int(y1.get()), int(x2.get()), int(y2.get()), float(dur.get()))
            except ValueError:
                messagebox.showerror("Ошибка", "Проверь числа")
                return
            result["action"] = ("drag", *vals)
            result["ok"] = True
            dlg.destroy()

        ttk.Button(dlg, text="🎯 Поймать ОТКУДА", command=capture_from).grid(row=3, column=0, columnspan=2, pady=6)
        ttk.Button(dlg, text="🎯 Поймать КУДА", command=capture_to).grid(row=3, column=2, columnspan=2, pady=6)
        ttk.Button(dlg, text="OK", command=ok).grid(row=4, column=0, columnspan=2, pady=6)
        ttk.Button(dlg, text="Отмена", command=dlg.destroy).grid(row=4, column=2, columnspan=2, pady=6)

        dlg.wait_window()
        return result.get("action") if result["ok"] else None

    def open_add_click(self, kind):
        a = self._dialog_click(kind)
        if a:
            self.actions.append(a)
            self._refresh_list()

    def open_add_key(self):
        a = self._dialog_key()
        if a:
            self.actions.append(a)
            self._refresh_list()

    def open_add_hotkey(self):
        a = self._dialog_hotkey()
        if a:
            self.actions.append(a)
            self._refresh_list()

    def open_add_text(self):
        a = self._dialog_text()
        if a:
            self.actions.append(a)
            self._refresh_list()

    def open_add_wait(self):
        a = self._dialog_wait()
        if a:
            self.actions.append(a)
            self._refresh_list()

    def open_add_scroll(self):
        a = self._dialog_scroll()
        if a:
            self.actions.append(a)
            self._refresh_list()

    def open_add_drag(self):
        a = self._dialog_drag()
        if a:
            self.actions.append(a)
            self._refresh_list()

    def _collect_current_ui(self):
        return {
            "actions": [list(a) for a in self.actions],
            "delay": self.delay_var.get(),
            "start_delay": self.start_delay_var.get(),
            "loop": self.loop_var.get(),
            "max_cycles": self.max_cycles_var.get(),
            "stop_key": self.stop_key_var.get(),
            "anti_enabled": self.anti_enabled_var.get(),
            "coord_spread": self.coord_spread_var.get(),
            "delay_spread": self.delay_spread_var.get(),
        }

    def _load_profile_into_ui(self, name):
        p = self.store.get(name)
        self.actions = [tuple(a) for a in p.get("actions", [])]
        self.delay_var.set(p.get("delay", "0.5"))
        self.start_delay_var.set(p.get("start_delay", "3"))
        self.loop_var.set(p.get("loop", True))
        self.max_cycles_var.set(str(p.get("max_cycles", "0")))
        self.stop_key_var.set(p.get("stop_key", "f7"))
        self.anti_enabled_var.set(p.get("anti_enabled", True))
        self.coord_spread_var.set(str(p.get("coord_spread", "3")))
        self.delay_spread_var.set(str(p.get("delay_spread", "20")))
        self._refresh_list()
        self._on_loop_toggle()
        self.profile_var.set(name)
        self.current_profile = name
        self.profile_combo["values"] = self.store.names()
        self._set_status(f"Профиль: {name}")

    def on_profile_switch(self, _event=None):
        self.store.set(self.current_profile, self._collect_current_ui())
        new_name = self.profile_var.get()
        self._load_profile_into_ui(new_name)

    def save_profile(self):
        self.store.set(self.current_profile, self._collect_current_ui())
        self._set_status(f"💾 Профиль «{self.current_profile}» сохранён")

    def new_profile(self):
        name = simpledialog.askstring("Новый профиль", "Название профиля:")
        if not name:
            return
        if name in self.store.profiles:
            messagebox.showerror("Ошибка", "Профиль с таким именем уже есть")
            return
        self.store.set(self.current_profile, self._collect_current_ui())
        self.store.set(name, ProfileStore._empty_profile())
        self._load_profile_into_ui(name)

    def duplicate_profile(self):
        name = simpledialog.askstring("Дублировать", "Название копии:")
        if not name:
            return
        if name in self.store.profiles:
            messagebox.showerror("Ошибка", "Профиль с таким именем уже есть")
            return
        self.store.set(name, self._collect_current_ui())
        self._load_profile_into_ui(name)

    def delete_profile(self):
        if len(self.store.profiles) <= 1:
            messagebox.showinfo("Инфо", "Нельзя удалить последний профиль")
            return
        if not messagebox.askyesno("Удалить", f"Удалить профиль «{self.current_profile}»?"):
            return
        self.store.delete(self.current_profile)
        new_name = self.store.names()[0]
        self._load_profile_into_ui(new_name)

    def export_profile(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"{self.current_profile}.json"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._collect_current_ui(), f, ensure_ascii=False, indent=2)
            self._set_status(f"📤 Экспортировано: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def import_profile(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        name = os.path.splitext(os.path.basename(path))[0]
        base = name
        i = 1
        while name in self.store.profiles:
            i += 1
            name = f"{base}_{i}"
        self.store.set(name, data)
        self._load_profile_into_ui(name)
        self._set_status(f"📥 Импортирован профиль «{name}»")

    def start_clicker(self):
        if not self.actions:
            messagebox.showinfo("Инфо", "Сначала добавь действия")
            return

        try:
            delay = float(self.delay_var.get())
            start_delay = float(self.start_delay_var.get())
            max_cycles = int(self.max_cycles_var.get()) if self.loop_var.get() else 1
            coord_spread = int(self.coord_spread_var.get())
            delay_spread = int(self.delay_spread_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Проверь числовые поля")
            return

        anti = {
            "enabled": self.anti_enabled_var.get(),
            "coord_spread": max(0, coord_spread),
            "delay_spread": max(0, delay_spread),
        }

        self.running = True
        self.should_exit = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        try:
            keyboard.add_hotkey(self.stop_key_var.get().strip(), self.stop_clicker)
        except Exception:
            pass

        self.worker = threading.Thread(
            target=self._run_loop,
            args=(delay, start_delay, max_cycles, anti),
            daemon=True
        )
        self.worker.start()

    def _run_loop(self, delay, start_delay, max_cycles, anti):
        self._set_status(f"Старт через {start_delay} сек...")
        for _ in range(int(start_delay * 10)):
            if not self.running:
                return
            time.sleep(0.1)

        cycle = 0
        while self.running and not self.should_exit:
            cycle += 1
            if max_cycles > 0 and cycle > max_cycles:
                break
            self.root.after(0, lambda c=cycle: self.cycle_label_var.set(
                f"Цикл: {c}" + (f" / {max_cycles}" if max_cycles > 0 else "")))

            for action in list(self.actions):
                if not self.running or self.should_exit:
                    return
                try:
                    desc = perform_action(action, anti)
                    self._set_status(f"✓ [{cycle}] {desc}")
                except Exception as e:
                    self._set_status(f"⚠ Ошибка: {e}")

                d = rand_delay(delay, anti["delay_spread"]) if anti["enabled"] else delay
                self._sleep_interruptible(d)

            if not self.loop_var.get():
                break

        self.root.after(0, self._on_finished)
        self._set_status("✅ Завершено")

    def _sleep_interruptible(self, seconds):
        waited = 0.0
        while waited < seconds and self.running and not self.should_exit:
            time.sleep(0.05)
            waited += 0.05

    def stop_clicker(self):
        self.running = False
        self.should_exit = True
        self._set_status("⏹ Остановлено")
        self.root.after(0, self._on_finished)

    def _on_finished(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.cycle_label_var.set("")

    def _set_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))


if __name__ == "__main__":
    root = tk.Tk()
    app = ClickerApp(root)
    root.mainloop()