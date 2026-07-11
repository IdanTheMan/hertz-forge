import tkinter as tk
from tkinter import ttk

from hertz_forge.constants import (
    WAVES, BG, SURFACE, SURFACE2,
    ACCENT, ACCENT2, MUTED, FG,
    DIVIDER, CARD)
from hertz_forge.widgets import SpinEntry

_BODY_KEYS = {
    "left_carrier_spin", "left_wave_var",
    "left_bw_spin", "left_amp_spin",
    "right_carrier_spin", "right_wave_var",
    "right_bw_spin", "right_amp_spin",
    "bi_l_lbl", "bi_r_lbl",
}

_ADV_KEYS = {
    "fm_l_lo", "fm_l_hi",
    "fm_r_lo", "fm_r_hi",
    "left_bi_spin", "right_bi_spin",
    "left_fm_var", "right_fm_var",
}


class RowMixin:

    # ── sync ──

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

    # ── slot creation ──

    def _create_slot(self, container, index):
        cfg = container["playlist"].rows[index]
        rows_frame = container["rows_frame"]

        border = tk.Frame(
            rows_frame, bg="#222244")
        border.pack(fill="x", padx=4, pady=4)

        card = tk.Frame(border, bg=CARD)
        card.pack(fill="x", padx=1, pady=1)

        hdr = tk.Frame(card, bg=CARD)
        hdr.pack(fill="x", padx=8, pady=(4, 0))

        grip = tk.Label(
            hdr, text="⠿", bg=CARD, fg=MUTED,
            font=("Helvetica", 12),
            cursor="sb_v_double_arrow",
            padx=2)
        grip.pack(side="left")

        row_inc_var = tk.BooleanVar(
            value=cfg.included)
        tk.Checkbutton(
            hdr, variable=row_inc_var,
            text="",
            bg=CARD, fg=ACCENT,
            selectcolor=SURFACE2,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold")
        ).pack(side="left")

        collapse_btn = tk.Label(
            hdr, text="▾", bg=CARD, fg=MUTED,
            font=("Helvetica", 10),
            cursor="hand2", padx=2)
        collapse_btn.pack(side="left")
        collapse_btn.bind(
            "<Button-1>",
            lambda e:
                self._toggle_row_collapse(slot))
        collapse_btn.bind(
            "<Enter>",
            lambda e: collapse_btn.config(
                fg=ACCENT))
        collapse_btn.bind(
            "<Leave>",
            lambda e: collapse_btn.config(
                fg=MUTED))

        num_lbl = tk.Label(
            hdr,
            text=(cfg.name if cfg.name
                  else f"Row {index + 1}"),
            bg=CARD, fg=MUTED,
            font=("Helvetica", 10, "bold"))
        num_lbl.pack(side="left", padx=(4, 0))

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

        content = tk.Frame(card, bg=CARD)
        content.pack(fill="x")

        body = tk.Frame(content, bg=CARD)
        body.pack(fill="x", padx=6, pady=(4, 0))

        adv_wrap = tk.Frame(content, bg=CARD)

        ctrl = tk.Frame(content, bg=CARD)
        ctrl.pack(fill="x", padx=8, pady=(4, 4))

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
            to=36000, step=5,
            fmt="{:.0f}",
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

        # ── slot dict created HERE ──
        slot = {
            "border":       border,
            "frame":        card,
            "body":         body,
            "adv_wrap":     adv_wrap,
            "config":       cfg,
            "num_lbl":      num_lbl,
            "grip":         grip,
            "sync_var":     sync_var,
            "bin_var":      bin_var,
            "dur_spin":     dur_spin,
            "_active":      False,
            "row_inc_var":  row_inc_var,
            "content":      content,
            "collapse_btn": collapse_btn,
            "collapsed":    False,
        }
        container["slots"].append(slot)

        # ── save / dup buttons (after slot
        #    exists so lambda can capture it)
        save_btn = tk.Button(
            hdr, text="save",
            font=("Helvetica", 8),
            bg=SURFACE2, fg=MUTED,
            activebackground=ACCENT2,
            activeforeground=ACCENT,
            relief="flat", bd=0,
            padx=4, pady=1,
            cursor="hand2",
            command=lambda c=container, s=slot:
                self._save_row_config(c, s))
        save_btn.pack(side="left", padx=(8, 0))
        save_btn.bind(
            "<Enter>",
            lambda e, b=save_btn:
                b.config(fg=ACCENT))
        save_btn.bind(
            "<Leave>",
            lambda e, b=save_btn:
                b.config(fg=MUTED))

        dup_btn = tk.Button(
            hdr, text="dup",
            font=("Helvetica", 8),
            bg=SURFACE2, fg=MUTED,
            activebackground=ACCENT2,
            activeforeground=ACCENT,
            relief="flat", bd=0,
            padx=4, pady=1,
            cursor="hand2",
            command=lambda c=container, s=slot:
                self._duplicate_row(c, s))
        dup_btn.pack(side="left", padx=(4, 0))
        dup_btn.bind(
            "<Enter>",
            lambda e, b=dup_btn:
                b.config(fg=ACCENT))
        dup_btn.bind(
            "<Leave>",
            lambda e, b=dup_btn:
                b.config(fg=MUTED))

        # wire include
        def _toggle_row_include():
            cfg.included = row_inc_var.get()
            container["playlist"]._rebuild_order()
            self._update_pl_dur(container)

        row_inc_var.trace_add(
            "write",
            lambda *_: _toggle_row_include())

        # wire row drag
        row_idx = index
        grip.bind(
            "<ButtonPress-1>",
            lambda e, c=container, i=row_idx:
                self._start_row_drag(c, i, e))
        grip.bind(
            "<Enter>",
            lambda e, g=grip: g.config(
                fg=ACCENT))
        grip.bind(
            "<Leave>",
            lambda e, g=grip: g.config(
                fg=MUTED))

        # ── helpers ──
        def _mirror_l_to_r():
            cfg.right.carrier = cfg.left.carrier
            cfg.right.wave    = cfg.left.wave
            cfg.right.bw_freq = cfg.left.bw_freq
            cfg.right.amp_val = cfg.left.amp_val
            for attr, field in [
                    ("carrier", "carrier_spin"),
                    ("bw_freq", "bw_spin"),
                    ("amp_val", "amp_spin")]:
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
            if sp: sp.set(cfg.left.bi_val)
            fv = slot.get("right_fm_var")
            if fv: fv.set(cfg.left.fm_on)
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

        _busy = [False]

        def on_sync(*_):
            if _busy[0]: return
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
            if _busy[0]: return
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
            if _busy[0]: return
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

    # ── body ──

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

        tk.Label(
            lf, text="L", bg=CARD,
            fg="#8888aa",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(fill="x")
        self._build_side(lf, slot, "left")

        tk.Label(
            rf, text="R", bg=CARD,
            fg="#8888aa",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(fill="x")
        self._build_side(rf, slot, "right")

    def _build_side(self, parent, slot, side):
        cfg = slot["config"]
        ch = (cfg.left if side == "left"
              else cfg.right)

        r = self._label_row(parent, "Carrier")
        car_spin = SpinEntry(
            r, width=5, from_=0, to=2000,
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
            r, width=5, from_=0, to=2000,
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
            r, text="BW", bg=CARD,
            fg="#8888aa",
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

        tk.Label(
            lf, text="L", bg=CARD,
            fg="#8888aa",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(fill="x")
        r1 = self._label_row(lf, "Carrier")
        slot["bi_l_lbl"] = tk.Label(
            r1, text="", bg=CARD, fg=ACCENT,
            font=("Helvetica", 9, "bold"))
        slot["bi_l_lbl"].grid(
            row=0, column=1, sticky="w")

        tk.Label(
            rf, text="R", bg=CARD,
            fg="#8888aa",
            font=("Helvetica", 9, "bold"),
            anchor="w").pack(fill="x")
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

    # ── advanced ──

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
            ).grid(row=0, column=1, sticky="ns")
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

        fm_var = tk.BooleanVar(
            value=ch.fm_on)
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
            r2, width=5, from_=0, to=2000,
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
            r2, width=5, from_=0, to=2000,
            step=1, fmt="{:.0f}",
            initial=str(int(hi_hz)),
            suffix="Hz", bg=CARD,
            callback=on_hi)
        hi_spin.grid(
            row=0, column=3, sticky="w",
            padx=(2, 0))

        slot[f"fm_{fk}_lo"] = lo_spin
        slot[f"fm_{fk}_hi"] = hi_spin

    # ── display updaters ──

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