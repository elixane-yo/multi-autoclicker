import pyautogui
import keyboard
import time
import threading

# ================== НАСТРОЙКИ ==================
# Список действий. Выполняются строго по очереди, сверху вниз, по кругу.
#
# Форматы записей:
#   ("click",  X, Y)                 — клик левой кнопкой
#   ("rclick", X, Y)                 — клик правой кнопкой
#   ("dclick", X, Y)                 — двойной клик
#   ("key",    "клавиша")            — нажатие клавиши
#   ("hotkey", "ctrl", "c")          — комбинация клавиш
#   ("text",   "привет")             — ввод текста
#   ("wait",   1.5)                  — пауза в секундах
#   ("scroll", X, Y, amount)         — прокрутка колесом (+вверх, -вниз)
#   ("scroll", X, Y, amount, dur)    — плавная прокрутка за dur секунд
#   ("hscroll", X, Y, amount)        — горизонтальный скролл
#   ("drag", x1, y1, x2, y2 [, dur]) — перетаскивание мышью
#
ACTIONS = [
    ("click", 448, 662),      # клик по первой точке
    ("click", 466, 489),         # нажать пробел
    ("click", 324, 1001),      # клик по второй точке
    ("click", 383, 997),
    ("key", "0"),  # Ctrl+C
    ("key", "."),        # напечатать "hello"
    ("key", "5"),     # правый клик
    ("scroll", 344, 784, -400),            # пауза 1 сек
    ("click", 344, 784),     # двойной клик
    ("wait", 4.0),
    ("click", 17, 72),
    ("click", 17, 72),
]

# Задержка между действиями (в секундах)
DELAY_BETWEEN_ACTIONS = 0.5

# Задержка перед стартом после нажатия клавиши старта
START_DELAY = 3.0

# Горячие клавиши управления
TOGGLE_KEY = "f6"   # старт / пауза
EXIT_KEY = "f7"     # выход
# ==============================================


running = False
should_exit = False


# ---------- Вспомогательные функции ----------

def scroll_at(x, y, amount, horizontal=False, duration=0.0):
    """Прокрутка колесом мыши в точке (x, y)."""
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
    """Перетаскивание: зажать кнопку в (x1,y1), отпустить в (x2,y2)."""
    pyautogui.moveTo(x1, y1)
    pyautogui.mouseDown(button=button)
    time.sleep(0.05)
    pyautogui.moveTo(x2, y2, duration=duration)
    time.sleep(0.05)
    pyautogui.mouseUp(button=button)


def perform_action(action):
    """Выполняет одно действие из списка."""
    kind = action[0]

    if kind == "click":
        pyautogui.click(action[1], action[2])
        return f"клик ({action[1]}, {action[2]})"

    elif kind == "rclick":
        pyautogui.rightClick(action[1], action[2])
        return f"правый клик ({action[1]}, {action[2]})"

    elif kind == "dclick":
        pyautogui.doubleClick(action[1], action[2])
        return f"двойной клик ({action[1]}, {action[2]})"

    elif kind == "key":
        keyboard.press_and_release(action[1])
        return f"клавиша [{action[1]}]"

    elif kind == "hotkey":
        keys = action[1:]
        keyboard.press_and_release("+".join(keys))
        return f"комбинация [{' + '.join(keys)}]"

    elif kind == "text":
        keyboard.write(action[1])
        return f"текст [{action[1]}]"

    elif kind == "scroll":
        x, y, amount = action[1], action[2], action[3]
        duration = action[4] if len(action) > 4 else 0.0
        scroll_at(x, y, amount, duration=duration)
        return f"скролл в ({x}, {y}) на {amount}"

    elif kind == "hscroll":
        x, y, amount = action[1], action[2], action[3]
        duration = action[4] if len(action) > 4 else 0.0
        scroll_at(x, y, amount, horizontal=True, duration=duration)
        return f"гориз. скролл в ({x}, {y}) на {amount}"

    elif kind == "drag":
        x1, y1, x2, y2 = action[1], action[2], action[3], action[4]
        duration = action[5] if len(action) > 5 else 0.5
        drag(x1, y1, x2, y2, duration=duration)
        return f"перетаскивание ({x1},{y1}) → ({x2},{y2})"

    return f"неизвестное действие: {action}"


def sleep_interruptible(seconds):
    """Спит, но прерывается при паузе или выходе."""
    waited = 0.0
    while waited < seconds and running and not should_exit:
        time.sleep(0.05)
        waited += 0.05


def clicker_loop():
    global running
    while not should_exit:
        if running:
            for action in ACTIONS:
                if not running or should_exit:
                    break

                if action[0] == "wait":
                    print(f"⏳ пауза {action[1]} сек")
                    sleep_interruptible(action[1])
                    continue

                desc = perform_action(action)
                print(f"✓ {desc}")
                sleep_interruptible(DELAY_BETWEEN_ACTIONS)
        else:
            time.sleep(0.1)


def toggle():
    global running
    running = not running
    print("▶ СТАРТ." if running else "⏸ ПАУЗА.")


def main():
    global should_exit
    print("=" * 55)
    print("МУЛЬТИАВТОКЛИКЕР + КЛАВИШИ + СКРОЛЛ")
    print(f"Действий в списке: {len(ACTIONS)}")
    print(f"Задержка между действиями: {DELAY_BETWEEN_ACTIONS} сек")
    print(f"[{TOGGLE_KEY.upper()}] — старт/пауза")
    print(f"[{EXIT_KEY.upper()}] — выход")
    print("=" * 55)
    print(f"После нажатия {TOGGLE_KEY.upper()} старт через {START_DELAY} сек...")

    t = threading.Thread(target=clicker_loop, daemon=True)
    t.start()

    keyboard.add_hotkey(TOGGLE_KEY, toggle)

    try:
        keyboard.wait(EXIT_KEY)
    except KeyboardInterrupt:
        pass

    should_exit = True
    time.sleep(0.2)
    print("Выход.")


if __name__ == "__main__":
    main()