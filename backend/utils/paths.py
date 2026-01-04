import sys
import os
from pathlib import Path


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def get_app_dir():
    if is_frozen():
        argv0 = Path(sys.argv[0])
        try:
            resolved = argv0.resolve()
        except Exception:
            resolved = argv0
        if resolved.suffix.lower() == ".exe":
            return resolved.parent
        return Path(os.getcwd()).resolve()
    return Path(__file__).resolve().parent.parent


def get_resource_dir():
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return get_app_dir()


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_dist_dir():
    return get_resource_dir() / "dist"


def get_previews_dir():
    return ensure_dir(get_app_dir() / "previews")

def get_resource_previews_dir():
    return get_resource_dir() / "previews"


def get_uploads_dir():
    base = get_app_dir()
    return ensure_dir(base / "uploads")


def get_data_dir():
    base = get_app_dir()
    return ensure_dir(base / "data")


def find_preview_file(filename: str):
    safe_name = Path(filename).name
    candidates = [
        get_previews_dir() / safe_name,
        get_resource_previews_dir() / safe_name,
    ]
    for p in candidates:
        try:
            if p.is_file():
                return p
        except Exception:
            continue
    return None
