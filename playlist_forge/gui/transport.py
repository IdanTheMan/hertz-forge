import os
import threading

from tkinter import filedialog, messagebox

from hertz_forge.constants import MUTED, ACCENT
from hertz_forge.audio import test_device_stereo
from ..engine import PlaylistEngine


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
        self._pl_transitioning = False
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

    # ── playlist transitions (seamless) ──

    def _do_pl_transition(self):
        """Switch to the next playlist without
        restarting the audio stream."""
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

        # ── UI: deactivate old ──
        old = self._playing_cont
        old["play_btn"].config(
            text="▶  Play")
        old["status_lbl"].config(
            text="● Stopped", fg=MUTED)
        old["frame"].config(
            highlightbackground="#333355")
        old["time_lbl"].config(text="")
        old["row_ind"].config(text="")

        # ── seamless switch — stream keeps
        #    running, only playlist data swaps
        self.eng.switch_playlist(
            new["playlist"])

        # ── UI: activate new ──
        self._playing_cont = new
        self._pl_transitioning = False
        new["play_btn"].config(
            text="■  Stop")
        new["status_lbl"].config(
            text="● Playing", fg=ACCENT)
        new["frame"].config(
            highlightbackground=ACCENT)
        new["time_lbl"].config(
            text="00:00:00")
        new["row_ind"].config(text="")
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
        container["status_lbl"].config(
            text="● Saving…", fg=ACCENT)
        self.root.update()

        save_eng = PlaylistEngine()
        save_eng.playlist = pl
        save_eng.vol = self.eng.vol

        def go():
            save_eng.save_wav(path)
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

    # ── tick ──

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
                self._pl_transitioning = False
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
                if not self._pl_transitioning:
                    self._pl_transitioning = True
                    self._do_pl_transition()
        else:
            self._set_active_row(None, -1)

        self.root.after(80, self._tick)