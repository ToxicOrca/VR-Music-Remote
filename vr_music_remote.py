"""
VR Music Remote
===============

A lightweight, always-on-top media controller designed for VR overlays
like Desktop+. It shows the current track title + album art (when available)
using Windows Global Media Session, and provides media/volume controls via
system media keys.

Notes
-----
- Windows only (uses Windows Global Media Session + Win32 media keys).
- Uses a normal window so Desktop+ can reliably enumerate/select it.
- Cursor is hidden over this window to reduce VR HUD clutter.
"""

import asyncio
import ctypes
import io
import threading
import tkinter as tk

from PIL import Image, ImageTk
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
)
from winsdk.windows.storage.streams import DataReader


# ----------------------------- UI CONFIG -----------------------------
WINDOW_W = 760
WINDOW_H = 290

BG = "#111111"
CHIP_BG = "#1e1e1e"
CHIP_BG_ACTIVE = "#2a2a2a"

ART_SIZE = 86

# Marquee (slow, VR-friendly)
MARQUEE_ENABLED = True
MARQUEE_WINDOW_CHARS = 36
MARQUEE_DELAY_MS = 350         # how fast it scrolls
MARQUEE_START_PAUSE_MS = 3500  # pause before scrolling begins
MARQUEE_GAP = "   •   "        # spacing between repeats


# ----------------------- SYSTEM MEDIA KEY INPUT ----------------------
user32 = ctypes.WinDLL("user32", use_last_error=True)
KEYEVENTF_KEYUP = 0x0002

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF


def press_vk(vk: int) -> None:
    """Send a global media key press (down + up)."""
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


# -------------------- NOW PLAYING + THUMBNAIL ------------------------
async def get_now_playing_and_art():
    """
    Returns (title, artist, img_bytes).

    img_bytes may be None if artwork is not available.
    """
    mgr = await MediaManager.request_async()
    session = mgr.get_current_session()
    if not session:
        return ("Nothing playing", "", None)

    props = await session.try_get_media_properties_async()
    title = (props.title or "").strip()
    artist = (props.artist or "").strip()

    img_bytes = None
    thumb = getattr(props, "thumbnail", None)
    if thumb is not None:
        try:
            stream = await thumb.open_read_async()
            size = int(stream.size)
            if size > 0:
                reader = DataReader(stream)
                await reader.load_async(size)
                buf = bytearray(size)
                reader.read_bytes(buf)
                img_bytes = bytes(buf)
                reader.close()
        except Exception:
            img_bytes = None

    if not title and not artist:
        title = "Playing (no metadata)"

    return (title, artist, img_bytes)


