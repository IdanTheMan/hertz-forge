import tkinter as tk
from tkinter import ttk

from hertz_forge.constants import (
    BG, SURFACE2, ACCENT, ACCENT2, MUTED, SLIDER_LEN)
from hertz_forge.widgets import SpinEntry


class BuildMixin:

    def _build(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=4, pady=(8, 0))

        tk.Label(
            top, text="Hertz Forge",
            bg=BG, fg=ACCENT,
            font=("Helvetica", 18, "bold")
        ).pack(
            anchor="w", padx=12, pady=(10, 0))
        tk.Label(
            top,
            text="Playlist Mode "
                 "— Sequential Brainwaves",
            bg=BG, fg=MUTED,
            font=("Helvetica", 9)
        ).pack(anchor="w", padx=12)
        self._sep(top)

        # ── Output device ──
        dev_row = tk.Frame(top, bg=BG)
        dev_row.pack(fill="x", padx=8, pady=2)
        tk.Label(
            dev_row, text="Output", bg=BG,
            fg="#8888aa",
            font=("Helvetica", 10),
            width=8, anchor="w"
        ).pack(side="left")
        self.device_names = [
            d[0] for d in self.output_devices]
        if not self.device_names:
            self.device_names = ["(no devices)"]
        self.device_var = tk.StringVar(
            value=self.device_names[0])
        self.dev_cb = ttk.Combobox(
            dev_row, textvariable=self.device_var,
            values=self.device_names,
            state="readonly", width=30)
        self.dev_cb.pack(
            side="left", fill="x", expand=True)
        self.dev_cb.bind(
            "<<ComboboxSelected>>",
            lambda _: self._apply_device())
        ttk.Button(
            dev_row, text="Test Stereo",
            style="Test.TButton",
            command=self._test_stereo
        ).pack(side="right", padx=(6, 0))

        # ── Volume ──
        vol_row = tk.Frame(top, bg=BG)
        vol_row.pack(fill="x", padx=8, pady=2)
        tk.Label(
            vol_row, text="Volume", bg=BG,
            fg="#8888aa",
            font=("Helvetica", 10),
            width=8, anchor="w"
        ).pack(side="left")
        self._vol_var = tk.DoubleVar(value=50)
        ttk.Scale(
            vol_row, from_=0, to=100,
            length=SLIDER_LEN,
            variable=self._vol_var
        ).pack(side="left", padx=(0, 6))
        self.vol_spin = SpinEntry(
            vol_row, width=6, from_=0, to=100,
            step=1, fmt="{:.0f}",
            initial="50", suffix="%",
            callback=self._on_vol, bg=BG)
        self.vol_spin.pack(side="left")
        self._vol_var.trace_add(
            "write", self._on_vol_var)

        # ── Playlists controls ──
        pl_row = tk.Frame(top, bg=BG)
        pl_row.pack(fill="x", padx=8, pady=(4, 2))
        tk.Label(
            pl_row, text="Playlists", bg=BG,
            fg="#6666a0",
            font=("Helvetica", 9, "bold"),
            width=8, anchor="w"
        ).pack(side="left")

        self._pl_shuffle_var = tk.BooleanVar(
            value=False)
        shuffle_cb = tk.Checkbutton(
            pl_row,
            variable=self._pl_shuffle_var,
            text="shuffle",
            bg=BG, fg=MUTED,
            selectcolor=BG,
            activebackground=BG,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold"),
            command=lambda: (
                self._toggle_pl_shuffle(),
                shuffle_cb.config(
                    fg=ACCENT
                    if self._pl_shuffle_var.get()
                    else MUTED)))
        shuffle_cb.pack(side="left")

        self._pl_loop_var = tk.BooleanVar(
            value=False)
        loop_cb = tk.Checkbutton(
            pl_row,
            variable=self._pl_loop_var,
            text="loop",
            bg=BG, fg=MUTED,
            selectcolor=BG,
            activebackground=BG,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold"),
            command=lambda: (
                self._toggle_pl_loop(),
                loop_cb.config(
                    fg=ACCENT
                    if self._pl_loop_var.get()
                    else MUTED)))
        loop_cb.pack(side="left", padx=(4, 8))

        self._stop_all_btn = tk.Button(
            pl_row, text="▶ Play All",
            font=("Helvetica", 9, "bold"),
            bg=SURFACE2, fg=ACCENT,
            activebackground=ACCENT2,
            activeforeground=ACCENT,
            relief="flat", bd=0,
            padx=6, pady=2,
            cursor="hand2",
            command=self._play_or_stop_all)
        self._stop_all_btn.pack(side="left")

        self._sep(top)

        # ── scrollable area ──
        bottom = tk.Frame(self.root, bg=BG)
        bottom.pack(fill="both", expand=True)

        self._sbar = ttk.Scrollbar(
            bottom, orient="vertical")
        self._sbar.pack(side="right", fill="y")
        self._scanvas = tk.Canvas(
            bottom, bg=BG,
            highlightthickness=0,
            yscrollcommand=self._sbar.set)
        self._scanvas.pack(
            side="left", fill="both",
            expand=True)
        self._sbar.config(
            command=self._scanvas.yview)

        self._inner = tk.Frame(
            self._scanvas, bg=BG)
        self._cw = self._scanvas.create_window(
            (0, 0), window=self._inner,
            anchor="nw")

        self._inner.bind(
            "<Configure>",
            self._on_inner_configure)
        self._scanvas.bind(
            "<Configure>",
            self._on_canvas_resize)
        self._scanvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel)

        # ── playlist frame ──
        self._pl_frame = tk.Frame(
            self._inner, bg=BG)
        self._pl_frame.pack(
            fill="x", padx=4, pady=4)

        btn_f = tk.Frame(self._inner, bg=BG)
        btn_f.pack(
            fill="x", padx=4, pady=(8, 4))
        _btn_row = tk.Frame(btn_f, bg=BG)
        _btn_row.pack(anchor="center")
        ttk.Button(
            _btn_row, text="+ Playlist",
            style="Small.TButton",
            command=self._add_playlist
        ).pack(side="left", padx=4)
        ttk.Button(
            _btn_row, text="Load Configs…",
            style="Small.TButton",
            command=self._load_configs_dialog
        ).pack(side="left", padx=4)

        # ── drop overlay ──
        self._drop_overlay = tk.Frame(
            self.root, bg="#0a0a20",
            highlightthickness=3,
            highlightbackground=ACCENT)
        tk.Label(
            self._drop_overlay,
            text="↓  Drop .hfc configs here  ↓",
            bg="#0a0a20", fg=ACCENT,
            font=("Helvetica", 14, "bold")
        ).place(relx=0.5, rely=0.5,
                anchor="center")
        self._drop_overlay.place_forget()

        tk.Frame(
            self._inner, bg=BG, height=20
        ).pack()