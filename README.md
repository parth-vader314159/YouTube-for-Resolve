<div align="center">

# YouTube for DaVinci Resolve

**Browse, download, and drop straight onto your timeline — without leaving Resolve.**

![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/use-personal--only-red)

[**⬇ Download for macOS**](https://github.com/parth-vader314159/YouTube-for-Resolve/releases/latest)

</div>

---

## What it does

A native panel that lives inside DaVinci Resolve's Scripts menu. Browse YouTube inside the app, hit download, and the clip lands directly in your Media Pool and onto your current timeline — no browser tab-switching, no manual importing.

<div align="center">
<img src="assets/Screenshot 2026-07-30 at 17.46.44.png" width="500" >
</div>

## Features

- 🎬 **Embedded browser** — search and navigate YouTube without leaving the app
- ⬇️ **MP4 or MP3** — grab video or extract audio only
- 📊 **Live progress** — real-time download size, speed, and ETA
- 🎞️ **Auto-import** — clip is added to your Media Pool and current timeline automatically
- 🌑 **Dark, native-feeling UI** styled to match Resolve

<div align="center">
<img src="assets/Screenshot 2026-07-30 at 17.47.01.png" width="500" >
</div>

## Installation

1. [Download the installer](https://github.com/parth-vader314159/yt-resolve/releases/latest)
2. Run `YTtoResolveInstaller.pkg`
3. Open DaVinci Resolve → **Workspace → Scripts** → look for the plugin in the list
4. Click to launch

> **First run only:** macOS may warn that the installer is from an unidentified developer. Right-click the `.pkg` → **Open** to bypass this.

## Requirements

- DaVinci Resolve (installed, with a project open)
- Python 3.10+ with `PySide6`, `PySide6-Addons`, and `yt-dlp` installed
- `ffmpeg` installed (`brew install ffmpeg`)

## A note on use

This tool is intended for downloading content you own the rights to, or that's licensed for reuse (your own uploads, Creative Commons footage, stock media, etc.) — not for pulling arbitrary copyrighted video off YouTube. Use responsibly.

---

<div align="center">
<sub>Built by <a href="https://github.com/parth-vader314159">parth-vader314159</a></sub>
</div>
