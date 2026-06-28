# ═══════════════════════════════════════════════════════════════
#  GUI APPLICATION
# ═══════════════════════════════════════════════════════════════

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import numpy as np

from .constants import (BAND_LABELS, WAVES, BW_PRESETS,
                        BG, SURFACE, SURFACE2, GRID, ACCENT,
                        ACCENT2, MUTED, FG, DIVIDER, CARD,
                        SLIDER_LEN)
from .audio import Engine, get_output_devices, test_device_stereo
from .widgets import SpinEntry


class App:

    def __init__(self):
        self.eng = Engine()
        self.output_devices = get_output_devices()
        self._draw_on = False
        self.root = tk.Tk()
        self.root.title("Hertz Forge")
        self.root.geometry("540x720")
        self.root.minsize(480, 360)
        self.root.configure(bg=BG)
        self._style()
        self._build()
        self._apply_device()
        self._update_bw_label()
        self._update_fm_display()
        self._update_binaural_display()
        self._tick()

    # ── style ─────────────────────────────────────────────────

    def _style(self):
        self.root.option_add("*TCombobox*Listbox.background",
                             SURFACE)
        self.root.option_add("*TCombobox*Listbox.foreground", FG)
        self.root.option_add(
            "*TCombobox*Listbox.selectBackground", ACCENT2)
        self.root.option_add(
            "*TCombobox*Listbox.selectForeground", ACCENT)
        self.root.option_add(
            "*TCombobox*Listbox.font", ("Helvetica", 10))
        s = ttk.Style(); s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG,
                     fieldbackground=SURFACE,
                     troughcolor=SURFACE2, borderwidth=0)
        s.configure("TLabel", background=BG, foreground=FG,
                     font=("Helvetica", 10))
        s.configure("TButton", font=("Helvetica", 10), padding=5)
        s.configure("Play.TButton",
                     font=("Helvetica", 12, "bold"), padding=6)
        s.configure("Test.TButton",
                     font=("Helvetica", 8), padding=3)
        s.configure("TCombobox",
                     fieldbackground=SURFACE, background=SURFACE,
                     foreground=FG, arrowcolor=ACCENT,
                     bordercolor="#3a3a5e",
                     darkcolor=SURFACE, lightcolor=SURFACE,
                     selectbackground=ACCENT2,
                     selectforeground=FG,
                     font=("Helvetica", 10))
        s.map("TCombobox",
               fieldbackground=[("readonly", SURFACE),
                                ("active", SURFACE2),
                                ("!disabled", SURFACE)],
               foreground=[("readonly", FG), ("active", FG),
                           ("!disabled", FG), ("focus", FG)],
               background=[("readonly", SURFACE),
                           ("active", SURFACE2)],
               arrowcolor=[("disabled", MUTED),
                           ("active", ACCENT),
                           ("!disabled", ACCENT)],
               bordercolor=[("focus", ACCENT),
                            ("!focus", "#3a3a5e")])
        s.configure("Vertical.TScrollbar",
                     background=SURFACE2, troughcolor=BG,
                     bordercolor=BG, arrowcolor=MUTED,
                     darkcolor=SURFACE, lightcolor=SURFACE)
        s.map("Vertical.TScrollbar",
               background=[("active", ACCENT2),
                           ("!active", SURFACE2)],
               arrowcolor=[("active", ACCENT),
                           ("!active", MUTED)])

    # ── layout helpers ─────────────────────────────────────────

    def _sep(self, p):
        tk.Frame(p, bg=DIVIDER, height=1).pack(
            fill="x", padx=8, pady=6)

    def _section(self, p, text):
        tk.Label(p, text=text, bg=BG, fg="#6666a0",
                 font=("Helvetica", 9, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=(8, 2))

    def _card(self, parent):
        c = tk.Frame(parent, bg=CARD, highlightthickness=1,
                     highlightbackground="#222244")
        c.pack(fill="x", padx=4, pady=4, ipady=6)
        c.columnconfigure(0, weight=1)
        c.columnconfigure(1, weight=1)
        return c

    def _col(self, card, row, col, pad=(10, 4)):
        f = tk.Frame(card, bg=CARD)
        f.grid(row=row, column=col, sticky="nsew",
               padx=pad, pady=4)
        return f

    def _col_label(self, parent, text):
        tk.Label(parent, text=text, bg=CARD, fg="#8888aa",
                 font=("Helvetica", 9, "bold"),
                 anchor="w").pack(fill="x")

    def _col_hint(self, parent, text):
        tk.Label(parent, text=text, bg=CARD, fg=MUTED,
                 font=("Helvetica", 8, "italic"),
                 anchor="w").pack(fill="x")

    def _slider_row(self, parent, from_, to, step, fmt,
                    initial, suffix, callback, bg=CARD):
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", pady=2)
        var = tk.DoubleVar(value=float(initial))
        slider = ttk.Scale(row, from_=from_, to=to,
                           length=SLIDER_LEN, variable=var)
        slider.pack(side="left", padx=(0, 6))
        spin = SpinEntry(row, width=6, from_=from_, to=to,
                         step=step, fmt=fmt, initial=initial,
                         suffix=suffix, callback=callback, bg=bg)
        spin.pack(side="left")
        return slider, spin, var

    def _divider_row(self, card, row):
        tk.Frame(card, bg=DIVIDER, height=1).grid(
            row=row, column=0, columnspan=2,
            sticky="ew", padx=10, pady=2)

    # ── build ──────────────────────────────────────────────────

    def _build(self):
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True)

        self._sbar = ttk.Scrollbar(container, orient="vertical")
        self._sbar.pack(side="right", fill="y")

        self._scanvas = tk.Canvas(
            container, bg=BG, highlightthickness=0,
            yscrollcommand=self._sbar.set)
        self._scanvas.pack(side="left", fill="both", expand=True)
        self._sbar.config(command=self._scanvas.yview)

        f = tk.Frame(self._scanvas, bg=BG)
        self._cw = self._scanvas.create_window(
            (0, 0), window=f, anchor="nw")

        f.bind("<Configure>",
               lambda e: self._scanvas.configure(
                   scrollregion=self._scanvas.bbox("all")))
        self._scanvas.bind("<Configure>",
                           self._on_canvas_resize)
        self._scanvas.bind_all("<MouseWheel>",
                               self._on_mousewheel)

        tk.Label(f, text="Hertz Forge", bg=BG, fg=ACCENT,
                 font=("Helvetica", 18, "bold")).pack(
                     anchor="w", padx=12, pady=(10, 0))
        tk.Label(f, text="Brainwave Entrainment Generator",
                 bg=BG, fg=MUTED,
                 font=("Helvetica", 9)).pack(
                     anchor="w", padx=12)
        self._sep(f)

        # ── OUTPUT DEVICE ──
        self._section(f, "OUTPUT DEVICE")
        df = tk.Frame(f, bg=BG); df.pack(fill="x", padx=8, pady=2)
        self.device_names = [d[0] for d in self.output_devices]
        if not self.device_names:
            self.device_names = ["(no devices)"]
        self.device_var = tk.StringVar(
            value=self.device_names[0])
        self.dev_cb = ttk.Combobox(
            df, textvariable=self.device_var,
            values=self.device_names,
            state="readonly", width=34)
        self.dev_cb.pack(side="left", fill="x", expand=True)
        self.dev_cb.bind("<<ComboboxSelected>>",
                         lambda _: self._apply_device())
        ttk.Button(df, text="Test Stereo",
                   style="Test.TButton",
                   command=self._test_stereo).pack(
                       side="right", padx=(6, 0))
        self.device_info = tk.Label(f, text="", bg=BG, fg=MUTED,
                                    font=("Helvetica", 8))
        self.device_info.pack(anchor="w", padx=12)
        self._sep(f)

        # ── FREQUENCIES ──
        self._section(f, "FREQUENCIES")
        card = self._card(f)

        c0 = self._col(card, 0, 0)
        self._col_label(c0, "CARRIER")
        tk.Label(c0, text="Frequency", bg=CARD, fg=MUTED,
                 font=("Helvetica", 8)).pack(
                     anchor="w", pady=(4, 0))
        _, self.carrier_spin, self._carrier_var = \
            self._slider_row(
                c0, 40, 1000, 1, "{:.0f}", "110", "Hz",
                self._on_carrier)
        self._carrier_var.trace_add("write",
                                    self._on_carrier_var)
        tk.Label(c0, text="Waveform", bg=CARD, fg=MUTED,
                 font=("Helvetica", 8)).pack(
                     anchor="w", pady=(4, 0))
        wf = tk.Frame(c0, bg=CARD); wf.pack(fill="x", pady=2)
        self.wave_var = tk.StringVar(value="sine")
        cb = ttk.Combobox(wf, textvariable=self.wave_var,
                          values=WAVES, state="readonly",
                          width=10)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>",
                lambda _: setattr(self.eng, "wave",
                                  self.wave_var.get()))

        c1 = self._col(card, 0, 1)
        self._col_label(c1, "BRAINWAVE FREQUENCY")
        self.bw_label = tk.Label(
            c1, text="40.0 Hz — Gamma", bg=CARD, fg=ACCENT,
            font=("Helvetica", 10, "bold"), anchor="w")
        self.bw_label.pack(fill="x", pady=(2, 0))
        tk.Label(c1, text="Frequency", bg=CARD, fg=MUTED,
                 font=("Helvetica", 8)).pack(
                     anchor="w", pady=(4, 0))
        _, self.bw_spin, self._bw_var = self._slider_row(
            c1, 0, 100, 0.5, "{:.1f}", "40.0", "Hz",
            self._on_bw)
        self._bw_var.trace_add("write", self._on_bw_var)
        pf = tk.Frame(c1, bg=CARD); pf.pack(fill="x", pady=(4, 0))
        for band, freq in BW_PRESETS:
            b = tk.Button(
                pf, text=f"{band}{freq}",
                font=("Helvetica", 8), bg=SURFACE2, fg=MUTED,
                activebackground=ACCENT2,
                activeforeground=ACCENT,
                relief="flat", bd=0, padx=4, pady=1,
                cursor="hand2",
                command=lambda f=freq: self._preset_bw(f))
            b.pack(side="left", padx=1)
            b.bind("<Enter>",
                   lambda e, bt=b: bt.config(fg=ACCENT))
            b.bind("<Leave>",
                   lambda e, bt=b: bt.config(fg=MUTED))

        self._sep(f)

        # ── MODULATION ──
        self._section(f, "MODULATION")
        card2 = self._card(f)

        c00 = self._col(card2, 0, 0)
        self._col_label(c00, "AMPLITUDE")
        _, self.amp_spin, self._amp_var = self._slider_row(
            c00, 0, 100, 1, "{:.0f}", "100", "",
            self._on_amp)
        self._amp_var.trace_add("write", self._on_amp_var)
        self._col_hint(c00, "0% flat · 50% half · 100% on/off")

        c01 = self._col(card2, 0, 1)
        self._col_label(c01, "BILATERAL PAN.")
        _, self.bi_spin, self._bi_var = self._slider_row(
            c01, 0, 100, 1, "{:.0f}", "0", "",
            self._on_bi)
        self._bi_var.trace_add("write", self._on_bi_var)
        self._col_hint(c01, "Higher = harder L/R switch")

        self._divider_row(card2, 1)

        c10 = self._col(card2, 2, 0)
        self._col_label(c10, "BINAURAL BEATS")
        brow = tk.Frame(c10, bg=CARD); brow.pack(fill="x", pady=2)
        self.binaural_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            brow, variable=self.binaural_var, text="on",
            bg=CARD, fg=ACCENT, selectcolor=SURFACE2,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 10, "bold"),
            command=self._on_binaural).pack(side="left")
        self.bin_left_lbl = tk.Label(
            brow, text="L: 90.0 Hz", bg=CARD, fg=ACCENT,
            font=("Helvetica", 9, "bold"))
        self.bin_left_lbl.pack(side="left", padx=(6, 0))
        tk.Label(brow, text=" — ",
                 bg=CARD, fg=MUTED).pack(side="left")
        self.bin_right_lbl = tk.Label(
            brow, text="R: 130.0 Hz", bg=CARD, fg=ACCENT,
            font=("Helvetica", 9, "bold"))
        self.bin_right_lbl.pack(side="left")
        self._col_hint(c10, "Headphones required")

        c11 = self._col(card2, 2, 1)
        self._col_label(c11, "FREQ MODULATION")
        frow = tk.Frame(c11, bg=CARD); frow.pack(fill="x", pady=2)
        self.fm_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            frow, variable=self.fm_var, text="on",
            bg=CARD, fg=ACCENT, selectcolor=SURFACE2,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 10, "bold"),
            command=self._on_fm).pack(side="left")
        srow = tk.Frame(c11, bg=CARD)
        srow.pack(fill="x", pady=(2, 0))
        self.fm_lo_spin = SpinEntry(
            srow, width=6, from_=20, to=2000, step=1,
            fmt="{:.0f}", initial="80", suffix="Hz",
            callback=self._on_fm_lo, bg=CARD)
        self.fm_lo_spin.pack(side="left")
        tk.Label(srow, text=" — ",
                 bg=CARD, fg=MUTED).pack(side="left")
        self.fm_hi_spin = SpinEntry(
            srow, width=6, from_=20, to=2000, step=1,
            fmt="{:.0f}", initial="150", suffix="Hz",
            callback=self._on_fm_hi, bg=CARD)
        self.fm_hi_spin.pack(side="left")
        self._col_hint(c11, "Modulates carrier")

        self._sep(f)

        # ── VISUALISER ──
        vis_frame = tk.Frame(f, bg=BG)
        vis_frame.pack(fill="x", padx=8, pady=4)
        tk.Label(vis_frame, text="VISUALISER", bg=BG,
                 fg="#6666a0",
                 font=("Helvetica", 9, "bold")).pack(
                     side="left")
        self._draw_var = tk.BooleanVar(value=False)
        self._draw_btn = tk.Checkbutton(
            vis_frame, variable=self._draw_var, text="off",
            bg=BG, fg=MUTED, selectcolor=SURFACE2,
            activebackground=BG,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold"),
            command=self._toggle_draw)
        self._draw_btn.pack(side="left", padx=(8, 0))

        self.canvas = tk.Canvas(f, bg="#060610", height=80,
                                highlightthickness=1,
                                highlightbackground="#1a1a36")
        self.canvas.pack(fill="x", padx=8, pady=4)
        self._sep(f)

        # ── OUTPUT ──
        self._section(f, "OUTPUT")
        card3 = self._card(f)

        ct0 = self._col(card3, 0, 0)
        self._col_label(ct0, "TRANSPORT")
        self.play_btn = ttk.Button(
            ct0, text="▶  Play", style="Play.TButton",
            command=self._toggle)
        self.play_btn.pack(anchor="w", pady=(6, 0))
        self.time_lbl = tk.Label(
            ct0, text="00:00:00", bg=CARD, fg=ACCENT,
            font=("Courier", 14, "bold"))
        self.time_lbl.pack(anchor="w", pady=(6, 0))
        self.status = tk.Label(ct0, text="Stopped",
                               bg=CARD, fg=MUTED,
                               font=("Helvetica", 9))
        self.status.pack(anchor="w")

        ct1 = self._col(card3, 0, 1)
        self._col_label(ct1, "SAVE WAV")
        ttk.Button(ct1, text="Export…",
                   command=self._save).pack(
                       anchor="w", pady=(6, 0))
        dd = tk.Frame(ct1, bg=CARD); dd.pack(fill="x", pady=(6, 0))
        self._dur_h = SpinEntry(
            dd, width=3, from_=0, to=23, step=1,
            fmt="{:02d}", initial="00", suffix="h", bg=CARD)
        self._dur_h.pack(side="left")
        self._dur_m = SpinEntry(
            dd, width=3, from_=0, to=59, step=1,
            fmt="{:02d}", initial="00", suffix="m", bg=CARD)
        self._dur_m.pack(side="left", padx=(2, 0))
        self._dur_s = SpinEntry(
            dd, width=3, from_=0, to=59, step=1,
            fmt="{:02d}", initial="30", suffix="s", bg=CARD)
        self._dur_s.pack(side="left", padx=(2, 0))
        pp = tk.Frame(ct1, bg=CARD); pp.pack(fill="x", pady=(2, 0))
        for label, h, m, s in [("1m",0,1,0),("2m",0,2,0),
                                ("5m",0,5,0),("10m",0,10,0),
                                ("30m",0,30,0),("1h",1,0,0)]:
            b = tk.Button(
                pp, text=label, font=("Helvetica", 8),
                bg=SURFACE2, fg=MUTED,
                activebackground=ACCENT2,
                activeforeground=ACCENT,
                relief="flat", bd=0, padx=4, pady=1,
                cursor="hand2",
                command=lambda h=h,m=m,s=s:
                    self._set_dur(h, m, s))
            b.pack(side="left", padx=1)
            b.bind("<Enter>",
                   lambda e, bt=b: bt.config(fg=ACCENT))
            b.bind("<Leave>",
                   lambda e, bt=b: bt.config(fg=MUTED))

        self._sep(f)

        # ── VOLUME ──
        self._section(f, "VOLUME")
        vf = tk.Frame(f, bg=BG)
        vf.pack(fill="x", padx=8, pady=2)
        tk.Label(vf, text="Level", bg=BG, fg="#8888aa",
                 font=("Helvetica", 10), width=10,
                 anchor="w").pack(side="left")
        _, self.vol_spin, self._vol_var = self._slider_row(
            vf, 0, 100, 1, "{:.0f}", "50", "%",
            self._on_vol, bg=BG)
        self._vol_var.trace_add("write", self._on_vol_var)

        tk.Frame(f, bg=BG, height=20).pack()

    # ── scroll ─────────────────────────────────────────────────

    def _on_canvas_resize(self, event):
        self._scanvas.itemconfig(self._cw, width=event.width)

    def _on_mousewheel(self, event):
        self._scanvas.yview_scroll(
            int(-1 * (event.delta / 120)), "units")

    # ══════════════════════════════════════════════════════════
    #  SLIDER ↔ SPIN SYNC
    # ══════════════════════════════════════════════════════════

    def _on_carrier_var(self, *_):
        try:
            v = float(self._carrier_var.get())
            self.carrier_spin.set(v); self.eng.carrier = v
            self._update_fm_display()
            self._update_binaural_display()
        except:
            pass

    def _on_carrier(self, v):
        self.eng.carrier = v; self._carrier_var.set(v)
        self._update_fm_display()
        self._update_binaural_display()

    def _on_bw_var(self, *_):
        try:
            v = float(self._bw_var.get())
            self.bw_spin.set(v); self.eng.bw_freq = v
            self._update_bw_label()
            self._update_binaural_display()
        except:
            pass

    def _on_bw(self, v):
        self.eng.bw_freq = v; self._bw_var.set(v)
        self._update_bw_label()
        self._update_binaural_display()

    def _on_amp_var(self, *_):
        try:
            v = float(self._amp_var.get())
            self.amp_spin.set(v); self.eng.amp_val = v
        except:
            pass

    def _on_amp(self, v):
        self.eng.amp_val = v; self._amp_var.set(v)

    def _on_bi_var(self, *_):
        try:
            v = float(self._bi_var.get())
            self.bi_spin.set(v); self.eng.bi_val = v
        except:
            pass

    def _on_bi(self, v):
        self.eng.bi_val = v; self._bi_var.set(v)

    def _on_vol_var(self, *_):
        try:
            v = float(self._vol_var.get())
            self.vol_spin.set(v); self.eng.vol = v / 100.0
        except:
            pass

    def _on_vol(self, v):
        self.eng.vol = v / 100.0; self._vol_var.set(v)

    # ══════════════════════════════════════════════════════════
    #  OTHER CALLBACKS
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def _band_for(freq):
        for lo, hi, name in BAND_LABELS:
            if lo <= freq < hi:
                return name
        return ""

    def _update_bw_label(self):
        f = self.bw_spin.get(); b = self._band_for(f)
        if f <= 0:
            self.bw_label.config(text="0.0 Hz — Constant")
        else:
            self.bw_label.config(
                text=f"{f:.1f} Hz"
                     f"{(' — ' + b) if b else ''}")

    def _update_fm_display(self):
        self.fm_lo_spin.set(
            self.eng.carrier + self.eng.fm_offset_lo)
        self.fm_hi_spin.set(
            self.eng.carrier + self.eng.fm_offset_hi)

    def _update_binaural_display(self):
        self.bin_left_lbl.config(
            text=f"L: "
                 f"{self.eng.carrier - self.eng.bw_freq / 2:.1f}"
                 f" Hz")
        self.bin_right_lbl.config(
            text=f"R: "
                 f"{self.eng.carrier + self.eng.bw_freq / 2:.1f}"
                 f" Hz")

    def _preset_bw(self, freq):
        self.bw_spin.set(freq); self._bw_var.set(freq)
        self.eng.bw_freq = freq
        self._update_bw_label()
        self._update_binaural_display()

    def _set_dur(self, h, m, s):
        self._dur_h.set(h); self._dur_m.set(m)
        self._dur_s.set(s)

    def _on_binaural(self):
        self.eng.binaural_on = bool(self.binaural_var.get())

    def _on_fm(self):
        self.eng.fm_on = bool(self.fm_var.get())

    def _on_fm_lo(self, v):
        self.eng.fm_offset_lo = v - self.eng.carrier

    def _on_fm_hi(self, v):
        self.eng.fm_offset_hi = v - self.eng.carrier

    # ── device ─────────────────────────────────────────────────

    def _apply_device(self):
        idx = self.dev_cb.current()
        if idx < 0 or idx >= len(self.output_devices):
            self.eng.device_index = None
            self.eng.channels = 2
            self.device_info.config(text="Using system default")
            return
        _, di, mch = self.output_devices[idx]
        self.eng.device_index = di
        self.eng.channels = min(mch, 2)
        c = self.eng.channels
        self.device_info.config(
            text=f"Device #{di} — {c}ch"
                 + (" · mono" if c == 1 else ""))

    def _test_stereo(self):
        self.status.config(text="Testing stereo…")
        self.root.update()
        idx = self.eng.device_index; ch = self.eng.channels

        def go():
            try:
                test_device_stereo(idx, ch)
            except Exception as e:
                self.root.after(0, lambda:
                    messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda:
                self.status.config(text="Stereo test done"))

        threading.Thread(target=go, daemon=True).start()

    # ── visualiser ─────────────────────────────────────────────

    def _toggle_draw(self):
        self._draw_on = bool(self._draw_var.get())
        if self._draw_on:
            self._draw_btn.config(text="on", fg=ACCENT)
        else:
            self._draw_btn.config(text="off", fg=MUTED)
            self.canvas.delete("all")

    # ── transport ──────────────────────────────────────────────

    def _apply_params(self):
        self._apply_device()
        self.eng.carrier = self.carrier_spin.get()
        self.eng.wave    = self.wave_var.get()
        self.eng.bw_freq = self.bw_spin.get()
        self.eng.amp_val = self.amp_spin.get()
        self.eng.bi_val  = self.bi_spin.get()
        self.eng.binaural_on = bool(self.binaural_var.get())
        self.eng.fm_on   = bool(self.fm_var.get())
        self.eng.fm_offset_lo = (
            self.fm_lo_spin.get() - self.eng.carrier)
        self.eng.fm_offset_hi = (
            self.fm_hi_spin.get() - self.eng.carrier)
        self.eng.vol = self.vol_spin.get() / 100.0

    def _toggle(self):
        if self.eng.playing:
            self.eng.stop()
            self.play_btn.config(text="▶  Play")
            self.status.config(text="Stopped")
        else:
            self._apply_params()
            try:
                self.eng.start()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return
            self.play_btn.config(text="■  Stop")
            self.status.config(text="Playing")

    def _save(self):
        duration = (int(self._dur_h.get()) * 3600
                    + int(self._dur_m.get()) * 60
                    + int(self._dur_s.get()))
        if duration <= 0:
            messagebox.showwarning("Duration",
                                   "Set export duration > 0")
            return

        dh = int(self._dur_h.get())
        dm = int(self._dur_m.get())
        ds = int(self._dur_s.get())
        dur_str = f"{dh:02d}:{dm:02d}:{ds:02d}"

        self._apply_params()

        # auto filename
        parts = ["hertzforge"]
        parts.append(f"{int(self.eng.carrier)}hz")
        parts.append(f"{self.eng.bw_freq:.0f}bw")
        parts.append(self.eng.wave)
        if self.eng.binaural_on:
            parts.append("binaural")
        if self.eng.fm_on:
            parts.append("fm")
        if self.eng.amp_val > 0:
            parts.append(f"amp{int(self.eng.amp_val)}")
        if self.eng.bi_val > 0:
            parts.append(f"bi{int(self.eng.bi_val)}")
        parts.append(dur_str.replace(":", ""))
        filename = "_".join(parts) + ".wav"

        path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV", "*.wav")],
            initialfile=filename)
        if not path:
            return

        self.status.config(text=f"Saving {dur_str}…")
        self.root.update()

        def go():
            self.eng.save_wav(path, duration=duration)
            mb = os.path.getsize(path) / (1024 * 1024)
            self.root.after(0, lambda:
                self.status.config(
                    text=f"Saved {dur_str} ({mb:.1f} MB)"))

        threading.Thread(target=go, daemon=True).start()

    # ── tick ───────────────────────────────────────────────────

    def _tick(self):
        e = int(self.eng.elapsed())
        m, s = divmod(e, 60); h, m = divmod(m, 60)
        self.time_lbl.config(
            text=f"{h:02d}:{m:02d}:{s:02d}")
        if self._draw_on:
            self._draw()
        self.root.after(80, self._tick)

    def _draw(self):
        c = self.canvas; w = c.winfo_width(); h = c.winfo_height()
        if w < 10:
            return
        c.delete("all"); cy = h // 2
        for y in range(0, h, 16):
            c.create_line(0, y, w, y, fill=GRID, width=1)
        c.create_line(0, cy, w, cy, fill="#161630",
                      dash=(3, 3))
        prev = self.eng.preview(n=4096)
        mono = (prev[:, 0] + prev[:, 1]) * 0.5
        npts = min(len(mono), w * 2)
        idx  = np.linspace(0, len(mono) - 1, npts).astype(int)
        pts  = []
        for i, s in enumerate(mono[idx]):
            pts.extend([i * w / npts, cy - s * (h / 2 - 4)])
        if len(pts) >= 4:
            c.create_line(*pts, fill="#082a1e", width=4,
                          smooth=True, capstyle="round")
            c.create_line(*pts, fill=ACCENT2, width=1.5,
                          smooth=True, capstyle="round")
            c.create_line(*pts, fill=ACCENT, width=0.8,
                          smooth=True, capstyle="round")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self.root.mainloop()

    def _quit(self):
        if self.eng.playing:
            self.eng.stop()
        self.root.destroy()