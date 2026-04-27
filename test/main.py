import queue
from threading import Thread
import tkinter as tk
import time

tasks = queue.Queue()
counter = 0
def worker():
    time.sleep(4)
    tasks.put(f"Task is ended {counter} times")


def checker():
    try:
        result = tasks.get_nowait()
        status_label.config(text= f"{result}")
        
    except queue.Empty:
        root.after(100, checker)

def starter():
    status_label.config(text="Вычисляю...")
    Thread(target=worker, daemon=True).start()
    Thread(target=worker, daemon=True).start()
    Thread(target=worker, daemon=True).start()
    Thread(target=worker, daemon=True).start()
    Thread(target=worker, daemon=True).start()

    checker()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x300")
    tk.Button(root, text="Load", command=starter).pack(pady=10)
    tk.Button(root, text="Load as a human").pack(pady=10)
    status_label = tk.Label(root, text="Готов")
    status_label.pack(pady=5)

    listbox = tk.Listbox(root)
    listbox.pack(fill="both", expand=True, padx=10, pady=10)

    root.mainloop()