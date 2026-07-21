import tkinter as tk

from hertz_forge.audio import get_output_devices
from ..engine import PlaylistEngine

from .style import StyleMixin
from .helpers import HelperMixin
from .build import BuildMixin
from .playlist_ui import PlaylistMixin
from .row_ui import RowMixin
from .interactions import InteractionMixin
from .transport import TransportMixin

try:
    from tkinterdnd2 import DND_FILES
    _HAS_DND = True
except ImportError:
    _HAS_DND = False


class App(StyleMixin, HelperMixin, BuildMixin,
          PlaylistMixin, RowMixin,
          InteractionMixin, TransportMixin):

    def __init__(self):
        self._playlists    = []
        self._containers   = []
        self.eng           = PlaylistEngine()
        self.output_devices = get_output_devices()
        self._playing_cont = None

        self._pl_loop       = True
        self._pl_shuffle    = True
        self._pl_play_order = []

        self._row_drag = {"active": False}
        self._pl_drag  = {"active": False}

        self._pl_transitioning = False
        self._pending_pl = None

        if _HAS_DND:
            from tkinterdnd2 import TkinterDnD
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title(
            "Hertz Forge — Playlists")
        self.root.geometry("505x720")
        self.root.minsize(505, 360)
        self.root.configure(bg="#0c0c18")

        self._style()
        self._build()

        if _HAS_DND:
            self.root.drop_target_register(
                DND_FILES)
            self.root.dnd_bind(
                "<<DropEnter>>",
                lambda e:
                    self._show_drop_overlay())
            self.root.dnd_bind(
                "<<DropLeave>>",
                lambda e:
                    self._hide_drop_overlay())
            self.root.dnd_bind(
                "<<Drop>>", self._on_drop)

        self._apply_device()
        self._add_playlist("Playlist 1")
        self._tick()

    def run(self):
        self.root.protocol(
            "WM_DELETE_WINDOW", self._quit)
        self.root.mainloop()

    def _quit(self):
        if self.eng.playing:
            self.eng.stop()
        self.root.destroy()