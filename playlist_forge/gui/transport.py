import os
import threading

from tkinter import filedialog, messagebox

from hertz_forge.constants import MUTED, ACCENT
from hertz_forge.audio import test_device_stereo
from ..engine import PlaylistEngine
from .helpers import _fmt_dur


class TransportMixin:

    # ── device / volume ──

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

    # ── play all / stop all ──

    def _play_or_stop_all(self):
        if self._playing_cont:
            self._stop_current()
        else:
            for c in self._containers:
                if c.get("included", True):
                    self._start_pl(c)
                    return

    def _sync_stop_all_btn(self):
        if self._playing_cont:
            self._stop_all_btn.config(
                text="■ Stop All", fg="#cc6666")
        else:
            self._stop_all_btn.config(
                text="▶ Play All", fg=ACCENT)

    # ── transport ──

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
        self._pl_transitioning = False
        self._sync_stop_all_btn()
        container["play_btn"].config(
            text="■  Stop")
        container["frame"].config(
            highlightbackground=ACCENT)

    def _toggle_pl(self, container):
        if self._playing_cont is container:
            self._stop_current()
            return
        if self._playing_cont:
            self._stop_current()
        self._start_pl(container)

    def _stop_current(self):
        self._pl_transitioning = False
        c = self._playing_cont
        if not c:
            return
        self.eng.stop()
        c["play_btn"].config(text="▶  Play")
        c["frame"].config(
            highlightbackground="#333355")
        self._playing_cont = None
        self._set_active_row(None, -1)
        self._reset_row_time_labels()
        self._sync_stop_all_btn()

    def _reset_row_time_labels(self):
        for cont in self._containers:
            for slot in cont["slots"]:
                dur = slot["config"].duration
                slot["row_time_lbl"].config(
                    text=_fmt_dur(dur),
                    fg=MUTED)

    # ── playlist transitions (seamless) ──

    def _do_pl_transition(self):
        if not self._playing_cont:
            return
        self._rebuild_pl_order()
        ci = self._containers.index(
            self._playing_cont)
        try:
            pos = self._pl_play_order.index(ci)
        except ValueError:
            self._stop_current()
            return

        next_pos = pos + 1
        if next_pos >= len(
                self._pl_play_order):
            if self._pl_loop:
                next_pos = 0
            else:
                self._stop_current()
                return

        next_ci = self._pl_play_order[next_pos]
        if next_ci >= len(self._containers):
            self._stop_current()
            return

        new = self._containers[next_ci]
        new["playlist"].prepare_playback()
        if not new["playlist"]._play_order:
            self._stop_current()
            return

        old = self._playing_cont
        old["play_btn"].config(
            text="▶  Play")
        old["frame"].config(
            highlightbackground="#333355")

        self.eng.switch_playlist(
            new["playlist"])

        self._playing_cont = new
        self._pl_transitioning = False
        self._sync_stop_all_btn()
        new["play_btn"].config(
            text="■  Stop")
        new["frame"].config(
            highlightbackground=ACCENT)
        self._set_active_row(None, -1)

    # ── save ──

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

        save_eng = PlaylistEngine()
        save_eng.playlist = pl
        save_eng.vol = self.eng.vol

        def go():
            save_eng.save_wav(path)
            mb = (os.path.getsize(path)
                  / (1024 * 1024))

            def done():
                self.root.after(
                    3000,
                    lambda: None)

            self.root.after(0, done)

        threading.Thread(
            target=go, daemon=True).start()

    # ── tick ──

    def _tick(self):
        active_cont = None
        active_idx = -1
        row_t = 0

        if self.eng.playing and self._playing_cont:
            c = self._playing_cont

            idx, row_t = (
                self.eng._current_row())
            self._set_active_row(c, idx)

            if idx >= 0:
                active_cont = c
                active_idx = idx
                self._pl_transitioning = False
            else:
                if not self._pl_transitioning:
                    self._pl_transitioning = True
                    self._do_pl_transition()

        # update per-row time labels
        for cont in self._containers:
            for ri, slot in enumerate(
                    cont["slots"]):
                lbl = slot["row_time_lbl"]
                if (cont is active_cont
                        and ri == active_idx):
                    lbl.config(
                        text=_fmt_dur(row_t),
                        fg=ACCENT)
                else:
                    lbl.config(
                        text=_fmt_dur(
                            slot["config"]
                            .duration),
                        fg=MUTED)

        self._sync_stop_all_btn()
        self.root.after(80, self._tick)