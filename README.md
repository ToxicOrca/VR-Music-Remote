# 🎵 VR Music Remote

**VR Music Remote** is a lightweight, always-on-top media controller designed for VR users.  
It works especially well with **Desktop+**, allowing you to control system media playback without leaving VR.

The app displays the currently playing track (with album art when available) and provides simple, VR-friendly media and volume controls.

---

## ✨ Features

- ▶️ Play / Pause  
- ⏮ Previous / ⏭ Next track  
- 🔊 Volume Up / Down / Mute  
- 🎶 Now Playing title with slow marquee scrolling (VR-readable speed)  
- 🖼 Album artwork via Windows Global Media Session  
- 🪟 Normal window (Desktop+ selectable and crop-friendly)  
- 🖱 Mouse cursor hidden over the window (clean VR HUD feel)  
- 🪶 Lightweight (Tkinter-based, minimal overhead)

---

## 🧠 How It Works

VR Music Remote uses:
- **Windows Global Media Session** to read currently playing media
- **System media keys** to control playback  
  (works with Spotify, YouTube, YouTube Music, VLC, etc.)
- A standard desktop window so tools like Desktop+ can easily capture and display it in VR

---

## 🖥 Requirements

- **Windows 10 or Windows 11**
- **Python 3.10+**
- Desktop overlay software (recommended: **Desktop+**)

---

## 📦 Installation (Python)

```bash
pip install pillow winsdk
python vr_music_remote.py
```

---

## 🚀 Usage (Recommended with Desktop+)

1. Launch **VR Music Remote**
2. Add the window in **Desktop+**
3. Crop out the title bar if desired
4. Position it as a VR HUD
5. Interact using your VR laser pointer or mouse

---

## 📦 Packaging as an EXE

You can package VR Music Remote as a standalone Windows executable using **PyInstaller**.

```bash
pip install pyinstaller pillow winsdk
pyinstaller --noconsole --onefile --name "VR Music Remote" --icon vr_music_remote.ico vr_music_remote.py
```

The executable will be created in:

```text
dist/VR Music Remote.exe
```

---

## 🖼 Icon

The icon was generated with ChatGPT (OpenAI) and is included in the repository.

---

## 📄 License

This project is released under the **MIT License**.

You are free to use, modify, and distribute this software.

---

## 🙏 Credits

- **Project Author:** ToxicOrca  
- **Development Assistance:** ChatGPT (OpenAI)  
  - Assisted with Python/Tkinter architecture
  - Async media session handling
  - UX refinements for VR use
- **Icon Creation Assistance:** ChatGPT (OpenAI)

ChatGPT was used as a collaborative development and design assistant throughout this project.

---

