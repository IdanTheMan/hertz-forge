# ═══════════════════════════════════════════════════════════════
#  PLAYLIST ENGINE
# ═══════════════════════════════════════════════════════════════

import random
import numpy as np
import sounddevice as sd
import wave
import time as _time


# ┌──────────────────────────────────────────────────────────┐
#  EDIT THESE to change what every new row starts with
# ────────────────────────────────────────────────────────────

ROW_DEFAULTS = {
    "duration":     1.0,

    "left_carrier":  440.0,
    "left_wave":     "sine",
    "left_bw":       40.0,
    "left_amp":      100.0,
    "left_bi":       0.0,
    "left_fm":       False,
    "left_fm_lo":    -30.0,
    "left_fm_hi":    40.0,

    "right_carrier": 440.0,
    "right_wave":    "sine",
    "right_bw":      40.0,
    "right_amp":     100.0,
    "right_bi":      0.0,
    "right_fm":      False,
    "right_fm_lo":   -30.0,
    "right_fm_hi":   40.0,

    "binaural_on":   False,
    "bi_carrier":    110.0,
    "bi_wave":       "sine",
    "bi_bw":         40.0,
    "bi_left_amp":   0.0,
    "bi_right_amp":  0.0,

    "sync_on":       True,
    "adv_on":        False,
}

# └──────────────────────────────────────────────────────────┘


def _osc(t, wave, freq):
    p = 2 * np.pi * freq * t
    if wave == "sine":
        return np.sin(p)
    if wave == "triangle":
        return 2 * np.abs(
            2 * ((p / (2 * np.pi)) % 1) - 1
        ) - 1
    if wave == "sawtooth":
        return 2 * ((p / (2 * np.pi)) % 1) - 1
    if wave == "square":
        return np.sign(np.sin(p))
    return np.sin(p)


class ChannelConfig:
    def __init__(self, side="left"):
        d = ROW_DEFAULTS
        self.carrier      = d[f"{side}_carrier"]
        self.wave         = d[f"{side}_wave"]
        self.bw_freq      = d[f"{side}_bw"]
        self.amp_val      = d[f"{side}_amp"]
        self.bi_val       = d[f"{side}_bi"]
        self.fm_on        = d[f"{side}_fm"]
        self.fm_offset_lo = d[f"{side}_fm_lo"]
        self.fm_offset_hi = d[f"{side}_fm_hi"]

    def render(self, t, primary_side,
               carrier_ov=None,
               wave_ov=None,
               bw_ov=None,
               amp_ov=None):
        carrier = (carrier_ov
                   if carrier_ov is not None
                   else self.carrier)
        wave = (wave_ov
                if wave_ov is not None
                else self.wave)
        bw = (bw_ov
              if bw_ov is not None
              else self.bw_freq)

        if bw <= 0:
            sig = _osc(t, wave, carrier)
            if primary_side == "left":
                return (sig.copy(),
                        np.zeros(len(t),
                                 dtype=np.float32))
            return (np.zeros(len(t),
                             dtype=np.float32),
                    sig.copy())

        bp  = 2 * np.pi * bw * t
        sb  = np.sin(bp)
        amp = ((amp_ov
                if amp_ov is not None
                else self.amp_val) / 100.0)
        bi  = self.bi_val  / 100.0

        if self.fm_on:
            fs = carrier + self.fm_offset_lo
            fe = carrier + self.fm_offset_hi
            c  = (fs + fe) / 2
            d  = abs(fe - fs) / 2
            car = (_osc(t, wave, c)
                   * np.cos(
                       (d / max(bw, 0.01))
                       * np.sin(bp)))
        else:
            car = _osc(t, wave, carrier)

        if amp > 0:
            env = 1.0 - amp * 0.5 * (1.0 - sb)
            sig = car * env
        elif self.fm_on:
            sig = car * 0.7
        else:
            sig = car

        left  = np.zeros(len(t),
                         dtype=np.float32)
        right = np.zeros(len(t),
                         dtype=np.float32)

        if bi > 0:
            ps = 1 + bi * 9
            pn = np.clip(
                0.5 - 0.5 * np.tanh(
                    ps * np.cos(
                        bp / 2 - np.pi / 4)),
                0, 1)
            cos_pan = np.cos(pn * np.pi / 2)
            sin_pan = np.sin(pn * np.pi / 2)
            if primary_side == "left":
                left  = sig * cos_pan
                right = sig * sin_pan
            else:
                left  = sig * sin_pan
                right = sig * cos_pan
        else:
            if primary_side == "left":
                left = sig
            else:
                right = sig

        return left, right


