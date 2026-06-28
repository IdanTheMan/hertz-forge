# ═══════════════════════════════════════════════════════════════
#  GUI — loop & shuffle at row and playlist level
# ═══════════════════════════════════════════════════════════════

import os
import sys
import random

_root = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

from hertz_forge.constants import (
    WAVES, BG, SURFACE, SURFACE2,
    ACCENT, ACCENT2, MUTED, FG,
    DIVIDER, CARD, SLIDER_LEN)
from hertz_forge.widgets import SpinEntry
from hertz_forge.audio import (
    get_output_devices, test_device_stereo)
from .engine import PlaylistEngine, Playlist

_LABEL_PX = 75

_BODY_KEYS = {
    "left_carrier_spin", "left_wave_var",
    "left_bw_spin", "left_amp_spin",
    "right_carrier_spin", "right_wave_var",
    "right_bw_spin", "right_amp_spin",
    "bi_l_lbl", "bi_r_lbl",
    "l_indicator", "r_indicator",
}

_ADV_KEYS = {
    "fm_l_lo", "fm_l_hi",
    "fm_r_lo", "fm_r_hi",
    "left_bi_spin", "right_bi_spin",
    "left_fm_var", "right_fm_var",
}


class App:

    def __init__(self):
        self._playlists    = []
        self._containers   = []
        self.eng           = PlaylistEngine()
        self.output_devices = get_output_devices()
        self._playing_cont = None

        # playlist-level loop/shuffle
        self._pl_loop       = False
        self._pl_shuffle    = False
        self._pl_play_order = []

        self.root = tk.Tk()
        self.root.title("Hertz Forge — Playlists")
        self.root.geometry("700x720")
        self.root.minsize(620, 360)
        self.root.configure(bg=BG)

        self._style()
        self._build()
        self._apply_device()
        self._add_playlist("Playlist 1")
        self._tick()

    # ── style ─────────────────────────────────────────────────

    def _style(self):
        self.root.option_add(
            "*TCombobox*Listbox.background",
            SURFACE)
        self.root.option_add(
            "*TCombobox*Listbox.foreground",
            FG)
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
            troughcolor=SURFACE2,
            borderwidth=0)
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

    # ── helpers ────────────────────────────────────────────────

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

    def _label_row(self, parent, text,
                   bg=CARD):
        r = tk.Frame(parent, bg=bg)
        r.pack(fill="x", pady=1)
        r.columnconfigure(0, minsize=_LABEL_PX)
        self._lbl(r, text, bg=bg)
        return r

    # ── main build ─────────────────────────────────────────────

    def _build(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=4, pady=(8, 0))

        tk.Label(
            top, text="Hertz Forge",
            bg=BG, fg=ACCENT,
            font=("Helvetica", 18, "bold")
        ).pack(anchor="w", padx=12,
               pady=(10, 0))
        tk.Label(
            top,
            text=("Playlist Mode — "
                  "Sequential Brainwaves"),
            bg=BG, fg=MUTED,
            font=("Helvetica", 9)
        ).pack(anchor="w", padx=12)
        self._sep(top)

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
            bottom, bg=BG, highlightthickness=0,
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
            lambda e: self._scanvas.configure(
                scrollregion=(
                    self._scanvas.bbox("all"))))
        self._scanvas.bind(
            "<Configure>",
            self._on_canvas_resize)
        self._scanvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel)

        # ── PLAYLISTS header with controls ──
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
        ttk.Button(
            btn_f, text="+ Playlist",
            style="Small.TButton",
            command=self._add_playlist
        ).pack(anchor="center")

        tk.Frame(
            self._inner, bg=BG, height=20
        ).pack()

    # ══════════════════════════════════════════════════════════
    #  PLAYLIST-LEVEL LOOP / SHUFFLE
    # ══════════════════════════════════════════════════════════

    def _toggle_pl_loop(self):
        self._pl_loop = self._pl_loop_var.get()

    def _toggle_pl_shuffle(self):
        self._pl_shuffle = \
            self._pl_shuffle_var.get()
        self._rebuild_pl_order()

    def _rebuild_pl_order(self):
        self._pl_play_order = list(
            range(len(self._containers)))
        if self._pl_shuffle:
            random.shuffle(
                self._pl_play_order)

    # ══════════════════════════════════════════════════════════
    #  PLAYLIST CONTAINERS
    # ══════════════════════════════════════════════════════════

    def _add_playlist(self, name=None):
        if name is None:
            n = len(self._playlists) + 1
            name = f"Playlist {n}"
        pl = Playlist(name=name)
        self._playlists.append(pl)
        self._create_pl_container(
            len(self._playlists) - 1)
        self._rebuild_pl_order()

    def _remove_playlist(self, container):
        ci = self._containers.index(container)
        if len(self._playlists) <= 1:
            messagebox.showinfo(
                "Playlist",
                "Keep at least one playlist.")
            return
        if self._playing_cont is container:
            self._stop_current()
        self._playlists.pop(ci)
        self._containers.pop(ci)
        container["frame"].destroy()
        for i, c in enumerate(
                self._containers):
            c["name_lbl"].config(
                text=f"Playlist {i + 1}")
        self._rebuild_pl_order()

    def _create_pl_container(self, ci):
        pl = self._playlists[ci]

        frame = tk.Frame(
            self._pl_frame, bg=CARD,
            highlightthickness=2,
            highlightbackground="#333355")
        frame.pack(
            fill="x", padx=4, pady=6, ipady=4)

        # ── line 1: name + delete ──
        h1 = tk.Frame(frame, bg=CARD)
        h1.pack(fill="x", padx=8, pady=(6, 0))

        name_lbl = tk.Label(
            h1, text=pl.name, bg=CARD,
            fg=ACCENT,
            font=("Helvetica", 11, "bold"))
        name_lbl.pack(side="left")

        tk.Button(
            h1, text="×",
            font=("Helvetica", 11, "bold"),
            bg=CARD, fg="#cc6666",
            activebackground="#442222",
            activeforeground="#cc6666",
            relief="flat", bd=0, padx=6,
            cursor="hand2"
        ).pack(side="right")

        # ── line 2: controls ──
        h2 = tk.Frame(frame, bg=CARD)
        h2.pack(fill="x", padx=8, pady=(4, 0))

        play_btn = tk.Button(
            h2, text="▶  Play",
            font=("Helvetica", 10, "bold"),
            bg=SURFACE2, fg=ACCENT,
            activebackground=ACCENT2,
            activeforeground=ACCENT,
            relief="flat", bd=0,
            padx=6, pady=2,
            cursor="hand2")
        play_btn.pack(side="left")

        export_btn = tk.Button(
            h2, text="Export…",
            font=("Helvetica", 9),
            bg=SURFACE2, fg=MUTED,
            activebackground=ACCENT2,
            activeforeground=ACCENT,
            relief="flat", bd=0,
            padx=4, pady=2,
            cursor="hand2")
        export_btn.pack(
            side="left", padx=(8, 0))

        # row loop
        row_loop_var = tk.BooleanVar(
            value=pl.row_loop)
        tk.Checkbutton(
            h2, variable=row_loop_var,
            text="loop",
            bg=CARD, fg=ACCENT,
            selectcolor=SURFACE2,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 8, "bold"),
            command=lambda: setattr(
                pl, 'row_loop',
                row_loop_var.get())
        ).pack(side="left", padx=(10, 0))

        # row shuffle
        row_shuffle_var = tk.BooleanVar(
            value=pl.row_shuffle)
        tk.Checkbutton(
            h2, variable=row_shuffle_var,
            text="shuffle",
            bg=CARD, fg=ACCENT,
            selectcolor=SURFACE2,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 8, "bold"),
            command=lambda: (
                setattr(pl, 'row_shuffle',
                        row_shuffle_var.get()),
                pl._rebuild_order())
        ).pack(side="left", padx=(4, 0))

        status_lbl = tk.Label(
            h2, text="● Stopped",
            bg=CARD, fg=MUTED,
            font=("Helvetica", 9))
        status_lbl.pack(
            side="left", padx=(12, 0))

        total_lbl = tk.Label(
            h2, text="Total: 00:00",
            bg=CARD, fg=MUTED,
            font=("Helvetica", 9))
        total_lbl.pack(
            side="left", padx=(12, 0))

        # ── line 3: playback info ──
        h3 = tk.Frame(frame, bg=CARD)
        h3.pack(fill="x", padx=8, pady=(2, 0))

        time_lbl = tk.Label(
            h3, text="", bg=CARD, fg=ACCENT,
            font=("Courier", 12, "bold"))
        time_lbl.pack(side="left")

        row_ind = tk.Label(
            h3, text="", bg=CARD, fg=ACCENT,
            font=("Helvetica", 9, "bold"))
        row_ind.pack(
            side="left", padx=(12, 0))

        self._sep(frame)

        # ── rows area ──
        rows_frame = tk.Frame(frame, bg=CARD)
        rows_frame.pack(
            fill="x", padx=4, pady=(2, 0))

        container = {
            "playlist":   pl,
            "frame":      frame,
            "name_lbl":   name_lbl,
            "play_btn":   play_btn,
            "export_btn": export_btn,
            "status_lbl": status_lbl,
            "total_lbl":  total_lbl,
            "time_lbl":   time_lbl,
            "row_ind":    row_ind,
            "rows_frame": rows_frame,
            "slots":      [],
        }
        self._containers.append(container)

        # wire buttons
        h1.winfo_children()[-1].config(
            command=lambda c=container:
                self._remove_playlist(c))
        play_btn.config(
            command=lambda c=container:
                self._toggle_pl(c))
        export_btn.config(
            command=lambda c=container:
                self._save_pl(c))

        for i in range(len(pl.rows)):
            self._create_slot(container, i)

        # + row
        rf = tk.Frame(frame, bg=CARD)
        rf.pack(
            fill="x", padx=4, pady=(6, 2))
        ttk.Button(
            rf, text="+ row",
            style="Small.TButton",
            command=lambda c=container:
                self._add_row(c)
        ).pack(anchor="center")

        self._update_pl_dur(container)

    # ══════════════════════════════════════════════════════════
    #  ROW MANAGEMENT
    # ══════════════════════════════════════════════════════════

    def _add_row(self, container):
        container["playlist"].add_row()
        idx = (len(container["playlist"].rows)
               - 1)
        self._create_slot(container, idx)
        self._update_pl_dur(container)

    def _remove_row(self, container, row_idx):
        container["playlist"].remove_row(
            row_idx)
        slot = container["slots"].pop(row_idx)
        slot["border"].destroy()
        self._renumber(container)
        self._update_pl_dur(container)

    def _renumber(self, container):
        for i, slot in enumerate(
                container["slots"]):
            slot["num_lbl"].config(
                text=f"Row {i + 1}")

    def _update_pl_dur(self, container):
        total = (
            container["playlist"]
            .total_duration())
        e = int(total)
        s = e % 60
        m = (e // 60) % 60
        h = e // 3600
        if h > 0:
            container["total_lbl"].config(
                text=(
                    f"Total: {h:02d}:"
                    f"{m:02d}:{s:02d}"))
        else:
            container["total_lbl"].config(
                text=(
                    f"Total: "
                    f"{m:02d}:{s:02d}"))

    def _on_remove_click(self, container,
                         border_frame):
        for i, slot in enumerate(
                container["slots"]):
            if slot["border"] is border_frame:
                self._remove_row(container, i)
                return

    # ══════════════════════════════════════════════════════════
    #  ACTIVE ROW
    # ══════════════════════════════════════════════════════════

    def _set_active_row(self, playing_cont,
                        row_idx):
        for container in self._containers:
            for ri, slot in enumerate(
                    container["slots"]):
                active = (
                    container is playing_cont
                    and ri == row_idx)
                if active == slot.get("_active"):
                    continue
                slot["_active"] = active

                slot["border"].config(
                    bg=(ACCENT if active
                        else "#222244"))
                slot["num_lbl"].config(
                    fg=(ACCENT if active
                        else MUTED))
                l_ind = slot.get("l_indicator")
                if l_ind:
                    l_ind.config(
                        fg=(ACCENT if active
                            else CARD),
                        bg=(ACCENT if active
                            else CARD))
                r_ind = slot.get("r_indicator")
                if r_ind:
                    r_ind.config(
                        fg=(ACCENT if active
                            else CARD),
                        bg=(ACCENT if active
                            else CARD))

    # ══════════════════════════════════════════════════════════
    #  SYNC — core
    # ══════════════════════════════════════════════════════════

    def _apply_sync(self, slot, source_side):
        cfg = slot["config"]
        if not slot["sync_var"].get():
            return
        src = (cfg.left
               if source_side == "left"
               else cfg.right)
        dst = (cfg.right
               if source_side == "left"
               else cfg.left)
        dk = ("right"
              if source_side == "left"
              else "left")
        dst.carrier = src.carrier
        dst.wave    = src.wave
        dst.bw_freq = src.bw_freq
        dst.amp_val = src.amp_val
        for attr, field in [
                ("carrier", "carrier_spin"),
                ("bw_freq", "bw_spin"),
                ("amp_val", "amp_spin")]:
            sp = slot.get(f"{dk}_{field}")
            if sp:
                sp.set(getattr(src, attr))
        wv = slot.get(f"{dk}_wave_var")
        if wv:
            wv.set(src.wave)

    # ══════════════════════════════════════════════════════════
    #  SYNC — advanced
    # ══════════════════════════════════════════════════════════

    def _apply_adv_sync(self, slot,
                        source_side):
        cfg = slot["config"]
        if not slot["sync_var"].get():
            return
        src = (cfg.left
               if source_side == "left"
               else cfg.right)
        dst = (cfg.right
               if source_side == "left"
               else cfg.left)
        d_side = ("right"
                  if source_side == "left"
                  else "left")
        s_fk = ("l" if source_side == "left"
                else "r")
        d_fk = ("r" if source_side == "left"
                else "l")

        dst.bi_val       = src.bi_val
        dst.fm_on        = src.fm_on
        dst.fm_offset_lo = src.fm_offset_lo
        dst.fm_offset_hi = src.fm_offset_hi

        sp = slot.get(f"{d_side}_bi_spin")
        if sp:
            sp.set(src.bi_val)
        fv = slot.get(f"{d_side}_fm_var")
        if fv:
            fv.set(src.fm_on)
        s_lo = slot.get(f"fm_{s_fk}_lo")
        s_hi = slot.get(f"fm_{s_fk}_hi")
        d_lo = slot.get(f"fm_{d_fk}_lo")
        d_hi = slot.get(f"fm_{d_fk}_hi")
        if d_lo and s_lo:
            d_lo.set(s_lo.get())
        if d_hi and s_hi:
            d_hi.set(s_hi.get())

    # ══════════════════════════════════════════════════════════
    #  SLOT CREATION
    # ══════════════════════════════════════════════════════════

    def _create_slot(self, container, index):
        cfg = container["playlist"].rows[index]
        rows_frame = container["rows_frame"]

        border = tk.Frame(
            rows_frame, bg="#222244")
        border.pack(fill="x", padx=4, pady=4)

        card = tk.Frame(border, bg=CARD)
        card.pack(fill="x", padx=1, pady=1)

        # ── header ──
        hdr = tk.Frame(card, bg=CARD)
        hdr.pack(fill="x", padx=8, pady=(4, 0))
        num_lbl = tk.Label(
            hdr, text=f"Row {index + 1}",
            bg=CARD, fg=ACCENT,
            font=("Helvetica", 10, "bold"))
        num_lbl.pack(side="left")
        tk.Button(
            hdr, text="×",
            font=("Helvetica", 11, "bold"),
            bg=CARD, fg="#cc6666",
            activebackground="#442222",
            activeforeground="#cc6666",
            relief="flat", bd=0, padx=6,
            cursor="hand2",
            command=lambda sf=border,
                           c=container:
                self._on_remove_click(c, sf)
        ).pack(side="right")

        # ── body ──
        body = tk.Frame(card, bg=CARD)
        body.pack(
            fill="x", padx=6, pady=(4, 0))

        # ── advanced wrap ──
        adv_wrap = tk.Frame(card, bg=CARD)

        # ── controls row ──
        ctrl = tk.Frame(card, bg=CARD)
        ctrl.pack(
            fill="x", padx=8, pady=(4, 4))

        sync_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            ctrl, variable=sync_var,
            text="sync",
            bg=CARD, fg=ACCENT,
            selectcolor=SURFACE2,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold")
        ).pack(side="left")

        bin_var = tk.BooleanVar(
            value=cfg.binaural_on)
        tk.Checkbutton(
            ctrl, variable=bin_var,
            text="binaural",
            bg=CARD, fg=ACCENT,
            selectcolor=SURFACE2,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold")
        ).pack(side="left", padx=(8, 0))

        tk.Label(
            ctrl, text="Duration",
            bg=CARD, fg="#8888aa",
            font=("Helvetica", 8, "bold")
        ).pack(side="left", padx=(12, 0))

        def on_dur(v):
            cfg.duration = v
            self._update_pl_dur(container)

        dur_spin = SpinEntry(
            ctrl, width=5, from_=0,
            to=36000, step=5, fmt="{:.0f}",
            initial=str(int(cfg.duration)),
            suffix="s", bg=CARD,
            callback=on_dur)
        dur_spin.pack(
            side="left", padx=(4, 0))

        tk.Frame(ctrl, bg=CARD).pack(
            side="left", fill="x", expand=True)

        adv_var = tk.BooleanVar(value=False)
        adv_btn = tk.Checkbutton(
            ctrl, variable=adv_var,
            text="Advanced ▸",
            bg=CARD, fg=MUTED,
            selectcolor=CARD,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 8))
        adv_btn.pack(side="right")

        slot = {
            "border":   border,
            "frame":    card,
            "body":     body,
            "adv_wrap": adv_wrap,
            "config":   cfg,
            "num_lbl":  num_lbl,
            "sync_var": sync_var,
            "bin_var":  bin_var,
            "dur_spin": dur_spin,
            "_active":  False,
        }
        container["slots"].append(slot)

        # ── helpers ──
        def _mirror_l_to_r():
            cfg.right.carrier = cfg.left.carrier
            cfg.right.wave    = cfg.left.wave
            cfg.right.bw_freq = cfg.left.bw_freq
            cfg.right.amp_val = cfg.left.amp_val
            for attr, field in [
                    ("carrier","carrier_spin"),
                    ("bw_freq","bw_spin"),
                    ("amp_val","amp_spin")]:
                sp = slot.get(
                    f"right_{field}")
                if sp:
                    sp.set(
                        getattr(cfg.right, attr))
            wv = slot.get("right_wave_var")
            if wv:
                wv.set(cfg.right.wave)

        def _mirror_adv_l_to_r():
            cfg.right.bi_val = cfg.left.bi_val
            cfg.right.fm_on  = cfg.left.fm_on
            cfg.right.fm_offset_lo = \
                cfg.left.fm_offset_lo
            cfg.right.fm_offset_hi = \
                cfg.left.fm_offset_hi
            sp = slot.get("right_bi_spin")
            if sp:
                sp.set(cfg.left.bi_val)
            fv = slot.get("right_fm_var")
            if fv:
                fv.set(cfg.left.fm_on)
            s_lo = slot.get("fm_l_lo")
            s_hi = slot.get("fm_l_hi")
            d_lo = slot.get("fm_r_lo")
            d_hi = slot.get("fm_r_hi")
            if d_lo and s_lo:
                d_lo.set(s_lo.get())
            if d_hi and s_hi:
                d_hi.set(s_hi.get())

        def _needs_rebuild(old):
            return cfg.binaural_on != old

        # ── guarded callbacks ──
        _busy = [False]

        def on_sync(*_):
            if _busy[0]:
                return
            _busy[0] = True
            try:
                old = cfg.binaural_on
                if sync_var.get():
                    bin_var.set(False)
                    cfg.binaural_on = False
                    _mirror_l_to_r()
                    _mirror_adv_l_to_r()
                if _needs_rebuild(old):
                    self._rebuild_body(slot)
                    self._rebuild_adv(slot)
            finally:
                _busy[0] = False

        def on_bin(*_):
            if _busy[0]:
                return
            _busy[0] = True
            try:
                old = cfg.binaural_on
                if bin_var.get():
                    sync_var.set(False)
                    adv_var.set(False)
                    adv_btn.config(
                        text="Advanced ▸",
                        fg=MUTED)
                    adv_wrap.pack_forget()
                    cfg.binaural_on = True
                    cfg.right.carrier = \
                        cfg.left.carrier
                    cfg.right.bw_freq = \
                        cfg.left.bw_freq
                else:
                    cfg.binaural_on = False
                if _needs_rebuild(old):
                    self._rebuild_body(slot)
                    self._rebuild_adv(slot)
            finally:
                _busy[0] = False

        def toggle_adv():
            if _busy[0]:
                return
            _busy[0] = True
            try:
                old = cfg.binaural_on
                if adv_var.get():
                    if bin_var.get():
                        bin_var.set(False)
                        cfg.binaural_on = False
                    adv_btn.config(
                        text="Advanced ▾",
                        fg=ACCENT)
                    adv_wrap.pack(
                        fill="x", padx=6,
                        pady=(0, 2),
                        before=ctrl)
                else:
                    adv_btn.config(
                        text="Advanced ▸",
                        fg=MUTED)
                    adv_wrap.pack_forget()
                if _needs_rebuild(old):
                    self._rebuild_body(slot)
                    self._rebuild_adv(slot)
            finally:
                _busy[0] = False

        sync_var.trace_add("write", on_sync)
        bin_var.trace_add("write", on_bin)
        adv_btn.config(command=toggle_adv)

        self._rebuild_body(slot)
        self._rebuild_adv(slot)

    # ══════════════════════════════════════════════════════════
    #  BODY
    # ══════════════════════════════════════════════════════════

    def _rebuild_body(self, slot):
        for w in slot["body"].winfo_children():
            w.destroy()
        for k in _BODY_KEYS:
            slot.pop(k, None)
        cfg = slot["config"]
        if cfg.binaural_on:
            self._build_binaural_body(slot)
        else:
            self._build_normal_body(slot)

    # ── non-binaural ──

    def _build_normal_body(self, slot):
        body = slot["body"]
        body.columnconfigure(
            0, weight=1, uniform="sides")
        body.columnconfigure(
            2, weight=1, uniform="sides")

        lf = tk.Frame(body, bg=CARD)
        lf.grid(row=0, column=0,
                sticky="nsew", padx=(0, 4))
        tk.Frame(
            body, bg=DIVIDER, width=1
        ).grid(row=0, column=1, sticky="ns")
        rf = tk.Frame(body, bg=CARD)
        rf.grid(row=0, column=2,
                sticky="nsew", padx=(4, 0))

        lh = tk.Frame(lf, bg=CARD)
        lh.pack(fill="x")
        slot["l_indicator"] = tk.Label(
            lh, text="▶", bg=CARD, fg=CARD,
            font=("Helvetica", 8, "bold"),
            width=2, anchor="w")
        slot["l_indicator"].pack(side="left")
        tk.Label(
            lh, text="L", bg=CARD, fg="#8888aa",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(side="left")
        self._build_side(lf, slot, "left")

        rh = tk.Frame(rf, bg=CARD)
        rh.pack(fill="x")
        slot["r_indicator"] = tk.Label(
            rh, text="▶", bg=CARD, fg=CARD,
            font=("Helvetica", 8, "bold"),
            width=2, anchor="w")
        slot["r_indicator"].pack(side="left")
        tk.Label(
            rh, text="R", bg=CARD, fg="#8888aa",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(side="left")
        self._build_side(rf, slot, "right")

    def _build_side(self, parent, slot, side):
        cfg = slot["config"]
        ch = (cfg.left if side == "left"
              else cfg.right)

        r = self._label_row(parent, "Carrier")
        car_spin = SpinEntry(
            r, width=5, from_=20, to=2000,
            step=1, fmt="{:.0f}",
            initial=str(int(ch.carrier)),
            suffix="Hz", bg=CARD,
            callback=lambda v, s=side: (
                setattr(ch, 'carrier', v),
                self._apply_sync(slot, s),
                self._update_fm_display(
                    slot, s)))
        car_spin.grid(
            row=0, column=1, sticky="w",
            padx=(0, 2))
        slot[f"{side}_carrier_spin"] = car_spin

        wv = tk.StringVar(value=ch.wave)
        wc = ttk.Combobox(
            r, textvariable=wv, values=WAVES,
            state="readonly", width=8)
        wc.grid(row=0, column=2, sticky="w")
        wc.bind(
            "<<ComboboxSelected>>",
            lambda e, s=side: (
                setattr(ch, 'wave', wv.get()),
                self._apply_sync(slot, s)))
        slot[f"{side}_wave_var"] = wv

        r2 = self._label_row(parent, "BW")
        bw_spin = SpinEntry(
            r2, width=5, from_=0, to=100,
            step=0.5, fmt="{:.1f}",
            initial=f"{ch.bw_freq:.1f}",
            suffix="Hz", bg=CARD,
            callback=lambda v, s=side: (
                setattr(ch, 'bw_freq', v),
                self._apply_sync(slot, s)))
        bw_spin.grid(
            row=0, column=1, sticky="w")
        slot[f"{side}_bw_spin"] = bw_spin

        r3 = self._label_row(parent, "Amp")
        amp_spin = SpinEntry(
            r3, width=5, from_=0, to=100,
            step=1, fmt="{:.0f}",
            initial=str(int(ch.amp_val)),
            suffix="", bg=CARD,
            callback=lambda v, s=side: (
                setattr(ch, 'amp_val', v),
                self._apply_sync(slot, s)))
        amp_spin.grid(
            row=0, column=1, sticky="w")
        slot[f"{side}_amp_spin"] = amp_spin

    # ── binaural ──

    def _build_binaural_body(self, slot):
        cfg  = slot["config"]
        body = slot["body"]

        r = self._label_row(body, "Center")

        def on_carrier(v):
            cfg.bi_carrier = v
            cfg.left.carrier = \
                v - cfg.bi_bw / 2
            cfg.right.carrier = \
                v + cfg.bi_bw / 2
            self._update_bin_labels(slot)
            self._update_fm_display(
                slot, "left")
            self._update_fm_display(
                slot, "right")

        def on_bw(v):
            cfg.bi_bw = v
            cfg.left.bw_freq  = v
            cfg.right.bw_freq = v
            cfg.left.carrier = \
                cfg.bi_carrier - v / 2
            cfg.right.carrier = \
                cfg.bi_carrier + v / 2
            self._update_bin_labels(slot)
            self._update_fm_display(
                slot, "left")
            self._update_fm_display(
                slot, "right")

        SpinEntry(
            r, width=5, from_=20, to=2000,
            step=1, fmt="{:.0f}",
            initial=str(int(cfg.bi_carrier)),
            suffix="Hz", bg=CARD,
            callback=on_carrier
        ).grid(row=0, column=1, sticky="w",
               padx=(0, 2))

        wv = tk.StringVar(value=cfg.bi_wave)
        ttk.Combobox(
            r, textvariable=wv, values=WAVES,
            state="readonly", width=8
        ).grid(row=0, column=2, sticky="w")
        wv.trace_add(
            "write",
            lambda *_: setattr(
                cfg, 'bi_wave', wv.get()))

        tk.Label(
            r, text="·", bg=CARD, fg=MUTED
        ).grid(row=0, column=3, padx=6)
        tk.Label(
            r, text="BW", bg=CARD, fg="#8888aa",
            font=("Helvetica", 8, "bold")
        ).grid(row=0, column=4)
        SpinEntry(
            r, width=5, from_=0, to=100,
            step=0.5, fmt="{:.1f}",
            initial=f"{cfg.bi_bw:.1f}",
            suffix="Hz", bg=CARD,
            callback=on_bw
        ).grid(row=0, column=5, sticky="w")

        cols = tk.Frame(body, bg=CARD)
        cols.pack(fill="x")
        cols.columnconfigure(
            0, weight=1, uniform="sides")
        cols.columnconfigure(
            2, weight=1, uniform="sides")

        lf = tk.Frame(cols, bg=CARD)
        lf.grid(row=0, column=0,
                sticky="nsew", padx=(0, 4))
        tk.Frame(
            cols, bg=DIVIDER, width=1
        ).grid(row=0, column=1, sticky="ns")
        rf = tk.Frame(cols, bg=CARD)
        rf.grid(row=0, column=2,
                sticky="nsew", padx=(4, 0))

        lh = tk.Frame(lf, bg=CARD)
        lh.pack(fill="x")
        slot["l_indicator"] = tk.Label(
            lh, text="▶", bg=CARD, fg=CARD,
            font=("Helvetica", 8, "bold"),
            width=2, anchor="w")
        slot["l_indicator"].pack(side="left")
        tk.Label(
            lh, text="L", bg=CARD, fg="#8888aa",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(side="left")

        r1 = self._label_row(lf, "Carrier")
        slot["bi_l_lbl"] = tk.Label(
            r1, text="", bg=CARD, fg=ACCENT,
            font=("Helvetica", 9, "bold"))
        slot["bi_l_lbl"].grid(
            row=0, column=1, sticky="w")

        rh = tk.Frame(rf, bg=CARD)
        rh.pack(fill="x")
        slot["r_indicator"] = tk.Label(
            rh, text="▶", bg=CARD, fg=CARD,
            font=("Helvetica", 8, "bold"),
            width=2, anchor="w")
        slot["r_indicator"].pack(side="left")
        tk.Label(
            rh, text="R", bg=CARD, fg="#8888aa",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(side="left")

        r3 = self._label_row(rf, "Carrier")
        slot["bi_r_lbl"] = tk.Label(
            r3, text="", bg=CARD, fg=ACCENT,
            font=("Helvetica", 9, "bold"))
        slot["bi_r_lbl"].grid(
            row=0, column=1, sticky="w")

        self._update_bin_labels(slot)

        r_amp = self._label_row(body, "Amp")

        tk.Label(
            r_amp, text="L", bg=CARD,
            fg="#8888aa",
            font=("Helvetica", 8, "bold")
        ).grid(row=0, column=1, padx=(0, 2))
        l_amp = SpinEntry(
            r_amp, width=5, from_=0, to=100,
            step=1, fmt="{:.0f}",
            initial=str(int(cfg.left.amp_val)),
            suffix="", bg=CARD,
            callback=lambda v: setattr(
                cfg.left, 'amp_val', v))
        l_amp.grid(
            row=0, column=2, sticky="w",
            padx=(0, 2))
        slot["left_amp_spin"] = l_amp

        tk.Label(
            r_amp, text="·", bg=CARD, fg=MUTED
        ).grid(row=0, column=3, padx=6)

        tk.Label(
            r_amp, text="R", bg=CARD,
            fg="#8888aa",
            font=("Helvetica", 8, "bold")
        ).grid(row=0, column=4, padx=(0, 2))
        r_amp_spin = SpinEntry(
            r_amp, width=5, from_=0, to=100,
            step=1, fmt="{:.0f}",
            initial=str(int(cfg.right.amp_val)),
            suffix="", bg=CARD,
            callback=lambda v: setattr(
                cfg.right, 'amp_val', v))
        r_amp_spin.grid(
            row=0, column=5, sticky="w")
        slot["right_amp_spin"] = r_amp_spin

    # ══════════════════════════════════════════════════════════
    #  ADVANCED
    # ══════════════════════════════════════════════════════════

    def _rebuild_adv(self, slot):
        for w in slot["adv_wrap"].winfo_children():
            w.destroy()
        for k in _ADV_KEYS:
            slot.pop(k, None)
        cfg = slot["config"]
        if cfg.binaural_on:
            self._build_adv_side(
                slot["adv_wrap"], slot, "left")
            self._build_adv_side(
                slot["adv_wrap"], slot, "right")
        else:
            wrap = slot["adv_wrap"]
            wrap.columnconfigure(
                0, weight=1, uniform="sides")
            wrap.columnconfigure(
                2, weight=1, uniform="sides")
            lf = tk.Frame(wrap, bg=CARD)
            lf.grid(
                row=0, column=0,
                sticky="nsew", padx=(0, 4))
            tk.Frame(
                wrap, bg=DIVIDER, width=1
            ).grid(
                row=0, column=1, sticky="ns")
            rf = tk.Frame(wrap, bg=CARD)
            rf.grid(
                row=0, column=2,
                sticky="nsew", padx=(4, 0))
            self._build_adv_side(
                lf, slot, "left")
            self._build_adv_side(
                rf, slot, "right")

    def _build_adv_side(self, parent, slot,
                        side):
        cfg = slot["config"]
        ch = (cfg.left if side == "left"
              else cfg.right)
        tag = "L" if side == "left" else "R"
        fk  = "l" if side == "left" else "r"

        r = self._label_row(
            parent, f"{tag} Bi")

        def on_bi(v, s=side):
            ch.bi_val = v
            self._apply_adv_sync(slot, s)

        bi_spin = SpinEntry(
            r, width=5, from_=0, to=100,
            step=1, fmt="{:.0f}",
            initial=str(int(ch.bi_val)),
            suffix="", bg=CARD,
            callback=on_bi)
        bi_spin.grid(
            row=0, column=1, sticky="w",
            padx=(0, 2))
        slot[f"{side}_bi_spin"] = bi_spin

        tk.Label(
            r, text="·", bg=CARD, fg=MUTED
        ).grid(row=0, column=2, padx=4)

        fm_var = tk.BooleanVar(value=ch.fm_on)
        slot[f"{side}_fm_var"] = fm_var

        def on_fm(s=side):
            ch.fm_on = bool(fm_var.get())
            self._apply_adv_sync(slot, s)

        tk.Checkbutton(
            r, variable=fm_var, text="FM",
            bg=CARD, fg=ACCENT,
            selectcolor=SURFACE2,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold"),
            command=on_fm
        ).grid(row=0, column=3, padx=(0, 4))

        base = self._get_effective_carrier(
            slot, side)
        lo_hz = base + ch.fm_offset_lo
        hi_hz = base + ch.fm_offset_hi

        r2 = self._label_row(parent, "FM")

        def on_lo(v, s=side, c=ch):
            eff = self._get_effective_carrier(
                slot, s)
            c.fm_offset_lo = v - eff
            self._apply_adv_sync(slot, s)

        def on_hi(v, s=side, c=ch):
            eff = self._get_effective_carrier(
                slot, s)
            c.fm_offset_hi = v - eff
            self._apply_adv_sync(slot, s)

        lo_spin = SpinEntry(
            r2, width=5, from_=20, to=2000,
            step=1, fmt="{:.0f}",
            initial=str(int(lo_hz)),
            suffix="Hz", bg=CARD,
            callback=on_lo)
        lo_spin.grid(
            row=0, column=1, sticky="w",
            padx=(0, 2))

        tk.Label(
            r2, text=" — ",
            bg=CARD, fg=MUTED
        ).grid(row=0, column=2)

        hi_spin = SpinEntry(
            r2, width=5, from_=20, to=2000,
            step=1, fmt="{:.0f}",
            initial=str(int(hi_hz)),
            suffix="Hz", bg=CARD,
            callback=on_hi)
        hi_spin.grid(
            row=0, column=3, sticky="w",
            padx=(2, 0))

        slot[f"fm_{fk}_lo"] = lo_spin
        slot[f"fm_{fk}_hi"] = hi_spin

    # ══════════════════════════════════════════════════════════
    #  DISPLAY UPDATERS
    # ══════════════════════════════════════════════════════════

    def _get_effective_carrier(self, slot,
                               side):
        cfg = slot["config"]
        if cfg.binaural_on:
            if side == "left":
                return (cfg.bi_carrier
                        - cfg.bi_bw / 2)
            return (cfg.bi_carrier
                    + cfg.bi_bw / 2)
        ch = (cfg.left if side == "left"
              else cfg.right)
        return ch.carrier

    def _update_bin_labels(self, slot):
        cfg = slot["config"]
        freq = cfg.bi_carrier
        bw   = cfg.bi_bw
        lbl_l = slot.get("bi_l_lbl")
        lbl_r = slot.get("bi_r_lbl")
        if lbl_l:
            lbl_l.config(
                text=(
                    f"L: "
                    f"{freq - bw/2:.1f} Hz"))
        if lbl_r:
            lbl_r.config(
                text=(
                    f"R: "
                    f"{freq + bw/2:.1f} Hz"))

    def _update_fm_display(self, slot, side):
        cfg = slot["config"]
        ch = (cfg.left if side == "left"
              else cfg.right)
        base = self._get_effective_carrier(
            slot, side)
        fk = ("l" if side == "left" else "r")
        lo = slot.get(f"fm_{fk}_lo")
        hi = slot.get(f"fm_{fk}_hi")
        if lo:
            lo.set(base + ch.fm_offset_lo)
        if hi:
            hi.set(base + ch.fm_offset_hi)

    # ══════════════════════════════════════════════════════════
    #  DEVICE / VOLUME / SCROLL
    # ══════════════════════════════════════════════════════════

    def _on_canvas_resize(self, event):
        self._scanvas.itemconfig(
            self._cw, width=event.width)

    def _on_mousewheel(self, event):
        self._scanvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units")

    def _apply_device(self):
        idx = self.dev_cb.current()
        if (idx < 0
                or idx >= len(
                    self.output_devices)):
            self.eng.device_index = None
            self.eng.channels = 2
            return
        _, di, mch = self.output_devices[idx]
        self.eng.device_index = di
        self.eng.channels = min(mch, 2)

    def _test_stereo(self):
        self.root.update()
        idx = self.eng.device_index
        ch  = self.eng.channels
        def go():
            try:
                test_device_stereo(idx, ch)
            except Exception as e:
                self.root.after(
                    0, lambda:
                        messagebox.showerror(
                            "Error", str(e)))
        threading.Thread(
            target=go, daemon=True).start()

    def _on_vol_var(self, *_):
        try:
            v = float(self._vol_var.get())
            self.vol_spin.set(v)
            self.eng.vol = v / 100.0
        except:
            pass

    def _on_vol(self, v):
        self.eng.vol = v / 100.0
        self._vol_var.set(v)

    # ══════════════════════════════════════════════════════════
    #  TRANSPORT — chains playlists
    # ══════════════════════════════════════════════════════════

    def _start_pl(self, container):
        container["playlist"].prepare_playback()
        self.eng.playlist = container["playlist"]
        try:
            self.eng.start()
        except Exception as e:
            messagebox.showerror(
                "Error", str(e))
            return
        self._playing_cont = container
        container["play_btn"].config(
            text="■  Stop")
        container["status_lbl"].config(
            text="● Playing", fg=ACCENT)
        container["frame"].config(
            highlightbackground=ACCENT)
        container["time_lbl"].config(
            text="00:00:00")
        container["row_ind"].config(text="")

    def _toggle_pl(self, container):
        if self._playing_cont is container:
            self._stop_current()
            return
        if self._playing_cont:
            self._stop_current()
        self._start_pl(container)

    def _stop_current(self):
        c = self._playing_cont
        if not c:
            return
        self.eng.stop()
        c["play_btn"].config(text="▶  Play")
        c["status_lbl"].config(
            text="● Stopped", fg=MUTED)
        c["frame"].config(
            highlightbackground="#333355")
        c["time_lbl"].config(text="")
        c["row_ind"].config(text="")
        self._playing_cont = None
        self._set_active_row(None, -1)

    def _play_next_playlist(self):
        if not self._playing_cont:
            return

        ci = self._containers.index(
            self._playing_cont)

        # find position in playlist order
        try:
            pos = self._pl_play_order.index(ci)
        except ValueError:
            self._stop_current()
            return

        self._stop_current()

        next_pos = pos + 1
        if next_pos >= len(self._pl_play_order):
            if self._pl_loop:
                next_pos = 0
            else:
                return

        next_ci = self._pl_play_order[next_pos]
        if next_ci < len(self._containers):
            self._start_pl(
                self._containers[next_ci])

    # ══════════════════════════════════════════════════════════
    #  SAVE
    # ══════════════════════════════════════════════════════════

    def _save_pl(self, container):
        pl = container["playlist"]
        duration = pl.total_duration()
        if duration <= 0:
            messagebox.showwarning(
                "Duration",
                "Set at least one row"
                " duration > 0")
            return
        e = int(duration)
        s = e % 60
        m = (e // 60) % 60
        h = e // 3600
        dur_str = (
            f"{h:02d}:{m:02d}:{s:02d}")
        pl_name = pl.name.lower().replace(
            " ", "_")
        initial = (
            f"{pl_name}"
            f"_{dur_str.replace(':', '')}.wav")
        path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV", "*.wav")],
            initialfile=initial)
        if not path:
            return
        container["status_lbl"].config(
            text="● Saving…", fg=ACCENT)
        self.root.update()

        save_eng = PlaylistEngine()
        save_eng.playlist = pl
        save_eng.vol = self.eng.vol

        def go():
            save_eng.save_wav(
                path, duration=duration)
            mb = (os.path.getsize(path)
                  / (1024 * 1024))
            def done():
                if (self._playing_cont
                        is container):
                    container[
                        "status_lbl"].config(
                        text="● Playing",
                        fg=ACCENT)
                else:
                    container[
                        "status_lbl"].config(
                        text=(
                            f"● Saved "
                            f"({mb:.1f} MB)"),
                        fg=ACCENT)
                    self.root.after(
                        3000,
                        lambda: container[
                            "status_lbl"
                        ].config(
                            text="● Stopped",
                            fg=MUTED))
            self.root.after(0, done)

        threading.Thread(
            target=go, daemon=True).start()

    # ══════════════════════════════════════════════════════════
    #  TICK
    # ══════════════════════════════════════════════════════════

    def _tick(self):
        c = self._playing_cont
        if self.eng.playing and c:
            e = self.eng.elapsed()
            total = int(e)
            s = total % 60
            m = (total // 60) % 60
            h = total // 3600
            c["time_lbl"].config(
                text=(
                    f"{h:02d}:"
                    f"{m:02d}:{s:02d}"))

            idx, row_t = (
                self.eng._current_row())
            self._set_active_row(c, idx)

            if idx >= 0:
                rs = int(row_t)
                rem = rs % 60
                rm  = (rs // 60) % 60
                rh  = rs // 3600
                c["row_ind"].config(
                    text=(
                        f"Row {idx+1} — "
                        f"{rh:02d}:{rm:02d}"
                        f":{rem:02d}"))
            else:
                self._play_next_playlist()
        else:
            self._set_active_row(None, -1)

        self.root.after(80, self._tick)

    # ══════════════════════════════════════════════════════════
    #  RUN / QUIT
    # ══════════════════════════════════════════════════════════

    def run(self):
        self.root.protocol(
            "WM_DELETE_WINDOW", self._quit)
        self.root.mainloop()

    def _quit(self):
        if self.eng.playing:
            self.eng.stop()
        self.root.destroy()