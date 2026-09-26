import subprocess
import platform
import hashlib
import os
import re

FOLDER_ICON = "\uf07b"
DEFAULT_FILE_ICON = "\uf15b"
FILE_ICONS = {
    ("txt", "md", "rtf", "log"): "\uf0f6",
    (
        "png",
        "jpg",
        "jpeg",
        "webp",
        "svg",
        "gif",
        "raw",
        "tiff",
        "tif",
        "heic",
        "heif",
        "bmp",
    ): "\uf03e",
    ("py", "pyc"): "\ue606",
    ("cpp", "c++", "cxx", "cc", "hpp", "h++", "hxx", "hh"): "\ue61d",
    ("c", "h"): "\ue61e",
    ("js", "jsx"): "\ue781",
    ("ts", "tsx"): "\ue8ca",
    ("html", "htm"): "\ue736",
    ("css"): "\ue749",
    ("json"): "\ue60b",
    ("java", "class", "jar"): "\ue738",
    ("mp3", "wav", "flac", "m4a", "aac", "ogg"): "\ue638",
    ("mp4", "mkv", "mov", "avi", "webm"): "\uf03d",
    ("pdf"): "\uf1c1",
    ("zip", "tar", "7z", "rar", "gz"): "\uf1c6",
    ("exe", "sh", "bat"): "\ue795",
    ("app"): "\ue711",
    ("enc"): "\udb80\ude21",
}


def get_file_icon(extension: str):
    if not extension:
        return DEFAULT_FILE_ICON

    for exts, icon in FILE_ICONS.items():
        if extension in exts:
            return icon

    return DEFAULT_FILE_ICON


if platform.system() == "Windows":
    import ctypes

    def is_app_focused():
        foreground_window = ctypes.windll.user32.GetForegroundWindow()
        return foreground_window != 0

    def open_file(file_path: str):
        os.startfile(file_path)

elif platform.system() == "Darwin":
    try:
        from AppKit import NSApplication

        def is_app_focused():
            return NSApplication.sharedApplication().isActive()

    except ImportError:

        def is_app_focused():
            return True

    def open_file(file_path: str):
        subprocess.run(["open", "--", file_path])

else:

    def is_app_focused():
        return True

    def open_file(file_path: str):
        subprocess.run(["xdg-open", "--", file_path])


# from ai
# The extension comes from an untrusted source: manifest keys reach this code
# via open_file, and encryptr.py only checks `type(self._root) == dict` on load.
# Allowlist it hard rather than trying to strip "bad" characters.
_SAFE_EXT = re.compile(r"\A\.[A-Za-z0-9]{1,16}\Z")


def _safe_ext(name: str) -> str:
    ext = os.path.splitext(name)[1]
    return ext if _SAFE_EXT.match(ext) else ""


def make_temp_path(temp_dir: str, path: list[str], name: str) -> str:
    h = hashlib.blake2b(digest_size=16)

    for part in [*path, name]:
        b = part.encode("utf-8", "surrogateescape")
        h.update(len(b).to_bytes(4, "big"))
        h.update(b)

    return os.path.join(temp_dir, h.hexdigest() + _safe_ext(name))
