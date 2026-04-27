import queue
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from services import recommender


class ChatTab:
    """Чат із локальною LLM (Ollama). Потокова відповідь передається у GUI
    через threading.Queue + root.after()."""

    def __init__(self, parent, root, status_var):
        self.parent = parent
        self.root = root
        self.status_var = status_var

        self.queue: queue.Queue = queue.Queue()
        self.history: list[dict] = []
        self.streaming = False
        self._assistant_buf = ""

        self._build_ui()
        self._append("Feel free to ask! \n")
        self._warmup_model_async()

    def _build_ui(self):
        top = ttk.Frame(self.parent)
        top.pack(fill="x", padx=5, pady=5)

        ttk.Label(
            top,
            text=f"Модель: {recommender.DEFAULT_MODEL}    {recommender.OLLAMA_URL}",
        ).pack(side="left")

        self.btn_clear = ttk.Button(top, text="Очистити чат", command=self._clear)
        self.btn_clear.pack(side="right")

        import tkinter.font as tkfont
        default = tkfont.nametofont("TkDefaultFont")
        family = default.actual("family")
        size = default.actual("size")

        self.history_widget = scrolledtext.ScrolledText(
            self.parent, wrap="word", state="disabled",
            font=(family, size),
        )
        self.history_widget.pack(fill="both", expand=True, padx=5, pady=5)
        self.history_widget.tag_config(
            "user", foreground="#1565c0",
            font=(family, size, "bold"),
        )
        self.history_widget.tag_config(
            "assistant", foreground="#2e7d32",
            font=(family, size, "bold"),
        )
        self.history_widget.tag_config(
            "system", foreground="#888888",
            font=(family, max(size - 1, 8), "italic"),
        )

        bottom = ttk.Frame(self.parent)
        bottom.pack(fill="x", padx=5, pady=5)

        self.input_var = tk.StringVar()
        self.entry = ttk.Entry(bottom, textvariable=self.input_var)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry.bind("<Return>", lambda _e: self._send())

        self.btn_send = ttk.Button(bottom, text="Надіслати", command=self._send)
        self.btn_send.pack(side="right")

        self.progress = ttk.Progressbar(bottom, mode="indeterminate", length=100)

    # ---- helpers ----

    def _append(self, text: str, tag: str | None = None):
        self.history_widget.config(state="normal")
        if tag:
            self.history_widget.insert("end", text, tag)
        else:
            self.history_widget.insert("end", text)
        self.history_widget.see("end")
        self.history_widget.config(state="disabled")

    def _clear(self):
        if self.streaming:
            return
        self.history.clear()
        self.history_widget.config(state="normal")
        self.history_widget.delete("1.0", "end")
        self.history_widget.config(state="disabled")
        self._append("Історію очищено.\n\n", "system")

    # ---- send / stream ----

    def _warmup_model_async(self):
        def worker():
            try:
                recommender.warmup_model()
            except Exception:
                # Warmup is best-effort and must not block the chat UI.
                return

        threading.Thread(target=worker, daemon=True).start()

    def _send(self):
        if self.streaming:
            return
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")

        self._append("Ви: ", "user")
        self._append(f"{text}\n")
        self.history.append({"role": "user", "content": text})

        self._append("Помічник: ", "assistant")
        self._assistant_buf = ""

        self.streaming = True
        self.btn_send.config(state="disabled")
        self.btn_clear.config(state="disabled")
        self.entry.config(state="disabled")
        self.progress.pack(side="right", padx=5)
        self.progress.start(10)
        self.status_var.set("AI відповідає...")

        history_snapshot = list(self.history)

        def worker():
            try:
                def on_chunk(chunk: str):
                    self.queue.put(("chunk", chunk))
                recommender.chat_stream(history_snapshot, on_chunk)
                self.queue.put(("done", None))
            except Exception as exc:
                self.queue.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(50, self._poll_queue)

    def _poll_queue(self):
        had_data = False
        try:
            while True:
                kind, data = self.queue.get_nowait()
                had_data = True
                if kind == "chunk":
                    self._append(data)
                    self._assistant_buf += data
                elif kind == "done":
                    self._append("\n\n")
                    self.history.append(
                        {"role": "assistant", "content": self._assistant_buf}
                    )
                    self._finish("Готово")
                    return
                elif kind == "error":
                    self._append(f"\n[Помилка: {data}]\n\n", "system")
                    messagebox.showerror("Помилка AI", str(data))
                    # відкочуємо останнє повідомлення користувача — щоб
                    # повторна спроба не накопичувала контекст
                    if self.history and self.history[-1]["role"] == "user":
                        pass
                    self._finish("Помилка AI")
                    return
        except queue.Empty:
            pass
        # продовжуємо опитувати
        self.root.after(50 if had_data else 100, self._poll_queue)

    def _finish(self, status_text: str):
        self.streaming = False
        self.btn_send.config(state="normal")
        self.btn_clear.config(state="normal")
        self.entry.config(state="normal")
        self.entry.focus_set()
        self.progress.stop()
        self.progress.pack_forget()
        self.status_var.set(status_text)
