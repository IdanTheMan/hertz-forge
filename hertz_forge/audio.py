# ═══════════════════════════════════════════════════════════════
#  AUDIO DEVICE DISCOVERY & ENGINE
# ═══════════════════════════════════════════════════════════════

import numpy as np
import sounddevice as sd
import wave
import time as _time


def get_output_devices():
    result = []
    for i, d in enumerate(sd.query_devices()):
        if d["max_output_channels"] > 0:
            result.append((f"{d['name']}  [{d['max_output_channels']}ch]",
                           i, d["max_output_channels"]))
    return result


def test_device_stereo(device_index, channels):
    sr = 44100; dur = 0.25
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    p = np.sin(2 * np.pi * 880 * t) * 0.4
    l = np.zeros((len(t), channels), dtype=np.float32)
    l[:, 0] = p.astype(np.float32)
    r = np.zeros((len(t), channels), dtype=np.float32)
    r[:, min(1, channels - 1)] = p.astype(np.float32)
    a = np.concatenate([
        l, np.zeros((int(sr * 0.15), channels), dtype=np.float32), r])
    sd.play(a, samplerate=sr, device=device_index, blocking=True)


class Engine:
    SR = 44100

    def __init__(self):
        self.stream = None; self.playing = False
        self._phase = 0.0;  self._t0 = 0.0
        self.carrier = 110.0; self.wave = "sine"; self.bw_freq = 40.0
        self.amp_val = 100.0; self.bi_val = 0.0
        self.binaural_on = False; self.fm_on = False
        self.fm_offset_lo = -30.0; self.fm_offset_hi = 40.0
        self.vol = 0.5; self.device_index = None; self.channels = 2

    @property
    def fm_start(self):       return self.carrier + self.fm_offset_lo
    @property
    def fm_end(self):         return self.carrier + self.fm_offset_hi
    @property
    def binaural_left(self):  return self.carrier - self.bw_freq / 2
    @property
    def binaural_right(self): return self.carrier + self.bw_freq / 2

    def _osc(self, t, f):
        p = 2 * np.pi * f * t
        if self.wave == "sine":     return np.sin(p)
        if self.wave == "triangle": return 2*np.abs(2*((p/(2*np.pi))%1)-1)-1
        if self.wave == "sawtooth": return 2*((p/(2*np.pi))%1)-1
        if self.wave == "square":   return np.sign(np.sin(p))
        return np.sin(p)

    def _render_stereo(self, t):
        bw = self.bw_freq
        out = np.zeros((len(t), 2))

        if bw <= 0:
            # no brainwave modulation — constant tone
            if self.binaural_on:
                bl = 0.6
                tone = self._osc(t, self.carrier) * bl
            else:
                tone = self._osc(t, self.carrier)
            out[:, 0] += tone; out[:, 1] += tone

        else:
            bp = 2*np.pi*bw*t; sb = np.sin(bp)
            amp = self.amp_val / 100.0; bi = self.bi_val / 100.0
            env = (1.0 - amp*0.5*(1.0 - sb)) if amp > 0 \
                  else np.ones_like(t)

            if self.binaural_on:
                bl = 0.6
                lt = self._osc(t, self.binaural_left)  * bl
                rt = self._osc(t, self.binaural_right) * bl
                lt *= env; rt *= env

                if bi > 0:
                    ps = 1 + bi*9
                    pn = np.clip(0.5 - 0.5*np.tanh(
                        ps*np.cos(bp/2 - np.pi/4)), 0, 1)
                    out[:,0] += lt * np.cos(pn*np.pi/2)
                    out[:,1] += rt * np.sin(pn*np.pi/2)
                else:
                    out[:,0] += lt; out[:,1] += rt

            else:
                if self.fm_on:
                    c = (self.fm_start+self.fm_end)/2
                    d = abs(self.fm_end-self.fm_start)/2
                    carrier = self._osc(t, c) * np.cos(
                        (d/max(bw,.01))*np.sin(bp))
                else:
                    carrier = self._osc(t, self.carrier)

                if amp > 0 or bi > 0:
                    if bi > 0:
                        ps = 1 + bi*9
                        pn = np.clip(0.5 - 0.5*np.tanh(
                            ps*np.cos(bp/2 - np.pi/4)), 0, 1)
                        out[:,0] += carrier*env*np.cos(pn*np.pi/2)
                        out[:,1] += carrier*env*np.sin(pn*np.pi/2)
                    else:
                        m = carrier*env; out[:,0] += m; out[:,1] += m
                elif self.fm_on:
                    out[:,0] += carrier*0.7; out[:,1] += carrier*0.7
                else:
                    out[:,0] += carrier; out[:,1] += carrier

        if np.max(np.abs(out)) > 1.0: out = np.tanh(out)
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
        if self.playing: return
        self._phase = 0; self._t0 = _time.time()
        self.stream = sd.OutputStream(
            samplerate=self.SR, channels=self.channels, dtype="float32",
            callback=self._cb, blocksize=2048,
            device=self.device_index)
        self.stream.start(); self.playing = True

    def stop(self):
        if not self.playing: return
        try: self.stream.stop(); self.stream.close()
        except: pass
        self.stream = None; self.playing = False

    def elapsed(self):
        return _time.time() - self._t0 if self.playing else 0

    def preview(self, n=4096):
        return self._render_stereo(np.arange(n) / self.SR)

    def save_wav(self, path, duration=120):
        total = int(self.SR * duration)
        phase = 0.0; parts = []; rem = total
        while rem > 0:
            n = min(self.SR, rem)
            t = (np.arange(n) + phase) / self.SR; phase += n
            parts.append(self._render_stereo(t)); rem -= n
        pcm = (np.concatenate(parts) * 32767).astype(np.int16)
        with wave.open(path, "w") as wf:
            wf.setnchannels(2); wf.setsampwidth(2)
            wf.setframerate(self.SR); wf.writeframes(pcm.tobytes())