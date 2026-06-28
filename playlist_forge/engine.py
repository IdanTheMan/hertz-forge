# ═══════════════════════════════════════════════════════════════
#  PLAYLIST ENGINE — sequential row playback by duration
# ═══════════════════════════════════════════════════════════════

import numpy as np
import sounddevice as sd
import wave
import time as _time


def _osc(t, wave, freq):
    p = 2 * np.pi * freq * t
    if wave == "sine":     return np.sin(p)
    if wave == "triangle": return 2*np.abs(2*((p/(2*np.pi))%1)-1)-1
    if wave == "sawtooth": return 2*((p/(2*np.pi))%1)-1
    if wave == "square":   return np.sign(np.sin(p))
    return np.sin(p)


class ChannelConfig:
    def __init__(self):
        self.carrier      = 110.0
        self.wave         = "sine"
        self.bw_freq      = 40.0
        self.amp_val      = 100.0
        self.bi_val       = 0.0
        self.fm_on        = False
        self.fm_offset_lo = -30.0
        self.fm_offset_hi = 40.0

    def render(self, t, primary_side,
               carrier_ov=None, wave_ov=None, bw_ov=None):
        carrier = (carrier_ov if carrier_ov is not None
                   else self.carrier)
        wave    = (wave_ov if wave_ov is not None
                   else self.wave)
        bw      = (bw_ov if bw_ov is not None
                   else self.bw_freq)

        if bw <= 0:
            sig = _osc(t, wave, carrier)
            if primary_side == "left":
                return sig.copy(), np.zeros(len(t),
                                            dtype=np.float32)
            return np.zeros(len(t), dtype=np.float32), \
                   sig.copy()

        bp  = 2 * np.pi * bw * t
        sb  = np.sin(bp)
        amp = self.amp_val / 100.0
        bi  = self.bi_val  / 100.0

        if self.fm_on:
            fs = carrier + self.fm_offset_lo
            fe = carrier + self.fm_offset_hi
            c  = (fs + fe) / 2
            d  = abs(fe - fs) / 2
            car = _osc(t, wave, c) * np.cos(
                (d / max(bw, 0.01)) * np.sin(bp))
        else:
            car = _osc(t, wave, carrier)

        if amp > 0:
            env = 1.0 - amp * 0.5 * (1.0 - sb)
            sig = car * env
        elif self.fm_on:
            sig = car * 0.7
        else:
            sig = car

        left  = np.zeros(len(t), dtype=np.float32)
        right = np.zeros(len(t), dtype=np.float32)

        if bi > 0:
            ps = 1 + bi * 9
            pn = np.clip(0.5 - 0.5 * np.tanh(
                ps * np.cos(bp / 2 - np.pi / 4)), 0, 1)
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
        self.left         = ChannelConfig()
        self.right        = ChannelConfig()
        self.binaural_on  = False
        self.bi_carrier   = 110.0
        self.bi_wave      = "sine"
        self.bi_bw        = 40.0
        self.duration     = 120.0        # seconds


class Playlist:
    def __init__(self, name="Playlist 1"):
        self.name = name
        self.rows = []

    def add_row(self):
        r = RowConfig(); self.rows.append(r); return r

    def insert_row(self, i):
        r = RowConfig(); self.rows.insert(i, r); return r

    def remove_row(self, i):
        if 0 <= i < len(self.rows):
            self.rows.pop(i)

    def total_duration(self):
        return sum(r.duration for r in self.rows)


class PlaylistEngine:
    SR = 44100

    def __init__(self):
        self.stream = None;  self.playing = False
        self._phase = 0.0;   self._t0 = 0.0
        self.playlist = None
        self.vol = 0.5
        self.device_index = None
        self.channels = 2

    def _current_row(self):
        """Return (row_index, row_elapsed) based on playlist time."""
        if not self.playlist or not self.playlist.rows:
            return -1, 0.0

        t = self.elapsed()
        acc = 0.0
        for i, row in enumerate(self.playlist.rows):
            dur = row.duration
            # last row with 0 duration plays forever
            if i == len(self.playlist.rows) - 1 and dur <= 0:
                return i, t - acc
            if dur <= 0:
                continue
            if t < acc + dur:
                return i, t - acc
            acc += dur

        # past all durations → stop
        return -1, 0.0

    def _render_stereo(self, t):
        left  = np.zeros(len(t))
        right = np.zeros(len(t))

        idx, _ = self._current_row()
        if idx >= 0 and idx < len(self.playlist.rows):
            row = self.playlist.rows[idx]
            if row.binaural_on:
                l_car = row.bi_carrier - row.bi_bw / 2
                r_car = row.bi_carrier + row.bi_bw / 2
                ll, lr = row.left.render(
                    t, "left", l_car, row.bi_wave,
                    row.bi_bw)
                rl, rr = row.right.render(
                    t, "right", r_car, row.bi_wave,
                    row.bi_bw)
            else:
                ll, lr = row.left.render(t, "left")
                rl, rr = row.right.render(t, "right")
            left  += ll + rl
            right += lr + rr

        out = np.column_stack([left, right])
        if np.max(np.abs(out)) > 1.0:
            out = np.tanh(out)
        return (out * self.vol).astype(np.float32)

    def _render_device(self, t):
        s = self._render_stereo(t); ch = self.channels
        if ch == 1:
            return ((s[:,0]+s[:,1])*0.5
                    ).reshape(-1, 1).astype(np.float32)
        if ch == 2:
            return s
        o = np.zeros((len(t), ch), dtype=np.float32)
        o[:,0] = s[:,0]; o[:,1] = s[:,1]
        return o

    def _cb(self, outdata, frames, time_info, status):
        t = (np.arange(frames)+self._phase)/self.SR
        self._phase += frames
        r = self._render_device(t); nc = outdata.shape[1]
        if r.shape[1] < nc:
            p = np.zeros((frames, nc), dtype=np.float32)
            p[:,:r.shape[1]] = r; outdata[:] = p
        elif r.shape[1] > nc:
            outdata[:] = r[:,:nc]
        else:
            outdata[:] = r

    def start(self):
        if self.playing:
            return
        self._phase = 0; self._t0 = _time.time()
        self.stream = sd.OutputStream(
            samplerate=self.SR, channels=self.channels,
            dtype="float32", callback=self._cb,
            blocksize=2048, device=self.device_index)
        self.stream.start(); self.playing = True

    def stop(self):
        if not self.playing:
            return
        try:
            self.stream.stop(); self.stream.close()
        except:
            pass
        self.stream = None; self.playing = False

    def elapsed(self):
        return _time.time() - self._t0 if self.playing else 0

    def save_wav(self, path, duration=120):
        # render sequentially by row
        self._phase = 0.0
        total = int(self.SR * duration)
        parts = [];  rem = total
        saved_t0 = self._t0
        while rem > 0:
            n = min(self.SR, rem)
            t = (np.arange(n) + self._phase) / self.SR
            self._phase += n
            parts.append(self._render_stereo(t))
            rem -= n
        self._t0 = saved_t0
        pcm = (np.concatenate(parts) * 32767).astype(np.int16)
        with wave.open(path, "w") as wf:
            wf.setnchannels(2); wf.setsampwidth(2)
            wf.setframerate(self.SR)
            wf.writeframes(pcm.tobytes())