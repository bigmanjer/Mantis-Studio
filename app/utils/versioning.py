from pathlib import Path

DEFAULT_APP_VERSION = "47.0"


def get_app_version() -> str:
    version_path = Path(__file__).resolve().parents[2] / "VERSION.txt"
    try:
        version = version_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return DEFAULT_APP_VERSION
    except OSError:
        return DEFAULT_APP_VERSION
    return version or DEFAULT_APP_VERSION