class RowConfig:
    def __init__(self):
        d = ROW_DEFAULTS
        self.left        = ChannelConfig("left")
        self.right       = ChannelConfig("right")
        self.binaural_on = d["binaural_on"]
        self.bi_carrier  = d["bi_carrier"]
        self.bi_wave     = d["bi_wave"]
        self.bi_bw       = d["bi_bw"]
        self.bi_left_amp = d["bi_left_amp"]
        self.bi_right_amp = d["bi_right_amp"]
        self.duration    = d["duration"]
        self.included    = True
        self.name        = ""
        self.sync_on     = d["sync_on"]
        self.adv_on      = d["adv_on"]


class Playlist:
    def __init__(self, name="Playlist 1"):
        self.name         = name
        self.rows         = []
        self.row_loop     = False
        self.row_shuffle  = False
        self.play_rows    = 0     # 0 = all
        self._play_order  = []

    def add_row(self):
        r = RowConfig()
        self.rows.append(r)
        self._rebuild_order()
        return r

    def insert_row(self, i):
        r = RowConfig()
        self.rows.insert(i, r)
        self._rebuild_order()
        return r

    def remove_row(self, i):
        if 0 <= i < len(self.rows):
            self.rows.pop(i)
            self._rebuild_order()

    def _rebuild_order(self):
        """Always natural order. Shuffle
        happens in prepare_playback (once) or
        _current_row (per cycle)."""
        self._play_order = [
            i for i, r in enumerate(self.rows)
            if r.included
        ]

    def prepare_playback(self):
        self._rebuild_order()
        if (self.row_shuffle
                and len(self._play_order) > 1):
            random.shuffle(self._play_order)

    def total_duration(self):
        return sum(
            r.duration for r in self.rows
            if r.included)

    def playback_duration(self):
        """Duration of the rows that will
        actually play (respects play_rows)."""
        included = [
            r for r in self.rows if r.included]
        if self.play_rows > 0:
            included = included[:self.play_rows]
        return sum(r.duration for r in included)


