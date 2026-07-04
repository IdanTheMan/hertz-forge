import tkinter as tk
from tkinter import ttk

from hertz_forge.constants import (
    WAVES, BG, SURFACE, SURFACE2,
    ACCENT, ACCENT2, MUTED, FG,
    DIVIDER, CARD, SLIDER_LEN)
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

        # ── OUTPUT DEVICE ──
        self._section(top, "OUTPUT DEVICE")
        df = tk.Frame(top, bg=BG)
        df.pack(fill="x", padx=8, pady=2)
        self.device_names = [
            d[0] for d in self.output_devices]
        if not self.device_names:
            self.device_names = ["(no devices)"]
        self.device_var = tk.StringVar(
            value=self.device_names[0])
        self.dev_cb = ttk.Combobox(
            df, textvariable=self.device_var,
            values=self.device_names,
            state="readonly", width=34)
        self.dev_cb.pack(
            side="left", fill="x", expand=True)
        self.dev_cb.bind(
            "<<ComboboxSelected>>",
            lambda _: self._apply_device())
        ttk.Button(
            df, text="Test Stereo",
            style="Test.TButton",
            command=self._test_stereo
        ).pack(side="right", padx=(6, 0))
        self._sep(top)

        # ── VOLUME ──
        self._section(top, "VOLUME")
        vf = tk.Frame(top, bg=BG)
        vf.pack(fill="x", padx=8, pady=2)
        tk.Label(
            vf, text="Level", bg=BG,
            fg="#8888aa",
            font=("Helvetica", 10), width=10,
            anchor="w").pack(side="left")
        self._vol_var = tk.DoubleVar(value=50)
        ttk.Scale(
            vf, from_=0, to=100,
            length=SLIDER_LEN,
            variable=self._vol_var
        ).pack(side="left", padx=(0, 6))
        self.vol_spin = SpinEntry(
            vf, width=6, from_=0, to=100,
            step=1, fmt="{:.0f}",
            initial="50", suffix="%",
            callback=self._on_vol, bg=BG)
        self.vol_spin.pack(side="left")
        self._vol_var.trace_add(
            "write", self._on_vol_var)
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

        # ── PLAYLISTS header ──
        pl_hdr = tk.Frame(self._inner, bg=BG)
        pl_hdr.pack(
            fill="x", padx=8, pady=(8, 2))
        tk.Label(
            pl_hdr, text="PLAYLISTS",
            bg=BG, fg="#6666a0",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(side="left")

        tk.Frame(pl_hdr, bg=BG).pack(
            side="left", fill="x", expand=True)

        self._pl_shuffle_var = tk.BooleanVar(
            value=False)
        tk.Checkbutton(
            pl_hdr,
            variable=self._pl_shuffle_var,
            text="shuffle",
            bg=BG, fg=ACCENT,
            selectcolor=SURFACE2,
            activebackground=BG,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold"),
            command=self._toggle_pl_shuffle
        ).pack(side="right")

        self._pl_loop_var = tk.BooleanVar(
            value=False)
        tk.Checkbutton(
            pl_hdr,
            variable=self._pl_loop_var,
            text="loop",
            bg=BG, fg=ACCENT,
            selectcolor=SURFACE2,
            activebackground=BG,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold"),
            command=self._toggle_pl_loop
        ).pack(side="right", padx=(0, 8))

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

        # ── drop overlay (hidden until a
        #    file drag enters) ──
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