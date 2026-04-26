import tkinter as tk
from tkinter import ttk

from gui.books_tab import BooksTab
from gui.readers_tab import ReadersTab
from gui.loans_tab import LoansTab
from gui.chat_tab import ChatTab
from gui.theme import apply_theme


class LibraryApp:
    def __init__(self):
        self.root = tk.Tk()
        apply_theme(self.root)
        self.root.title("Бібліотека")
        self.root.geometry("1280x720")

        self.status_var = tk.StringVar(value="Готовий")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        books_frame = ttk.Frame(notebook)
        notebook.add(books_frame, text="Книги")
        BooksTab(books_frame, self.root, self.status_var)

        readers_frame = ttk.Frame(notebook)
        notebook.add(readers_frame, text="Читачі")
        ReadersTab(readers_frame, self.root, self.status_var)

        loans_frame = ttk.Frame(notebook)
        notebook.add(loans_frame, text="Позичено")
        LoansTab(loans_frame, self.root, self.status_var)

        chat_frame = ttk.Frame(notebook)
        notebook.add(chat_frame, text="Асистент")
        ChatTab(chat_frame, self.root, self.status_var)

        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            relief="sunken",
            padx=5,
        )
        status_bar.pack(side="bottom", fill="x")

    def run(self):
        self.root.mainloop()
