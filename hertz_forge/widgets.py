# ═══════════════════════════════════════════════════════════════
#  SPIN ENTRY WIDGET
# ═══════════════════════════════════════════════════════════════

import tkinter as tk
from .constants import BG, FG, SURFACE, SURFACE2, ACCENT2, MUTED, ACCENT, ULINE


class SpinEntry(tk.Frame):
    """Compact numeric entry with ▲▼ arrows — click, hold-repeat, or drag."""

    def __init__(self, parent, width=7, from_=0, to=100, step=1,
                 fmt="{:.0f}", initial="0", callback=None, suffix="",
                 bg=BG):
        super().__init__(parent, bg=bg)
        self._fmt = fmt
        self._lo = from_
        self._hi = to
        self._step = step
        self._cb = callback
        self._rid = None
        self._dir = 0
        self._sy = 0
        self._bg = bg

        try:
            self._cur = float(initial)
        except:
            self._cur = float(from_)

        self.var = tk.StringVar(value=initial)

        # ── entry with bottom underline only ──
        entry_wrap = tk.Frame(self, bg=bg)
        entry_wrap.pack(side="left", fill="y")

        self._underline = tk.Frame(
            entry_wrap, bg=ULINE, height=1)
        self._underline.pack(
            side="bottom", fill="x")

        self.entry = tk.Entry(
            entry_wrap, width=width, justify="right",
            textvariable=self.var,
            font=("Helvetica", 10),
            bg=SURFACE, fg=FG,
            relief="flat", bd=0,
            highlightthickness=0,
            insertbackground=ACCENT,
            selectbackground=ACCENT2,
            selectforeground=ACCENT)
        self.entry.pack(fill="both", expand=True)

        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)

        af = tk.Frame(self, bg=bg)
        af.pack(side="left", fill="y")
        kw = dict(
            font=("Helvetica", 6), width=2,
            padx=0, pady=0, bg=SURFACE2, fg=MUTED,
            activebackground=ACCENT2,
            activeforeground=ACCENT,
            relief="flat", bd=0,
            highlightthickness=0, cursor="hand2")
        self._up = tk.Button(af, text="▲", **kw)
        self._up.pack(fill="both", expand=True)
        self._dn = tk.Button(af, text="▼", **kw)
        self._dn.pack(fill="both", expand=True)
        for b in (self._up, self._dn):
            b.bind("<Enter>",
                   lambda e, bt=b: bt.config(fg=ACCENT))
            b.bind("<Leave>",
                   lambda e, bt=b: bt.config(fg=MUTED))

        if suffix:
            tk.Label(
                self, text=suffix, bg=bg, fg=MUTED,
                font=("Helvetica", 9)).pack(
                    side="left", padx=(3, 0))

        for btn, d in ((self._up, 1), (self._dn, -1)):
            btn.bind(
                "<ButtonPress-1>",
                lambda e, dd=d: self._press(e, dd))
            btn.bind("<B1-Motion>", self._drag)
            btn.bind(
                "<ButtonRelease-1>",
                lambda e: self._release())

        self.entry.bind("<Return>", self._commit)
        self.entry.bind("<FocusOut>", self._focus_out)

    def _focus_in(self, _=None):
        self._underline.config(bg=ACCENT)
        self.entry.bind(
            "<FocusIn>",
            lambda e: self.entry.select_range(0, "end"))
        self.entry.select_range(0, "end")
        self.entry.icursor("end")

    def _focus_out(self, _=None):
        self._underline.config(bg=ULINE)
        self._commit()

    def _apply(self, v):
        v = max(self._lo, min(self._hi, v))
        self._cur = v
        self.var.set(self._fmt.format(v))
        if self._cb:
            self._cb(v)

    def _press(self, event, direction):
        self._dir = direction
        self._sy = event.y_root
        self._apply(self._cur + self._step * direction)
        self._rid = self.after(400, self._tick)

    def _tick(self):
        self._apply(self._cur + self._step * self._dir)
        self._rid = self.after(60, self._tick)

    def _drag(self, event):
        dy = self._sy - event.y_root
        if dy > 12:
            self._dir = 1
        elif dy < -12:
            self._dir = -1

    def _release(self):
        if self._rid is not None:
            self.after_cancel(self._rid)
            self._rid = None

    def _commit(self, _=None):
        try:
            self._apply(float(self.var.get()))
        except:
            self.var.set(self._fmt.format(self._cur))

    def set(self, v):
        self._cur = float(v)
        self.var.set(self._fmt.format(self._cur))

    def get(self):
        return self._cur