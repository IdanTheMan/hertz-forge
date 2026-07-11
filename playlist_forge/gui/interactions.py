import tkinter as tk
from tkinter import filedialog

from hertz_forge.constants import ACCENT
from ..config import save_row, load_rows, suggested_filename


class InteractionMixin:

    # ══════════════════════════════════════════════════════════
    #  DRAG AND DROP — ROWS (cross-playlist)
    # ══════════════════════════════════════════════════════════

    def _start_row_drag(self, container,
                        idx, event):
        if (self._row_drag.get("active")
                or self._pl_drag.get("active")):
            return
        handle = container["slots"][idx]["grip"]
        self._row_drag = {
            "active":        True,
            "src":           idx,
            "src_container": container,
            "tgt_container": container,
            "handle":        handle,
            "start_y":       event.y_root,
            "moved":         False,
            "indicator":     None,
            "last_tgt_row":  -1,
            "last_tgt_ci":   self._containers
                             .index(container),
        }
        handle.grab_set()
        handle.bind(
            "<B1-Motion>",
            self._on_row_drag_motion)
        handle.bind(
            "<ButtonRelease-1>",
            self._on_row_drag_end)

    def _find_drop_target_global(self, event):
        """Return ``(container_index, row_index)``
        or ``(None, None)``."""
        for ci, cont in enumerate(
                self._containers):
            if cont.get("collapsed"):
                continue

            slots = cont["slots"]

            if not slots:
                fy = (cont["frame"]
                      .winfo_rooty())
                fh = (cont["frame"]
                      .winfo_height())
                if fy <= event.y_root <= fy + fh:
                    return ci, 0
                continue

            for i, slot in enumerate(slots):
                wy = (slot["border"]
                      .winfo_rooty())
                wh = (slot["border"]
                      .winfo_height())
                if event.y_root < wy + wh / 2:
                    return ci, i

            # past all rows — still inside this
            # container?
            fy = (cont["frame"]
                  .winfo_rooty())
            fh = (cont["frame"]
                  .winfo_height())
            if event.y_root <= fy + fh:
                return ci, len(slots)

        return None, None

    def _on_row_drag_motion(self, event):
        d = self._row_drag
        if not d.get("active"):
            return

        if not d["moved"]:
            if abs(event.y_root
                   - d["start_y"]) < 6:
                return
            d["moved"] = True
            src_c = d["src_container"]
            d["indicator"] = tk.Frame(
                src_c["rows_frame"],
                bg=ACCENT, height=2)
            src_c["slots"][d["src"]][
                "border"].config(bg="#2a2a5a")

        tgt_ci, tgt_row = (
            self._find_drop_target_global(event))
        if tgt_ci is None:
            return

        tgt_cont = self._containers[tgt_ci]

        # ── highlight management ──
        prev = d.get("tgt_container")
        if prev is not tgt_cont:
            if prev is not d["src_container"]:
                try:
                    prev["frame"].config(
                        highlightbackground=(
                            "#333355"))
                except (tk.TclError, KeyError):
                    pass
            if tgt_cont is not d["src_container"]:
                tgt_cont["frame"].config(
                    highlightbackground=ACCENT)
            d["tgt_container"] = tgt_cont

        # ── move indicator ──
        if (tgt_ci != d["last_tgt_ci"]
                or tgt_row != d["last_tgt_row"]):
            d["last_tgt_ci"] = tgt_ci
            d["last_tgt_row"] = tgt_row

            if d["indicator"]:
                try:
                    d["indicator"].destroy()
                except tk.TclError:
                    pass

            d["indicator"] = tk.Frame(
                tgt_cont["rows_frame"],
                bg=ACCENT, height=2)
            d["tgt_container"] = tgt_cont

            self._position_row_indicator_in(
                tgt_cont, d, tgt_row)

    def _on_row_drag_end(self, event):
        d = self._row_drag
        if not d.get("active"):
            return

        handle = d["handle"]
        try:
            handle.grab_release()
            handle.unbind("<B1-Motion>")
            handle.unbind("<ButtonRelease-1>")
        except tk.TclError:
            pass

        if d["moved"]:
            src     = d["src"]
            src_c   = d["src_container"]
            tgt_ci, tgt_row = (
                self._find_drop_target_global(
                    event))
            tgt_c = (self._containers[tgt_ci]
                     if tgt_ci is not None
                     else src_c)

            # ── cleanup ──
            if d["indicator"]:
                try:
                    d["indicator"].destroy()
                except tk.TclError:
                    pass

            try:
                src_c["slots"][src][
                    "border"].config(
                        bg="#222244")
            except (tk.TclError, IndexError):
                pass

            if tgt_c is not src_c:
                try:
                    tgt_c["frame"].config(
                        highlightbackground=(
                            "#333355"))
                except (tk.TclError, KeyError):
                    pass

            # ── dispatch ──
            if tgt_ci is not None:
                if tgt_c is src_c:
                    if (tgt_row != src
                            and tgt_row
                                != src + 1):
                        self._reorder_rows(
                            src_c, src, tgt_row)
                else:
                    self._move_row_cross(
                        src_c, src,
                        tgt_c, tgt_row)

        self._row_drag = {"active": False}

    def _position_row_indicator_in(
            self, container, d, target):
        slots = container["slots"]
        rf = container["rows_frame"]
        ind = d["indicator"]

        if target < len(slots):
            y = (slots[target]["border"]
                 .winfo_rooty()
                 - rf.winfo_rooty())
        elif slots:
            last = slots[-1]["border"]
            y = (last.winfo_rooty()
                 + last.winfo_height()
                 - rf.winfo_rooty())
        else:
            y = 0

        ind.place(
            x=8, y=y,
            relwidth=1.0, width=-16, height=2)

    def _rebuild_container_slots(self, container):
        """Destroy and recreate all slots for a
        container, then renumber and update
        duration."""
        for slot in container["slots"]:
            slot["border"].destroy()
        container["slots"].clear()
        for i in range(
                len(container["playlist"].rows)):
            self._create_slot(container, i)
        self._renumber(container)
        container["playlist"]._rebuild_order()
        self._update_pl_dur(container)

    def _reorder_rows(self, container,
                      src, target):
        pl = container["playlist"]
        row = pl.rows.pop(src)
        if target > src:
            target -= 1
        pl.rows.insert(target, row)

        self._rebuild_container_slots(container)
        self._refresh_scroll()

    def _move_row_cross(self, src_cont, src_idx,
                        tgt_cont, tgt_idx):
        """Move a row from one playlist to
        another."""
        src_pl = src_cont["playlist"]
        tgt_pl = tgt_cont["playlist"]

        row = src_pl.rows.pop(src_idx)
        tgt_pl.rows.insert(tgt_idx, row)

        self._rebuild_container_slots(src_cont)
        self._rebuild_container_slots(tgt_cont)
        self._refresh_scroll()

    # ══════════════════════════════════════════════════════════
    #  DRAG AND DROP — PLAYLISTS (unchanged)
    # ══════════════════════════════════════════════════════════

    def _start_pl_drag(self, grip_widget,
                       event):
        if (self._pl_drag.get("active")
                or self._row_drag.get("active")):
            return
        idx = None
        for i, c in enumerate(self._containers):
            if c["pl_grip"] is grip_widget:
                idx = i
                break
        if idx is None:
            return
        handle = grip_widget
        self._pl_drag = {
            "active":     True,
            "src":        idx,
            "handle":     handle,
            "start_y":    event.y_root,
            "moved":      False,
            "indicator":  None,
            "last_target": -1,
        }
        handle.grab_set()
        handle.bind(
            "<B1-Motion>",
            self._on_pl_drag_motion)
        handle.bind(
            "<ButtonRelease-1>",
            self._on_pl_drag_end)

    def _on_pl_drag_motion(self, event):
        d = self._pl_drag
        if not d.get("active"):
            return

        if not d["moved"]:
            if abs(event.y_root
                   - d["start_y"]) < 6:
                return
            d["moved"] = True
            d["indicator"] = tk.Frame(
                self._pl_frame,
                bg=ACCENT, height=2)
            self._containers[d["src"]][
                "frame"].config(
                    highlightbackground=ACCENT)

        target = self._get_pl_drop_target(event)
        if target != d["last_target"]:
            d["last_target"] = target
            self._position_pl_indicator(
                d, target)

    def _on_pl_drag_end(self, event):
        d = self._pl_drag
        if not d.get("active"):
            return

        handle = d["handle"]
        try:
            handle.grab_release()
            handle.unbind("<B1-Motion>")
            handle.unbind("<ButtonRelease-1>")
        except tk.TclError:
            pass

        if d["moved"]:
            src = d["src"]
            target = (
                self._get_pl_drop_target(event))

            if d["indicator"]:
                try:
                    d["indicator"].destroy()
                except tk.TclError:
                    pass
            try:
                self._containers[src][
                    "frame"].config(
                        highlightbackground=(
                            "#333355"))
            except (tk.TclError, IndexError):
                pass

            if (target != src
                    and target != src + 1):
                self._reorder_playlists(
                    src, target)

        self._pl_drag = {"active": False}

    def _get_pl_drop_target(self, event):
        for i, cont in enumerate(
                self._containers):
            wy = cont["frame"].winfo_rooty()
            wh = cont["frame"].winfo_height()
            if event.y_root < wy + wh / 2:
                return i
        return len(self._containers)

    def _position_pl_indicator(self, d, target):
        conts = self._containers
        pf = self._pl_frame
        ind = d["indicator"]

        if target < len(conts):
            y = (conts[target]["frame"]
                 .winfo_rooty()
                 - pf.winfo_rooty())
        elif conts:
            last = conts[-1]["frame"]
            y = (last.winfo_rooty()
                 + last.winfo_height()
                 - pf.winfo_rooty())
        else:
            y = 0

        ind.place(
            x=8, y=y,
            relwidth=1.0, width=-16, height=2)

    def _reorder_playlists(self, src, target):
        pl = self._playlists.pop(src)
        cont = self._containers.pop(src)
        if target > src:
            target -= 1
        self._playlists.insert(target, pl)
        self._containers.insert(target, cont)

        self._rebuild_pl_order()
        self._reflow_playlists()

    # ══════════════════════════════════════════════════════════
    #  CONFIG SAVE / LOAD (unchanged)
    # ══════════════════════════════════════════════════════════

    def _save_row_config(self, container, slot):
        cfg = slot["config"]
        fname = suggested_filename(cfg)
        path = filedialog.asksaveasfilename(
            defaultextension=".hfc",
            filetypes=[("Hertz Forge Config",
                        "*.hfc")],
            initialfile=fname)
        if not path:
            return
        save_row(cfg, path)

    def _load_configs_dialog(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Hertz Forge Config",
                        "*.hfc")],
            title="Load Row Configs")
        if not paths:
            return
        self._load_config_files(list(paths))

    def _load_into_playlist(self, container):
        paths = filedialog.askopenfilenames(
            filetypes=[("Hertz Forge Config",
                        "*.hfc")],
            title="Load Configs into Playlist")
        if not paths:
            return
        self._load_config_files(list(paths),
                                container)

    def _load_config_files(self, paths,
                           container=None):
        rows = load_rows(paths)
        if not rows:
            return
        if container is None:
            if not self._containers:
                self._add_playlist("Playlist 1")
            container = self._containers[-1]
        pl = container["playlist"]
        for rc in rows:
            pl.rows.append(rc)
            idx = len(pl.rows) - 1
            rc.name = f"Row {idx + 1}"
            self._create_slot(container, idx)
        pl._rebuild_order()
        self._update_pl_dur(container)
        self._refresh_scroll()

    # ══════════════════════════════════════════════════════════
    #  DRAG-AND-DROP FILES (unchanged)
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def _parse_dnd_paths(data):
        """Parse tkinterdnd2 ``<<Drop>>``
        event data into a list of file paths.
        Handles Windows brace-quoted paths
        with spaces."""
        paths, buf, brace = [], "", False
        for ch in data:
            if ch == "{":
                brace = True
                buf = ""
            elif ch == "}":
                brace = False
                paths.append(buf)
                buf = ""
            elif ch == " " and not brace:
                if buf:
                    paths.append(buf)
                    buf = ""
            else:
                buf += ch
        if buf:
            paths.append(buf)
        return [p for p in paths if p]

    def _on_drop(self, event):
        self._hide_drop_overlay()
        paths = self._parse_dnd_paths(
            event.data)
        hfc = [p for p in paths
               if p.lower().endswith(".hfc")]
        if hfc:
            self._load_config_files(hfc)

    def _show_drop_overlay(self):
        self._drop_overlay.place(
            relx=0.5, rely=0.5,
            anchor="center",
            relwidth=0.95, relheight=0.95)
        self._drop_overlay.lift()

    def _hide_drop_overlay(self):
        self._drop_overlay.place_forget()