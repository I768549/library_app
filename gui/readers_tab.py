import time
import tkinter as tk
from tkinter import ttk, messagebox

from workers import ThreadWorker
from database import repository


class ReadersTab:
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

        self.btn_add = ttk.Button(top, text="Додати читача", command=self._open_add_dialog)
        self.btn_add.pack(side="left", padx=5)

        self.btn_delete = ttk.Button(top, text="Видалити обраного", command=self._delete_selected)
        self.btn_delete.pack(side="left", padx=5)

        self.progress = ttk.Progressbar(top, mode="indeterminate", length=120)

        frame = ttk.Frame(self.parent)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("full_name", "email", "registered_at", "active_loans")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col, txt, w in [
            ("full_name", "Ім'я", 240),
            ("email", "Email", 220),
            ("registered_at", "Зареєстрований", 150),
            ("active_loans", "Активних позик", 130),
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _start(self, msg):
        for b in (self.btn_refresh, self.btn_add, self.btn_delete):
            b.config(state="disabled")
        self.progress.pack(side="right", padx=5)
        self.progress.start(10)
        self.status_var.set(msg)
        self._t0 = time.perf_counter()

    def _done(self, msg):
        self.progress.stop()
        self.progress.pack_forget()
        for b in (self.btn_refresh, self.btn_add, self.btn_delete):
            b.config(state="normal")
        elapsed = time.perf_counter() - getattr(self, "_t0", time.perf_counter())
        self.status_var.set(f"{msg} (за {elapsed:.2f}с)")

    def _err(self, exc):
        self.progress.stop()
        self.progress.pack_forget()
        for b in (self.btn_refresh, self.btn_add, self.btn_delete):
            b.config(state="normal")
        messagebox.showerror("Помилка", str(exc))
        self.status_var.set(f"Помилка: {exc}")

    def refresh(self):
        self.worker.run(
            repository.get_all_readers,
            on_start=lambda: self._start("Завантаження читачів..."),
            on_done=self._populate,
            on_error=self._err,
        )

    def _populate(self, readers):
        self.tree.delete(*self.tree.get_children())
        for r in readers:
            self.tree.insert(
                "", "end", iid=str(r["id"]),
                values=(
                    r["full_name"],
                    r["email"],
                    r["registered_at"],
                    r["active loans"],
                ),
            )
        self._done(f"Завантажено {len(readers)} читачів")

    def _open_add_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Новий читач")
        dlg.transient(self.root)
        dlg.grab_set()

        full_name_var = tk.StringVar()
        email_var = tk.StringVar()

        ttk.Label(dlg, text="ПІБ:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        name_entry = tk.Entry(dlg, textvariable=full_name_var, width=40)
        name_entry.grid(row=0, column=1, padx=5, pady=3, sticky="we")

        ttk.Label(dlg, text="Email:").grid(row=1, column=0, sticky="e", padx=5, pady=3)
        email_entry = tk.Entry(dlg, textvariable=email_var, width=40)
        email_entry.grid(row=1, column=1, padx=5, pady=3, sticky="we")

        def submit():
            errors = []
            full = full_name_var.get().strip()
            email = email_var.get().strip()

            if not full:
                name_entry.config(background="#ffd6d6")
                errors.append("ПІБ порожнє")
            else:
                name_entry.config(background="white")

            if "@" not in email or len(email) < 3:
                email_entry.config(background="#ffd6d6")
                errors.append("Email некоректний (потрібен @)")
            else:
                email_entry.config(background="white")

            if errors:
                messagebox.showerror("Помилка", "\n".join(errors), parent=dlg)
                return

            self.worker.run(
                repository.add_reader, full, email,
                on_start=lambda: self._start("Додавання читача..."),
                on_done=lambda new_id: self._after_add(dlg, new_id),
                on_error=self._err,
            )

        ttk.Button(dlg, text="Зберегти", command=submit).grid(
            row=2, column=0, columnspan=2, pady=10
        )

    def _after_add(self, dlg, new_id):
        self._done(f"Читача додано (id={new_id})")
        dlg.destroy()
        self.refresh()

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Видалення", "Оберіть читача")
            return
        rid = int(sel[0])
        name = self.tree.set(sel[0], "full_name")
        if not messagebox.askyesno("Підтвердження", f"Видалити читача '{name}'?"):
            return
        self.worker.run(
            repository.delete_reader, rid,
            on_start=lambda: self._start("Видалення..."),
            on_done=lambda _: (self._done("Читача видалено"), self.refresh()),
            on_error=self._err,
        )