# ------------------------------ APP UI ------------------------------
class VRMusicRemote(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VR Music Remote")

        # Keep a NORMAL window so Desktop+ can select it (you can crop title bar in Desktop+)
        self.overrideredirect(False)

        self.attributes("-topmost", True)
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.configure(bg=BG)

        # Hide mouse cursor over this window (reduces VR distraction)
        self.configure(cursor="none")

        # Artwork / title state
        self._art_size = ART_SIZE
        self._photo = None

        # Marquee state
        self._stop = False
        self._marquee_run = ""
        self._marquee_i = 0
        self._marquee_job = None
        self._marquee_pause_job = None

        # Build widgets
        self._build_ui()

        # Async updater thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._runner, daemon=True)
        self._thread.start()

        # Close handling
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self) -> None:
        # Header row (art + title)
        header = tk.Frame(self, bg=BG, highlightthickness=0, bd=0)
        header.pack(fill="x", padx=12, pady=(10, 6))

        art_box = tk.Frame(
            header, bg="#222222",
            width=self._art_size, height=self._art_size,
            highlightthickness=0, bd=0,
        )
        art_box.pack(side="left")
        art_box.pack_propagate(False)

        self.art_label = tk.Label(art_box, bg="#222222")
        self.art_label.pack(fill="both", expand=True)

        title_col = tk.Frame(header, bg=BG, highlightthickness=0, bd=0)
        title_col.pack(side="left", fill="x", expand=True, padx=(12, 0))

        self.now_playing_var = tk.StringVar(value="🎵 (loading...)")
        title_lbl = tk.Label(
            title_col,
            textvariable=self.now_playing_var,
            fg="white",
            bg=BG,
            font=("Segoe UI", 18, "bold"),
            anchor="w",
        )
        title_lbl.pack(fill="x")

        # Buttons grid
        btn_frame = tk.Frame(self, bg=BG, highlightthickness=0, bd=0)
        btn_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        for c in range(3):
            btn_frame.grid_columnconfigure(c, weight=1)

        btn_frame.grid_rowconfigure(0, weight=1, minsize=66)
        btn_frame.grid_rowconfigure(1, weight=1, minsize=66)

        big_font = ("Segoe UI Emoji", 22)

        def mkbtn(icon: str, cmd, col: int, row: int) -> None:
            b = tk.Button(
                btn_frame,
                text=icon,
                command=cmd,
                font=big_font,
                relief="flat",
                bd=0,
                highlightthickness=0,
                takefocus=0,
                fg="white",
                bg=CHIP_BG,
                activebackground=CHIP_BG_ACTIVE,
                activeforeground="white",
                padx=10,
                pady=2,
            )
            b.grid(row=row, column=col, padx=12, pady=8, sticky="nsew")

        mkbtn("⏮", lambda: press_vk(VK_MEDIA_PREV_TRACK), 0, 0)
        mkbtn("⏯", lambda: press_vk(VK_MEDIA_PLAY_PAUSE), 1, 0)
        mkbtn("⏭", lambda: press_vk(VK_MEDIA_NEXT_TRACK), 2, 0)

        mkbtn("🔉", lambda: press_vk(VK_VOLUME_DOWN), 0, 1)
        mkbtn("🔇", lambda: press_vk(VK_VOLUME_MUTE), 1, 1)
        mkbtn("🔊", lambda: press_vk(VK_VOLUME_UP), 2, 1)

    # -------------------------- MARQUEE --------------------------
    def _start_marquee(self, text: str) -> None:
        # Cancel any existing jobs
        if self._marquee_job is not None:
            try:
                self.after_cancel(self._marquee_job)
            except Exception:
                pass
            self._marquee_job = None

        if self._marquee_pause_job is not None:
            try:
                self.after_cancel(self._marquee_pause_job)
            except Exception:
                pass
            self._marquee_pause_job = None

        if not MARQUEE_ENABLED:
            self.now_playing_var.set(text)
            return

        t = text.strip()
        if len(t) <= MARQUEE_WINDOW_CHARS:
            self.now_playing_var.set(t)
            return

        # Show start, pause, then scroll
        self.now_playing_var.set(t[:MARQUEE_WINDOW_CHARS])
        self._marquee_run = t + MARQUEE_GAP + t
        self._marquee_i = 0
        self._marquee_pause_job = self.after(MARQUEE_START_PAUSE_MS, self._tick_marquee)

    def _tick_marquee(self) -> None:
        if self._stop or not self._marquee_run:
            return

        n = len(self._marquee_run)
        i = self._marquee_i % n
        shown = (self._marquee_run[i : i + MARQUEE_WINDOW_CHARS]).ljust(MARQUEE_WINDOW_CHARS)
        self.now_playing_var.set(shown)

        self._marquee_i += 1
        self._marquee_job = self.after(MARQUEE_DELAY_MS, self._tick_marquee)

    # -------------------------- ASYNC UPDATE --------------------------
    def _runner(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._update_loop())

    def _set_art(self, img_bytes) -> None:
        if not img_bytes:
            self.art_label.configure(image="")
            self._photo = None
            return

        try:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img = img.resize((self._art_size, self._art_size), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            self.art_label.configure(image=self._photo)
        except Exception:
            self.art_label.configure(image="")
            self._photo = None

    async def _update_loop(self) -> None:
        last = None
        while not self._stop:
            try:
                title, artist, img_bytes = await get_now_playing_and_art()
                cur = (title, artist)

                if cur != last:
                    last = cur
                    line = f"🎵 {title}" if title else "🎵 (unknown)"
                    # UI updates must happen on the Tk thread
                    self.after(0, self._start_marquee, line)
                    self.after(0, self._set_art, img_bytes)

            except Exception:
                self.after(0, self._start_marquee, "🎵 (unable to read media session)")
                self.after(0, self._set_art, None)

            await asyncio.sleep(0.5)

    def destroy(self) -> None:
        # Stop marquee jobs
        self._stop = True
        if self._marquee_job is not None:
            try:
                self.after_cancel(self._marquee_job)
            except Exception:
                pass
        if self._marquee_pause_job is not None:
            try:
                self.after_cancel(self._marquee_pause_job)
            except Exception:
                pass

        # Stop asyncio loop thread
        try:
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception:
            pass

        super().destroy()


if __name__ == "__main__":
    VRMusicRemote().mainloop()
