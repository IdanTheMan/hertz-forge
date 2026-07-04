import tkinter as tk
from tkinter import ttk

from hertz_forge.constants import (
    BG, SURFACE, SURFACE2, ACCENT, ACCENT2, MUTED, FG)


class StyleMixin:

    def _style(self):
        self.root.option_add(
            "*TCombobox*Listbox.background",
            SURFACE)
        self.root.option_add(
            "*TCombobox*Listbox.foreground", FG)
        self.root.option_add(
            "*TCombobox*Listbox.selectBackground",
            ACCENT2)
        self.root.option_add(
            "*TCombobox*Listbox.selectForeground",
            ACCENT)
        self.root.option_add(
            "*TCombobox*Listbox.font",
            ("Helvetica", 10))
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(
            ".", background=BG, foreground=FG,
            fieldbackground=SURFACE,
            troughcolor=SURFACE2, borderwidth=0)
        s.configure(
            "TLabel", background=BG,
            foreground=FG,
            font=("Helvetica", 10))
        s.configure(
            "TButton",
            font=("Helvetica", 10), padding=5)
        s.configure(
            "Play.TButton",
            font=("Helvetica", 12, "bold"),
            padding=6)
        s.configure(
            "Test.TButton",
            font=("Helvetica", 8), padding=3)
        s.configure(
            "Small.TButton",
            font=("Helvetica", 9), padding=3)
        s.configure(
            "TCombobox",
            fieldbackground=SURFACE,
            background=SURFACE,
            foreground=FG, arrowcolor=ACCENT,
            bordercolor="#3a3a5e",
            darkcolor=SURFACE,
            lightcolor=SURFACE,
            selectbackground=ACCENT2,
            selectforeground=FG,
            font=("Helvetica", 10))
        s.map("TCombobox",
               fieldbackground=[
                   ("readonly", SURFACE),
                   ("active", SURFACE2),
                   ("!disabled", SURFACE)],
               foreground=[
                   ("readonly", FG),
                   ("active", FG),
                   ("!disabled", FG),
                   ("focus", FG)],
               background=[
                   ("readonly", SURFACE),
                   ("active", SURFACE2)],
               arrowcolor=[
                   ("disabled", MUTED),
                   ("active", ACCENT),
                   ("!disabled", ACCENT)],
               bordercolor=[
                   ("focus", ACCENT),
                   ("!focus", "#3a3a5e")])
        s.configure(
            "Vertical.TScrollbar",
            background=SURFACE2,
            troughcolor=BG, bordercolor=BG,
            arrowcolor=MUTED,
            darkcolor=SURFACE,
            lightcolor=SURFACE)
        s.map("Vertical.TScrollbar",
               background=[
                   ("active", ACCENT2),
                   ("!active", SURFACE2)],
               arrowcolor=[
                   ("active", ACCENT),
                   ("!active", MUTED)])