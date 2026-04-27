"""
Урок 02 — ручной неблокирующий вариант (без класса Worker).

Запуск: python test/02_manual_async.py

Что здесь изучаем:
1. Тяжелая работа уходит в фоновый поток (threading.Thread).
2. Поток НЕ трогает Tkinter-виджеты.
3. Поток кладет результат в queue.Queue.
4. UI-поток периодически проверяет очередь через root.after(...).

Это тот же фундамент, на котором построен workers/db_worker.py,
только пока без упаковки в класс.
"""

import queue
import threading
import time
import tkinter as tk


# Очередь обмена: фон -> UI
result_queue = queue.Queue()


def fake_db_query():
    """Имитация долгого запроса к БД."""
    time.sleep(3)
    return ["Книга 1", "Книга 2", "Книга 3"]


def db_task():
    """Фоновая задача: выполняется НЕ в UI-потоке."""
    try:
        books = fake_db_query()
        result_queue.put(("done", books))
    except Exception as exc:
        result_queue.put(("error", exc))


def on_load_click():
    status_label.config(text="Загружаю... (thread)")
    load_btn.config(state="disabled")

    # Стартуем фоновый поток для тяжелой задачи.
    threading.Thread(target=db_task, daemon=True).start()

    # Запускаем цикл опроса очереди в UI-потоке.
    root.after(100, poll_result_queue)


def poll_result_queue():
    """Проверяем, есть ли ответ от фонового потока."""
    try:
        kind, data = result_queue.get_nowait()
    except queue.Empty:
        # Пока ответа нет — проверим снова через 100 мс.
        root.after(100, poll_result_queue)
        return

    if kind == "done":
        books = data
        listbox.delete(0, tk.END)
        for book in books:
            listbox.insert(tk.END, book)
        status_label.config(text=f"Загружено: {len(books)} книг")
    else:
        status_label.config(text=f"Ошибка: {data}")

    load_btn.config(state="normal")


# --- UI ---
root = tk.Tk()
root.title("02 — Thread + Queue + after")
root.geometry("420x300")

load_btn = tk.Button(root, text="Загрузить", command=on_load_click)
load_btn.pack(pady=10)

status_label = tk.Label(root, text="Готов")
status_label.pack(pady=5)

listbox = tk.Listbox(root)
listbox.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()
