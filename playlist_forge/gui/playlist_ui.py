import copy
import tkinter as tk
from tkinter import ttk
import random

from hertz_forge.constants import (
    BG, SURFACE, SURFACE2, ACCENT, ACCENT2,
    MUTED, FG, DIVIDER, CARD)
from ..engine import Playlist

_MIN_COL_W = 320


class PlaylistMixin:

    # ── playlist loop / shuffle ──

    def _toggle_pl_loop(self):
        self._pl_loop = self._pl_loop_var.get()

    def _toggle_pl_shuffle(self):
        self._pl_shuffle = (
            self._pl_shuffle_var.get())
        self._rebuild_pl_order()

    def _rebuild_pl_order(self):
        self._pl_play_order = [
            i for i, c in enumerate(
                self._containers)
            if c.get("included", True)]
        if self._pl_shuffle:
            random.shuffle(self._pl_play_order)

    # ── reflow (multi-column) ──

    def _schedule_reflow(self):
        if hasattr(self, '_reflow_id'):
            try:
                self.root.after_cancel(
                    self._reflow_id)
            except (ValueError, tk.TclError):
                pass
        self._reflow_id = self.root.after(
            20, self._reflow_playlists)

    def _reflow_playlists(self):
        pf = self._pl_frame
        pf.update_idletasks()
        avail = pf.winfo_width()
        if avail < 10:
            return
        cols = max(1, avail // _MIN_COL_W)

        for i, c in enumerate(self._containers):
            r = i // cols
            co = i % cols
            c["frame"].grid(
                row=r, column=co,
                sticky="nsew",
                padx=4, pady=6, ipady=4)

        for col in range(cols):
            pf.columnconfigure(
                col, weight=1, uniform="pl")
        for col in range(cols, 20):
            pf.columnconfigure(
                col, weight=0, uniform="")

        self._refresh_scroll()

    # ── collapse / expand ──

    def _toggle_pl_collapse(self, container):
        if container["collapsed"]:
            container["content"].pack(fill="x")
            container["collapse_btn"].config(
                text="▾")
            container["collapsed"] = False
        else:
            container["content"].pack_forget()
            container["collapse_btn"].config(
                text="▸")
            container["collapsed"] = True
        self._refresh_scroll()

    def _toggle_row_collapse(self, slot):
        if slot["collapsed"]:
            slot["content"].pack(fill="x")
            slot["collapse_btn"].config(
                text="▾")
            slot["collapsed"] = False
        else:
            slot["content"].pack_forget()
            slot["collapse_btn"].config(
                text="▸")
            slot["collapsed"] = True
        self._refresh_scroll()

    # ── playlist containers ──

    def _add_playlist(self, name=None):
        if name is None:
            name = (f"Playlist "
                    f"{len(self._playlists) + 1}")
        pl = Playlist(name=name)
        self._playlists.append(pl)
        ci = len(self._playlists) - 1
        self._create_pl_container(ci)
        self._add_row(self._containers[ci])
        self._rebuild_pl_order()

    def _remove_playlist(self, container):
        ci = self._containers.index(container)
        if self._playing_cont is container:
            self._stop_current()
        self._playlists.pop(ci)
        self._containers.pop(ci)
        container["frame"].destroy()
        self._rebuild_pl_order()
        self._reflow_playlists()

    def _duplicate_playlist(self, container):
        pl = container["playlist"]
        new_pl = Playlist(
            name=f"{pl.name} (copy)")
        new_pl.row_loop = pl.row_loop
        new_pl.row_shuffle = pl.row_shuffle
        new_pl.rows = [
            copy.deepcopy(r) for r in pl.rows]
        self._playlists.append(new_pl)
        ci = len(self._playlists) - 1
        self._create_pl_container(ci)
        new_cont = self._containers[ci]
        for i in range(len(new_pl.rows)):
            self._create_slot(new_cont, i)
        self._renumber(new_cont)
        self._update_pl_dur(new_cont)
        self._rebuild_pl_order()
        self._reflow_playlists()

    def _create_pl_container(self, ci):
        pl = self._playlists[ci]

        frame = tk.Frame(
            self._pl_frame, bg=CARD,
            highlightthickness=2,
            highlightbackground="#333355")
        # grid placement handled by _reflow

        # ── line 1 ──
        h1 = tk.Frame(frame, bg=CARD)
        h1.pack(fill="x", padx=8, pady=(6, 0))

        pl_grip = tk.Label(
            h1, text="⠿", bg=CARD, fg=MUTED,
            font=("Helvetica", 14),
            cursor="sb_v_double_arrow",
            padx=2)
        pl_grip.pack(side="left")

        pl_include_var = tk.BooleanVar(
            value=True)
        include_cb = tk.Checkbutton(
            h1, variable=pl_include_var,
            text="",
            bg=CARD, fg=ACCENT,
            selectcolor=CARD,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 9, "bold"))
        include_cb.pack(side="left")

        collapse_btn = tk.Label(
            h1, text="▾", bg=CARD, fg=MUTED,
            font=("Helvetica", 10),
            cursor="hand2", padx=2)
        collapse_btn.pack(side="left")
        collapse_btn.bind(
            "<Button-1>",
            lambda e:
                self._toggle_pl_collapse(
                    container))
        collapse_btn.bind(
            "<Enter>",
            lambda e: collapse_btn.config(
                fg=ACCENT))
        collapse_btn.bind(
            "<Leave>",
            lambda e: collapse_btn.config(
                fg=MUTED))

        name_lbl = tk.Label(
            h1, text=pl.name, bg=CARD,
            fg=ACCENT,
            font=("Helvetica", 11, "bold"))
        name_lbl.pack(side="left", padx=(4, 0))

        del_btn = tk.Button(
            h1, text="×",
            font=("Helvetica", 11, "bold"),
            bg=CARD, fg="#cc6666",
            activebackground="#442222",
            activeforeground="#cc6666",
            relief="flat", bd=0, padx=6,
            cursor="hand2")
        del_btn.pack(side="right")

        dup_btn = tk.Button(
            h1, text="dup",
            font=("Helvetica", 8),
            bg=CARD, fg=MUTED,
            activebackground=CARD,
            activeforeground=ACCENT,
            relief="flat", bd=0, padx=4,
            cursor="hand2")
        dup_btn.pack(side="right")
        dup_btn.bind(
            "<Enter>",
            lambda e, b=dup_btn:
                b.config(fg=ACCENT))
        dup_btn.bind(
            "<Leave>",
            lambda e, b=dup_btn:
                b.config(fg=MUTED))

        # ── content ──
        content = tk.Frame(frame, bg=CARD)
        content.pack(fill="x")

        # ── line 2: controls ──
        h2 = tk.Frame(content, bg=CARD)
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

        load_btn = tk.Button(
            h2, text="Load…",
            font=("Helvetica", 9),
            bg=SURFACE2, fg=MUTED,
            activebackground=ACCENT2,
            activeforeground=ACCENT,
            relief="flat", bd=0,
            padx=4, pady=2,
            cursor="hand2")
        load_btn.pack(
            side="left", padx=(8, 0))

        row_loop_var = tk.BooleanVar(
            value=pl.row_loop)
        loop_cb = tk.Checkbutton(
            h2, variable=row_loop_var,
            text="loop",
            bg=CARD, fg=MUTED,
            selectcolor=CARD,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 8, "bold"),
            command=lambda: (
                setattr(pl, 'row_loop',
                        row_loop_var.get()),
                loop_cb.config(
                    fg=ACCENT
                    if row_loop_var.get()
                    else MUTED)))
        loop_cb.pack(side="left", padx=(10, 0))

        row_shuffle_var = tk.BooleanVar(
            value=pl.row_shuffle)
        shuffle_cb = tk.Checkbutton(
            h2, variable=row_shuffle_var,
            text="shuffle",
            bg=CARD, fg=MUTED,
            selectcolor=CARD,
            activebackground=CARD,
            activeforeground=ACCENT,
            font=("Helvetica", 8, "bold"),
            command=lambda: (
                setattr(pl, 'row_shuffle',
                        row_shuffle_var.get()),
                pl._rebuild_order(),
                shuffle_cb.config(
                    fg=ACCENT
                    if row_shuffle_var.get()
                    else MUTED)))
        shuffle_cb.pack(side="left", padx=(4, 0))

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
        h3 = tk.Frame(content, bg=CARD)
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

        tk.Frame(
            content, bg=DIVIDER, height=1
        ).pack(fill="x", padx=8, pady=6)

        # ── rows area ──
        rows_frame = tk.Frame(content, bg=CARD)
        rows_frame.pack(
            fill="x", padx=4, pady=(2, 0))

        btn_frame = tk.Frame(content, bg=CARD)
        btn_frame.pack(
            fill="x", padx=4, pady=(6, 2))
        ttk.Button(
            btn_frame, text="+ row",
            style="Small.TButton",
            command=lambda c=None: None
        ).pack(anchor="center")

        container = {
            "playlist":     pl,
            "frame":        frame,
            "name_lbl":     name_lbl,
            "pl_grip":      pl_grip,
            "play_btn":     play_btn,
            "export_btn":   export_btn,
            "load_btn":     load_btn,
            "status_lbl":   status_lbl,
            "total_lbl":    total_lbl,
            "time_lbl":     time_lbl,
            "row_ind":      row_ind,
            "rows_frame":   rows_frame,
            "btn_frame":    btn_frame,
            "content":      content,
            "collapse_btn": collapse_btn,
            "collapsed":    False,
            "slots":        [],
            "included":     True,
        }
        self._containers.append(container)

        btn_frame.winfo_children()[0].config(
            command=lambda c=container:
                self._add_row(c))

        def _toggle_pl_include():
            container["included"] = (
                pl_include_var.get())
            self._rebuild_pl_order()
            self._update_pl_dur(container)
            include_cb.config(
                fg=ACCENT
                if pl_include_var.get()
                else MUTED)

        include_cb.config(
            command=_toggle_pl_include)
        del_btn.config(
            command=lambda c=container:
                self._remove_playlist(c))
        dup_btn.config(
            command=lambda c=container:
                self._duplicate_playlist(c))
        play_btn.config(
            command=lambda c=container:
                self._toggle_pl(c))
        export_btn.config(
            command=lambda c=container:
                self._save_pl(c))
        load_btn.config(
            command=lambda c=container:
                self._load_into_playlist(c))

        pl_grip.bind(
            "<ButtonPress-1>",
            lambda e, g=pl_grip:
                self._start_pl_drag(g, e))
        pl_grip.bind(
            "<Enter>",
            lambda e, g=pl_grip: g.config(
                fg=ACCENT))
        pl_grip.bind(
            "<Leave>",
            lambda e, g=pl_grip: g.config(
                fg=MUTED))

        self._update_pl_dur(container)
        self._reflow_playlists()

    # ── row management ──

    def _add_row(self, container):
        container["playlist"].add_row()
        idx = (len(container["playlist"].rows)
               - 1)
        container["playlist"].rows[idx].name = (
            f"Row {idx + 1}")
        self._create_slot(container, idx)
        self._update_pl_dur(container)
        self._refresh_scroll()

    def _remove_row(self, container, row_idx):
        container["playlist"].remove_row(
            row_idx)
        slot = container["slots"].pop(row_idx)
        slot["border"].destroy()

        if not container["slots"]:
            old_rf = container["rows_frame"]
            new_rf = tk.Frame(
                container["content"], bg=CARD)
            new_rf.pack(
                fill="x", padx=4, pady=(2, 0),
                before=container["btn_frame"])
            old_rf.destroy()
            container["rows_frame"] = new_rf

        self._renumber(container)
        self._update_pl_dur(container)
        self._refresh_scroll()

    def _duplicate_row(self, container, slot):
        cfg = slot["config"]
        new_cfg = copy.deepcopy(cfg)
        pl = container["playlist"]
        idx = pl.rows.index(cfg)
        pl.rows.insert(idx + 1, new_cfg)
        new_cfg.name = ""
        self._rebuild_container_slots(container)
        self._refresh_scroll()

    def _renumber(self, container):
        for i, slot in enumerate(
                container["slots"]):
            cfg = slot["config"]
            cfg.name = f"Row {i + 1}"
            slot["num_lbl"].config(
                text=cfg.name)

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

    # ── active row ──

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