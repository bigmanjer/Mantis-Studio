#!/usr/bin/env python3
import importlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _check_imports() -> bool:
    ok = True
    try:
        navigation = importlib.import_module("app.utils.navigation")
        labels, page_map = navigation.get_nav_config(True)
        assert "Dashboard" in labels
        assert page_map.get("Dashboard") == "home"
    except Exception as exc:  # pragma: no cover - used for CLI smoke validation
        print(f"[SMOKE] Navigation import failed: {exc}")
        ok = False

    try:
        ui = importlib.import_module("app.components.ui")
        required = ("card", "section_header", "primary_button", "stat_tile", "action_card")
        missing = [name for name in required if not hasattr(ui, name)]
        if missing:
            raise RuntimeError(f"Missing UI helpers: {', '.join(missing)}")
    except Exception as exc:  # pragma: no cover
        print(f"[SMOKE] UI import failed: {exc}")
        ok = False

    return ok


def _run_selftest() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "app.main", "--selftest"],
        check=False,
        capture_output=True,
        text=True,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip())
    return result.returncode == 0


def main() -> int:
    ok = _check_imports()
    ok = _run_selftest() and ok
    if ok:
        print("[SMOKE] PASS")
        return 0
    print("[SMOKE] FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
