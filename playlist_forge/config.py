# ═══════════════════════════════════════════════════════════════
#  ROW CONFIG — save · load · naming
# ═══════════════════════════════════════════════════════════════

"""
Row-configuration save / load utilities.

Each saved config is a small JSON file with the extension .hfc
(Hertz Forge Config).

Naming format:  bw_modulation_carrier+wave_duration_extras
─────────────────────────────────────────────────────────────
  10_a_440csi_30s                 10 Hz BW, amplitude, 440 Hz sine, 30 s
  40_a_440ctri_60s                40 Hz BW, amplitude, 440 Hz triangle, 60 s
  40_b_110csi_30s                 binaural, center 110 Hz sine
  10_fm_440csaw_120s              FM on, 440 Hz sawtooth
  40_st_440csq_30s                bilateral panning, 440 Hz square
  40_st_fm_440csi_30s             bilateral + FM
  10_a_440csi_30s_amp80           non-default amplitude
  40_a_L440csiR460ctri_30s        split L/R carriers & waves

Wave shortcuts:  si  tri  saw  sq
Carrier suffix:  c   (e.g. 440c → 440 Hz carrier)
Modulation:      a = amplitude · b = binaural · st = bilateral · fm = FM
"""

import json
import re
from .engine import ChannelConfig, RowConfig

WAVE_SHORT = {
    "sine":     "si",
    "triangle": "tri",
    "sawtooth": "saw",
    "square":   "sq",
}


# ── naming ──────────────────────────────────────────────────

def _wave_tag(wave):
    return WAVE_SHORT.get(wave, wave[:2])


def generate_row_name(rc):
    """Return a concise, human-readable name for a row config.

    Order:  bw → modulation → carrier+wave → duration → extras
    """
    parts = []

    # ── 1. brainwave frequency ──
    if rc.binaural_on:
        bw = rc.bi_bw
    else:
        bw = rc.left.bw_freq

    if bw == int(bw):
        parts.append(f"{int(bw)}")
    else:
        parts.append(f"{bw:.1f}")

    # ── 2. modulation type(s) ──
    mods = []
    if rc.binaural_on:
        mods.append("b")
    if not rc.binaural_on:
        if rc.left.bi_val > 0 or rc.right.bi_val > 0:
            mods.append("st")
    if rc.left.fm_on or rc.right.fm_on:
        mods.append("fm")
    if not mods:
        mods.append("a")
    parts.append("_".join(mods))

    # ── 3. carrier + waveform ──
    if rc.binaural_on:
        c = rc.bi_carrier
        w = _wave_tag(rc.bi_wave)
        parts.append(f"{c:.0f}c{w}")
    else:
        lc  = rc.left.carrier
        rc_c = rc.right.carrier
        lw  = _wave_tag(rc.left.wave)
        rw  = _wave_tag(rc.right.wave)

        if lc == rc_c and rc.left.wave == rc.right.wave:
            parts.append(f"{lc:.0f}c{lw}")
        elif lc == rc_c:
            parts.append(f"{lc:.0f}cL{lw}R{rw}")
        elif rc.left.wave == rc.right.wave:
            if rc_c == 0:
                parts.append(f"L{lc:.0f}c{lw}")
            elif lc == 0:
                parts.append(f"R{rc_c:.0f}c{lw}")
            else:
                parts.append(f"L{lc:.0f}R{rc_c:.0f}c{lw}")
        else:
            if rc_c == 0:
                parts.append(f"L{lc:.0f}c{lw}")
            elif lc == 0:
                parts.append(f"R{rc_c:.0f}c{rw}")
            else:
                parts.append(
                    f"L{lc:.0f}c{lw}R{rc_c:.0f}c{rw}")

    # ── 4. duration ──
    dur = rc.duration
    if dur == int(dur):
        parts.append(f"{int(dur)}s")
    else:
        parts.append(f"{dur:.1f}s")

    # ── 5. extras (non-default values) ──

    # amplitude
    if rc.binaural_on:
        la = rc.bi_left_amp
        ra = rc.bi_right_amp
        if la != 0 or ra != 0:
            if la == ra:
                parts.append(f"amp{la:.0f}")
            elif ra == 0:
                parts.append(f"Lamp{la:.0f}")
            elif la == 0:
                parts.append(f"Ramp{ra:.0f}")
            else:
                parts.append(f"Lamp{la:.0f}Ramp{ra:.0f}")
    else:
        la = rc.left.amp_val
        ra = rc.right.amp_val
        if la != 100 or ra != 100:
            if la == ra:
                parts.append(f"amp{la:.0f}")
            elif ra == 0:
                parts.append(f"Lamp{la:.0f}")
            elif la == 0:
                parts.append(f"Ramp{ra:.0f}")
            else:
                parts.append(f"Lamp{la:.0f}Ramp{ra:.0f}")

    # volume
    lv = rc.left.vol
    rv = rc.right.vol
    if lv != 100 or rv != 100:
        if lv == rv:
            parts.append(f"vol{lv:.0f}")
        elif rv == 100:
            parts.append(f"Lvol{lv:.0f}")
        elif lv == 100:
            parts.append(f"Rvol{rv:.0f}")
        else:
            parts.append(f"Lvol{lv:.0f}Rvol{rv:.0f}")

    return "_".join(parts)


