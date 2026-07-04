import tkinter as tk

from hertz_forge.constants import BG, MUTED, DIVIDER, CARD

_LABEL_PX = 75


class HelperMixin:

    def _sep(self, p):
        tk.Frame(p, bg=DIVIDER, height=1).pack(
            fill="x", padx=8, pady=6)

    def _section(self, p, text):
        tk.Label(
            p, text=text, bg=BG, fg="#6666a0",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(
                fill="x", padx=8, pady=(8, 2))

    def _lbl(self, parent, text, row=0,
             bg=CARD):
        tk.Label(
            parent, text=text, bg=bg,
            fg="#8888aa",
            font=("Helvetica", 8, "bold"),
            anchor="w").grid(
                row=row, column=0,
                sticky="w", padx=(0, 4))

    def _label_row(self, parent, text, bg=CARD):
        r = tk.Frame(parent, bg=bg)
        r.pack(fill="x", pady=1)
        r.columnconfigure(0, minsize=_LABEL_PX)
        self._lbl(r, text, bg=bg)
        return r

    def _on_inner_configure(self, _event):
        self._scanvas.configure(
            scrollregion=self._scanvas.bbox(
                "all"))

    def _on_canvas_resize(self, event):
        self._scanvas.itemconfig(
            self._cw, width=event.width)

    def _refresh_scroll(self):
        self.root.update_idletasks()
        self._scanvas.configure(
            scrollregion=self._scanvas.bbox(
                "all"))

    def _on_mousewheel(self, event):
        self._scanvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units")