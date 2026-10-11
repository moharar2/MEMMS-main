"""Verify that main.py boots cleanly end-to-end, then quits."""
import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_boot_test():
    # Patch QApplication.exec to return immediately so main() exits.
    from PySide6.QtWidgets import QApplication
    real_exec = QApplication.exec
    QApplication.exec = lambda self: 0  # type: ignore

    import main as app_main  # noqa: E402

    rc = app_main.main()
    print(f"main() returned: {rc}")
    print("OK: full main.py boot path succeeded.")
    return rc


if __name__ == "__main__":
    run_boot_test()