def suggested_filename(rc):
    """Safe filename like ``10_a_440csi_30s.hfc``."""
    name = generate_row_name(rc)
    name = re.sub(r"[^\w\-.]", "_", name)
    return f"{name}.hfc"


# ── serialisation ───────────────────────────────────────────

def _ch_to_dict(ch):
    return {
        "carrier":      ch.carrier,
        "wave":         ch.wave,
        "bw_freq":      ch.bw_freq,
        "amp_val":      ch.amp_val,
        "bi_val":       ch.bi_val,
        "fm_on":        ch.fm_on,
        "fm_offset_lo": ch.fm_offset_lo,
        "fm_offset_hi": ch.fm_offset_hi,
        "vol":          ch.vol,
    }


def _dict_to_ch(d, side):
    ch = ChannelConfig(side)
    ch.carrier      = d.get("carrier",      ch.carrier)
    ch.wave         = d.get("wave",         ch.wave)
    ch.bw_freq      = d.get("bw_freq",      ch.bw_freq)
    ch.amp_val      = d.get("amp_val",      ch.amp_val)
    ch.bi_val       = d.get("bi_val",       ch.bi_val)
    ch.fm_on        = d.get("fm_on",        ch.fm_on)
    ch.fm_offset_lo = d.get("fm_offset_lo", ch.fm_offset_lo)
    ch.fm_offset_hi = d.get("fm_offset_hi", ch.fm_offset_hi)
    ch.vol          = d.get("vol",          ch.vol)
    return ch


def row_to_dict(rc):
    """Serialize a ``RowConfig`` to a JSON-friendly dict."""
    return {
        "hertz_forge_config": 1,
        "name": generate_row_name(rc),
        "row": {
            "duration":     rc.duration,
            "binaural_on":  rc.binaural_on,
            "bi_carrier":   rc.bi_carrier,
            "bi_wave":      rc.bi_wave,
            "bi_bw":        rc.bi_bw,
            "bi_left_amp":  rc.bi_left_amp,
            "bi_right_amp": rc.bi_right_amp,
            "sync_on":      rc.sync_on,
            "adv_on":       rc.adv_on,
            "left":         _ch_to_dict(rc.left),
            "right":        _ch_to_dict(rc.right),
        },
    }


def dict_to_row(d):
    """Deserialize a dict into a fresh ``RowConfig``."""
    r  = d["row"]
    rc = RowConfig()
    rc.duration     = r.get("duration",     rc.duration)
    rc.binaural_on  = r.get("binaural_on",  rc.binaural_on)
    rc.bi_carrier   = r.get("bi_carrier",   rc.bi_carrier)
    rc.bi_wave      = r.get("bi_wave",      rc.bi_wave)
    rc.bi_bw        = r.get("bi_bw",        rc.bi_bw)
    rc.bi_left_amp  = r.get("bi_left_amp",  rc.bi_left_amp)
    rc.bi_right_amp = r.get("bi_right_amp", rc.bi_right_amp)
    rc.sync_on      = r.get("sync_on",      rc.sync_on)
    rc.adv_on       = r.get("adv_on",       rc.adv_on)
    rc.left  = _dict_to_ch(r.get("left",  {}), "left")
    rc.right = _dict_to_ch(r.get("right", {}), "right")
    return rc


# ── file I/O ────────────────────────────────────────────────

def save_row(rc, path):
    """Write one row config to a ``.hfc`` JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(row_to_dict(rc), f, indent=2)


def load_row(path):
    """Read a ``.hfc`` file and return a ``RowConfig``."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return dict_to_row(data)


def load_rows(paths):
    """Load several ``.hfc`` files; skip any that fail."""
    rows = []
    for p in paths:
        if p.lower().endswith(".hfc"):
            try:
                rows.append(load_row(p))
            except Exception:
                pass
    return rows