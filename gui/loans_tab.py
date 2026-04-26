import time
import tkinter as tk
from tkinter import ttk, messagebox

from workers import ThreadWorker
from database import repository


class LoansTab:
    def __init__(self, parent, root, status_var):
        self.parent = parent
        self.root = root
        self.status_var = status_var
        self.worker = ThreadWorker(root)

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ttk.Frame(self.parent)
        top.pack(fill="x", padx=5, pady=5)

        self.btn_refresh = ttk.Button(top, text="Оновити", command=self.refresh)
        self.btn_refresh.pack(side="left", padx=5)

        self.btn_new = ttk.Button(top, text="Оформити позику", command=self._open_new_loan_dialog)
        self.btn_new.pack(side="left", padx=5)

        self.btn_return = ttk.Button(top, text="Повернути обрану", command=self._return_selected)
        self.btn_return.pack(side="left", padx=5)

        self.progress = ttk.Progressbar(top, mode="indeterminate", length=120)

        frame = ttk.Frame(self.parent)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("book", "reader", "loaned_at")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col, txt, w in [
            ("book", "Книга", 360),
            ("reader", "Читач", 240),
            ("loaned_at", "Дата видачі", 130),
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _all_buttons(self):
        return (self.btn_refresh, self.btn_new, self.btn_return)

    def _start(self, msg):
        for b in self._all_buttons():
            b.config(state="disabled")
        self.progress.pack(side="right", padx=5)
        self.progress.start(10)
        self.status_var.set(msg)
        self._t0 = time.perf_counter()

    def _done(self, msg):
        self.progress.stop()
        self.progress.pack_forget()
        for b in self._all_buttons():
            b.config(state="normal")
        elapsed = time.perf_counter() - getattr(self, "_t0", time.perf_counter())
        self.status_var.set(f"{msg} (за {elapsed:.2f}с)")

    def _err(self, exc):
        self.progress.stop()
        self.progress.pack_forget()
        for b in self._all_buttons():
            b.config(state="normal")
        messagebox.showerror("Помилка", str(exc))
        self.status_var.set(f"Помилка: {exc}")

    def refresh(self):
        self.worker.run(
            repository.get_active_loans,
            on_start=lambda: self._start("Завантаження позик..."),
            on_done=self._populate,
            on_error=self._err,
        )

    def _populate(self, loans):
        self.tree.delete(*self.tree.get_children())
        for l in loans:
            self.tree.insert(
                "", "end", iid=str(l["id"]),
                values=(l["book title"], l["reader name"], l["loaned at"]),
            )
        self._done(f"Активних позик: {len(loans)}")

    def _open_new_loan_dialog(self):
        def load():
            return repository.get_all_books(), repository.get_all_readers()

        self.worker.run(
            load,
            on_start=lambda: self._start("Завантаження даних..."),
            on_done=self._show_new_loan_dialog,
            on_error=self._err,
        )

    def _show_new_loan_dialog(self, data):
        books, readers = data
        self._done("Готово")

        dlg = tk.Toplevel(self.root)
        dlg.title("Нова позика")
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="Книга:").grid(row=0, column=0, sticky="ne", padx=5, pady=3)
        book_lb = tk.Listbox(dlg, height=10, width=60, exportselection=False)
        for b in books:
            book_lb.insert(tk.END, f'{b["title"]} ({b["year"]}) — {b["authors"] or "—"}')
        book_lb.grid(row=0, column=1, padx=5, pady=3, sticky="we")

        ttk.Label(dlg, text="Читач:").grid(row=1, column=0, sticky="ne", padx=5, pady=3)
        reader_lb = tk.Listbox(dlg, height=6, width=60, exportselection=False)
        for r in readers:
            reader_lb.insert(tk.END, f'{r["full_name"]} <{r["email"]}>')
        reader_lb.grid(row=1, column=1, padx=5, pady=3, sticky="we")

        def submit():
            bsel = book_lb.curselection()
            rsel = reader_lb.curselection()
            if not bsel or not rsel:
                messagebox.showerror("Помилка", "Оберіть книгу та читача", parent=dlg)
                return
            book_id = books[bsel[0]]["id"]
            reader_id = readers[rsel[0]]["id"]
            self.worker.run(
                repository.create_loan, book_id, reader_id,
                on_start=lambda: self._start("Оформлення позики..."),
                on_done=lambda new_id: self._after_create(dlg, new_id),
                on_error=self._err,
            )

        ttk.Button(dlg, text="Оформити", command=submit).grid(
            row=2, column=0, columnspan=2, pady=10
        )

    def _after_create(self, dlg, new_id):
        self._done(f"Позику створено (id={new_id})")
        dlg.destroy()
        self.refresh()

    def _return_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Повернення", "Оберіть позику зі списку")
            return
        loan_id = int(sel[0])
        book = self.tree.set(sel[0], "book")
        if not messagebox.askyesno("Підтвердження", f"Повернути '{book}'?"):
            return
        self.worker.run(
            repository.return_book, loan_id,
            on_start=lambda: self._start("Повернення..."),
            on_done=lambda _: (self._done("Книгу повернено"), self.refresh()),
            on_error=self._err,
        )
