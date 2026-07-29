import sys, os

log_path = os.path.join(os.path.expanduser("~"), "Videos", "resolve_downloads", "log.txt")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
sys.stdout = open(log_path, "a")
sys.stderr = sys.stdout

# Windows Resolve scripting modules path
sys.path.append(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")
import DaVinciResolveScript as dvr
import yt_dlp
import threading

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QButtonGroup, QProgressBar
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, Signal, QObject, QUrl

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Videos", "resolve_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Adjust to wherever ffmpeg.exe actually lives on your machine.
# Run `where ffmpeg` in Command Prompt to find it if unsure.
FFMPEG_LOCATION = r"C:\ffmpeg\bin"


def download(url, audio_only=False, progress_callback=None):
    def hook(d):
        if d["status"] == "downloading" and progress_callback:
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total else 0
            progress_callback({
                "percent": percent,
                "downloaded_str": d.get("_downloaded_bytes_str", "").strip(),
                "total_str": d.get("_total_bytes_str", "").strip(),
                "speed_str": d.get("_speed_str", "").strip(),
                "eta_str": d.get("_eta_str", "").strip(),
            })

    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "format": "bestaudio/best" if audio_only else "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "ffmpeg_location": FFMPEG_LOCATION,
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "progress_hooks": [hook],
    }
    if audio_only:
        ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        if audio_only:
            filepath = os.path.splitext(filepath)[0] + ".mp3"
        return filepath


def import_to_resolve(filepath):
    resolve = dvr.scriptapp("Resolve")
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()

    imported = media_pool.ImportMedia([filepath])
    if not imported:
        return False
    timeline = project.GetCurrentTimeline()
    if timeline is None:
        media_pool.CreateEmptyTimeline("YT Import Timeline")
    media_pool.AppendToTimeline(imported)
    return True


class WorkerSignals(QObject):
    status = Signal(str, str)
    progress = Signal(dict)
    finished = Signal()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-downloader")
        self.resize(1920, 1080)

        self.current_video_url = ""

        self.signals = WorkerSignals()
        self.signals.status.connect(self.set_status)
        self.signals.progress.connect(self.update_progress)
        self.signals.finished.connect(lambda: self.download_btn.setEnabled(True))

        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Import to Resolve")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.youtube.com"))
        self.browser.setMinimumHeight(380)
        self.browser.urlChanged.connect(self.on_url_changed)
        layout.addWidget(self.browser)

        format_row = QHBoxLayout()
        self.mp4_radio = QRadioButton("MP4 (video)")
        self.mp3_radio = QRadioButton("MP3 (audio)")
        self.mp4_radio.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.mp4_radio)
        group.addButton(self.mp3_radio)
        format_row.addWidget(self.mp4_radio)
        format_row.addWidget(self.mp3_radio)
        format_row.addStretch()
        layout.addLayout(format_row)

        self.download_btn = QPushButton("Download & Import")
        self.download_btn.clicked.connect(self.run_pipeline)
        layout.addWidget(self.download_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_detail = QLabel("")
        self.progress_detail.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_detail)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.apply_styles()

    def on_url_changed(self, qurl):
        url_str = qurl.toString()
        if "youtube.com/watch" in url_str or "youtu.be/" in url_str:
            self.current_video_url = url_str
            self.set_status(f"Ready: {url_str[:40]}...", "lightgreen")
        else:
            self.current_video_url = ""

    def set_status(self, message, color="white"):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")

    def update_progress(self, data):
        percent = data.get("percent", 0)
        self.progress_bar.setValue(int(percent))
        detail = (
            f"{data.get('downloaded_str','')} / {data.get('total_str','')}  "
            f"\u2022  {data.get('speed_str','')}  \u2022  ETA {data.get('eta_str','')}"
        )
        self.progress_detail.setText(detail)

    def run_pipeline(self):
        url = self.current_video_url
        audio_only = self.mp3_radio.isChecked()

        if not url:
            self.set_status("Navigate to a video first", "orange")
            return

        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_detail.setText("")
        self.set_status("Downloading...", "white")

        def worker():
            try:
                path = download(
                    url, audio_only,
                    progress_callback=lambda d: self.signals.progress.emit(d)
                )
                self.signals.status.emit("Importing to Resolve...", "white")
                ok = import_to_resolve(path)
                if ok:
                    self.signals.status.emit("Done \u2713", "lightgreen")
                else:
                    self.signals.status.emit("Import failed", "red")
            except Exception as e:
                self.signals.status.emit(f"Error: {e}", "red")
            finally:
                self.signals.finished.emit()

        threading.Thread(target=worker, daemon=True).start()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #272727;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#title {
                font-size: 20px;
                font-weight: bold;
                color: #ffffff;
            }
            QLabel {
                color: #cccccc;
                font-size: 13px;
            }
            QRadioButton {
                color: #dddddd;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #ff0000;
            }
            QRadioButton::indicator:checked {
                background-color: #ff0000;
            }
            QPushButton {
                background-color: #ff0000;
                color: white;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QPushButton:disabled {
                background-color: #a3a3a3;
                color: #272727;
            }
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #a3a3a3;
                height: 12px;
            }
            QProgressBar::chunk {
                background-color: #ff0000;
                border-radius: 6px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())