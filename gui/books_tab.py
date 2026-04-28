import time
import tkinter as tk
from tkinter import ttk, messagebox

from workers import ThreadWorker
from database import repository


class BooksTab:
    def __init__(self, parent, root, status_var):
        self.parent = parent
        self.root = root
        self.status_var = status_var
        self.worker = ThreadWorker(root)

        self._all_books: list[dict] = []
        self._authors: list[dict] = []
        self._genres: list[dict] = []
        self._sort_state: dict[str, bool] = {}

        self._build_ui()
        self.refresh_books()
        self._load_lookups()

    def _build_ui(self):
        top = ttk.Frame(self.parent)
        top.pack(fill="x", padx=5, pady=5)

        ttk.Label(top, text="Пошук:").pack(side="left")
        self.search_var = tk.StringVar()
        # NOTE: прибрали "живий" пошук через trace_add
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda _e: self._apply_search())

        self.btn_search = ttk.Button(top, text="Шукати", command=self._apply_search)
        self.btn_search.pack(side="left", padx=5)

        self.btn_refresh = ttk.Button(top, text="Оновити", command=self.refresh_books)
        self.btn_refresh.pack(side="left", padx=5)

        self.btn_add = ttk.Button(top, text="Додати книгу", command=self._open_add_dialog)
        self.btn_add.pack(side="left", padx=5)

        self.btn_delete = ttk.Button(top, text="Видалити обрану", command=self._delete_selected)
        self.btn_delete.pack(side="left", padx=5)

        self.progress = ttk.Progressbar(top, mode="indeterminate", length=120)
        # Прогресс-бар з'являється лише на час фонової операції

        frame = ttk.Frame(self.parent)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("title", "year", "isbn", "authors", "genres")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col, txt, w in [
            ("title", "Назва", 280),
            ("year", "Рік", 60),
            ("isbn", "ISBN", 130),
            ("authors", "Автори", 200),
            ("genres", "Жанри", 180),
        ]:
            self.tree.heading(col, text=txt, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # ---- progress / status helpers ----

    def _start(self, msg):
        for b in (self.btn_search, self.btn_refresh, self.btn_add, self.btn_delete):
            b.config(state="disabled")
        self.progress.pack(side="right", padx=5)
        self.progress.start(10)
        self.status_var.set(msg)
        self._t0 = time.perf_counter()

    def _done(self, msg):
        self.progress.stop()
        self.progress.pack_forget()
        for b in (self.btn_search, self.btn_refresh, self.btn_add, self.btn_delete):
            b.config(state="normal")
        elapsed = time.perf_counter() - getattr(self, "_t0", time.perf_counter())
        self.status_var.set(f"{msg} (за {elapsed:.2f}с)")

    def _err(self, exc):
        self.progress.stop()
        self.progress.pack_forget()
        for b in (self.btn_search, self.btn_refresh, self.btn_add, self.btn_delete):
            b.config(state="normal")
        messagebox.showerror("Помилка", str(exc))
        self.status_var.set(f"Помилка: {exc}")

    # ---- loading ----

    def refresh_books(self):
        self.worker.run(
            repository.get_all_books,
            on_start=lambda: self._start("Завантаження книг..."),
            on_done=self._populate_tree,
            on_error=self._err,
        )

    def _load_lookups(self):
        def load():
            return repository.get_all_authors(), repository.get_all_genres()
        self.worker.run(
            load,
            on_done=self._save_lookups,
            on_error=lambda e: None,
        )

    def _save_lookups(self, data):
        self._authors, self._genres = data

    def _populate_tree(self, books):
        self._all_books = books
        self._render(books)
        self._done(f"Завантажено {len(books)} книг")

    def _render(self, books):
        self.tree.delete(*self.tree.get_children())
        for b in books:
            self.tree.insert(
                "", "end", iid=str(b["id"]),
                values=(b["title"], b["year"], b["isbn"], b["authors"], b["genres"]),
            )

    def _apply_search(self):
        q = self.search_var.get().strip()
        if not q:
            self._render(self._all_books)
            return

        q_norm = q.casefold()

        filtered = [
            b for b in self._all_books
            if str(b.get("title", "")).casefold() == q_norm
            or str(b.get("authors", "")).casefold() == q_norm
        ]
        self._render(filtered)

    def _sort_by(self, col):
        ascending = not self._sort_state.get(col, False)
        self._sort_state = {col: ascending}
        items = list(self.tree.get_children())

        def key(iid):
            v = str(self.tree.set(iid, col))
            if col == "year":
                try:
                    return int(v)
                except ValueError:
                    return 0
            return v.lower()

        items.sort(key=key, reverse=not ascending)
        for i, iid in enumerate(items):
            self.tree.move(iid, "", i)

    # ---- add dialog ----

    def _open_add_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Нова книга")
        dlg.transient(self.root)
        dlg.grab_set()

        title_var = tk.StringVar()
        year_var = tk.StringVar()
        isbn_var = tk.StringVar()

        ttk.Label(dlg, text="Назва:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        title_entry = tk.Entry(dlg, textvariable=title_var, width=40)
        title_entry.grid(row=0, column=1, padx=5, pady=3, sticky="we")

        ttk.Label(dlg, text="Рік:").grid(row=1, column=0, sticky="e", padx=5, pady=3)
        year_entry = tk.Entry(dlg, textvariable=year_var, width=40)
        year_entry.grid(row=1, column=1, padx=5, pady=3, sticky="we")

        ttk.Label(dlg, text="ISBN (13 цифр):").grid(row=2, column=0, sticky="e", padx=5, pady=3)
        isbn_entry = tk.Entry(dlg, textvariable=isbn_var, width=40)
        isbn_entry.grid(row=2, column=1, padx=5, pady=3, sticky="we")

        ttk.Label(dlg, text="Опис:").grid(row=3, column=0, sticky="ne", padx=5, pady=3)
        desc_text = tk.Text(dlg, width=40, height=4)
        desc_text.grid(row=3, column=1, padx=5, pady=3, sticky="we")

        ttk.Label(dlg, text="Автори:").grid(row=4, column=0, sticky="ne", padx=5, pady=3)
        authors_lb = tk.Listbox(dlg, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        for a in self._authors:
            authors_lb.insert(tk.END, f'{a["last_name"]} {a["first_name"]}')
        authors_lb.grid(row=4, column=1, padx=5, pady=3, sticky="we")

        ttk.Label(dlg, text="Жанри:").grid(row=5, column=0, sticky="ne", padx=5, pady=3)
        genres_lb = tk.Listbox(dlg, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        for g in self._genres:
            genres_lb.insert(tk.END, g["name"])
        genres_lb.grid(row=5, column=1, padx=5, pady=3, sticky="we")

        def submit():
            errors = []

            for entry, var, name in [
                (title_entry, title_var, "Назва"),
                (year_entry, year_var, "Рік"),
                (isbn_entry, isbn_var, "ISBN"),
            ]:
                if not var.get().strip():
                    entry.config(background="#ffd6d6")
                    errors.append(f"{name}: порожнє")
                else:
                    entry.config(background="white")

            year_int = 0
            try:
                year_int = int(year_var.get())
            except ValueError:
                year_entry.config(background="#ffd6d6")
                errors.append("Рік має бути числом")

            isbn_val = isbn_var.get().strip()
            if not (isbn_val.isdigit() and len(isbn_val) == 13):
                isbn_entry.config(background="#ffd6d6")
                errors.append("ISBN має містити рівно 13 цифр")

            if errors:
                messagebox.showerror("Помилка валідації", "\n".join(errors), parent=dlg)
                return

            author_ids = [self._authors[i]["id"] for i in authors_lb.curselection()]
            genre_ids = [self._genres[i]["id"] for i in genres_lb.curselection()]
            description = desc_text.get("1.0", "end").strip()

            self.worker.run(
                repository.add_book,
                title_var.get().strip(), year_int, isbn_val, description,
                genre_ids, author_ids,
                on_start=lambda: self._start("Додавання книги..."),
                on_done=lambda new_id: self._after_add(dlg, new_id),
                on_error=self._err,
            )

        ttk.Button(dlg, text="Зберегти", command=submit).grid(
            row=6, column=0, columnspan=2, pady=10
        )

    def _after_add(self, dlg, new_id):
        self._done(f"Книгу додано (id={new_id})")
        dlg.destroy()
        self.refresh_books()

    # ---- delete ----

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Видалення", "Оберіть книгу зі списку")
            return
        book_id = int(sel[0])
        title = self.tree.set(sel[0], "title")
        if not messagebox.askyesno("Підтвердження", f"Видалити '{title}'?"):
            return
        self.worker.run(
            repository.delete_book, book_id,
            on_start=lambda: self._start("Видалення..."),
            on_done=lambda _: (self._done("Книгу видалено"), self.refresh_books()),
            on_error=self._err,
        )
