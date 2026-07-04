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

    # ── scroll ──

    def _schedule_scroll_sync(self):
        """Debounce: cancel any pending sync
        and schedule a new one 10 ms out."""
        if hasattr(self, '_scroll_sync_id'):
            try:
                self.root.after_cancel(
                    self._scroll_sync_id)
            except (ValueError, tk.TclError):
                pass
        self._scroll_sync_id = self.root.after(
            10, self._do_scroll_sync)

    def _do_scroll_sync(self):
        """Run once geometry has settled."""
        self._scanvas.configure(
            scrollregion=self._scanvas.bbox(
                "all"))
        self._clamp_scroll()

    def _on_inner_configure(self, _event):
        self._schedule_scroll_sync()

    def _on_canvas_resize(self, event):
        self._scanvas.itemconfig(
            self._cw, width=event.width)
        self._clamp_scroll()

    def _refresh_scroll(self):
        self._schedule_scroll_sync()

    def _clamp_scroll(self):
        """Reset to top when content fits
        inside the viewport."""
        bbox = self._scanvas.bbox("all")
        if not bbox:
            return
        content_h = bbox[3] - bbox[1]
        canvas_h = self._scanvas.winfo_height()
        if content_h <= canvas_h:
            self._scanvas.yview_moveto(0.0)

    def _on_mousewheel(self, event):
        """Only scroll when content overflows
        the viewport."""
        bbox = self._scanvas.bbox("all")
        if bbox:
            content_h = bbox[3] - bbox[1]
            canvas_h = self._scanvas\
                           .winfo_height()
            if content_h <= canvas_h:
                return
        self._scanvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units")