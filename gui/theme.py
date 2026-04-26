"""Косметичні налаштування для Tk: тема, шрифти, DPI.

Допомагає виправити «битмапні» шрифти в conda-збірках Tcl/Tk на Linux —
ми форсуємо конкретний системний шрифт (а не дефолтний 'fixed').
"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

_PREFERRED_FONTS = (
    "Noto Sans",
    "Cantarell",
    "Inter",
    "DejaVu Sans",
    "Liberation Sans",
    "Ubuntu",
    "Helvetica",
)
_PREFERRED_MONO = (
    "JetBrains Mono",
    "Fira Code",
    "Source Code Pro",
    "DejaVu Sans Mono",
    "Liberation Mono",
    "Noto Sans Mono",
    "Monospace",
)


def _pick(root: tk.Tk, candidates) -> str | None:
    families = set(tkfont.families(root))
    for f in candidates:
        if f in families:
            return f
    return None


def apply_theme(root: tk.Tk, base_size: int = 11) -> None:
    # HiDPI масштабування (1.0 — 72dpi; десктопи зазвичай 96+)
    try:
        root.tk.call("tk", "scaling", 1.33)
    except tk.TclError:
        pass

    style = ttk.Style(root)
    available = style.theme_names()
    for theme in ("clam", "alt", "default"):
        if theme in available:
            style.theme_use(theme)
            break

    family = _pick(root, _PREFERRED_FONTS) or "TkDefaultFont"
    mono = _pick(root, _PREFERRED_MONO) or family

    named_proportional = (
        "TkDefaultFont", "TkTextFont", "TkHeadingFont",
        "TkMenuFont", "TkSmallCaptionFont", "TkCaptionFont",
        "TkIconFont", "TkTooltipFont",
    )
    for name in named_proportional:
        try:
            tkfont.nametofont(name).configure(family=family, size=base_size)
        except tk.TclError:
            pass
    try:
        tkfont.nametofont("TkFixedFont").configure(family=mono, size=base_size)
    except tk.TclError:
        pass

    style.configure("Treeview", rowheight=int(base_size * 2.2))
    style.configure("Treeview.Heading", font=(family, base_size, "bold"))
    style.configure("TNotebook.Tab", padding=(12, 6))
    style.configure("TButton", padding=(10, 4))