class PlaylistEngine:
    SR = 44100

    def __init__(self):
        self.stream       = None
        self.playing       = False
        self._phase        = 0.0
        self._t0           = 0.0
        self.playlist      = None
        self.vol           = 0.5
        self.device_index  = None
        self.channels      = 2
        self._last_cycle   = 0

    def _build_playable(self, order, looping):
        playable = []
        for idx in order:
            dur = self.playlist.rows[idx].duration
            if dur > 0:
                playable.append((idx, dur))
            elif (not looping
                  and idx == order[-1]):
                playable.append((idx, 0))
        return playable

    def _find_row(self, playable, t):
        acc = 0.0
        for idx, dur in playable:
            if dur <= 0:
                return idx, t - acc
            if t < acc + dur:
                return idx, t - acc
            acc += dur
        if playable:
            return playable[-1][0], t
        return -1, 0.0

    def _current_row(self):
        if (not self.playlist
                or not self.playlist.rows):
            return -1, 0.0

        t = self.elapsed()
        order = self.playlist._play_order
        looping = self.playlist.row_loop
        shuffling = self.playlist.row_shuffle
        play_rows = self.playlist.play_rows

        # limit by play_rows
        if (play_rows > 0
                and len(order) > play_rows):
            order = order[:play_rows]

        playable = self._build_playable(
            order, looping)

        if not playable:
            if order:
                return order[0], t
            return -1, 0.0

        total = sum(
            d for _, d in playable if d > 0)

        if not looping:
            if total > 0 and t >= total:
                return -1, 0.0
            return self._find_row(playable, t)

        if total <= 0:
            return playable[0][0], t

        cycle_num = int(t / total)
        pos = t - cycle_num * total

        if (shuffling
                and cycle_num != self._last_cycle
        ):
            self._last_cycle = cycle_num
            # fresh random each cycle
            included = [
                i for i, r
                in enumerate(self.playlist.rows)
                if r.included]
            if included:
                if (play_rows > 0
                        and play_rows
                            < len(included)):
                    new_order = random.sample(
                        included, play_rows)
                else:
                    new_order = list(included)
                    random.shuffle(new_order)
                # persist to _play_order so
                # next call picks it up
                self.playlist._play_order = \
                    new_order
                order = new_order
                playable = self._build_playable(
                    order, True)
                # recalculate with new total
                total = sum(
                    d for _, d in playable
                    if d > 0)
                if total > 0:
                    cycle_num = int(t / total)
                    pos = (t
                           - cycle_num * total)

        return self._find_row(playable, pos)

    def _render_stereo(self, t):
        left  = np.zeros(len(t))
        right = np.zeros(len(t))

        idx, _ = self._current_row()
        if (idx >= 0
                and idx < len(
                    self.playlist.rows)):
            row = self.playlist.rows[idx]
            if row.binaural_on:
                l_car = (row.bi_carrier
                         - row.bi_bw / 2)
                r_car = (row.bi_carrier
                         + row.bi_bw / 2)
                ll, lr = row.left.render(
                    t, "left", l_car,
                    row.bi_wave, row.bi_bw,
                    row.bi_left_amp)
                rl, rr = row.right.render(
                    t, "right", r_car,
                    row.bi_wave, row.bi_bw,
                    row.bi_right_amp)
            else:
                ll, lr = row.left.render(
                    t, "left")
                rl, rr = row.right.render(
                    t, "right")
            left  += ll + rl
            right += lr + rr

        out = np.column_stack([left, right])
        if np.max(np.abs(out)) > 1.0:
            out = np.tanh(out)
        return (out * self.vol).astype(
            np.float32)

    def _render_device(self, t):
        s  = self._render_stereo(t)
        ch = self.channels
        if ch == 1:
            return (
                (s[:, 0] + s[:, 1]) * 0.5
            ).reshape(-1, 1).astype(np.float32)
        if ch == 2:
            return s
        o = np.zeros(
            (len(t), ch), dtype=np.float32)
        o[:, 0] = s[:, 0]
        o[:, 1] = s[:, 1]
        return o

    def _cb(self, outdata, frames,
            time_info, status):
        t = ((np.arange(frames) + self._phase)
             / self.SR)
        self._phase += frames
        r  = self._render_device(t)
        nc = outdata.shape[1]
        if r.shape[1] < nc:
            p = np.zeros(
                (frames, nc), dtype=np.float32)
            p[:, :r.shape[1]] = r
            outdata[:] = p
        elif r.shape[1] > nc:
            outdata[:] = r[:, :nc]
        else:
            outdata[:] = r

    def start(self):
        if self.playing:
            return
        self._phase      = 0
        self._t0         = _time.time()
        self._last_cycle = 0
        self.stream = sd.OutputStream(
            samplerate=self.SR,
            channels=self.channels,
            dtype="float32",
            callback=self._cb,
            blocksize=2048,
            device=self.device_index)
        self.stream.start()
        self.playing = True

    def stop(self):
        if not self.playing:
            return
        try:
            self.stream.stop()
            self.stream.close()
        except:
            pass
        self.stream  = None
        self.playing = False

    def elapsed(self):
        if self.playing:
            return _time.time() - self._t0
        return 0

    def save_wav(self, path, duration=120):
        self._phase = 0.0
        total = int(self.SR * duration)
        parts = []
        rem   = total
        saved_t0 = self._t0
        while rem > 0:
            n = min(self.SR, rem)
            t = ((np.arange(n) + self._phase)
                 / self.SR)
            self._phase += n
            parts.append(
                self._render_stereo(t))
            rem -= n
        self._t0 = saved_t0
        pcm = (np.concatenate(parts) * 32767
               ).astype(np.int16)
        with wave.open(path, "w") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(self.SR)
            wf.writeframes(pcm.tobytes())

    def switch_playlist(self, playlist):
        """Switch to a new playlist without
        restarting the audio stream."""
        self.playlist = playlist
        playlist.prepare_playback()
        self._t0 = _time.time()
        self._last_cycle = 0