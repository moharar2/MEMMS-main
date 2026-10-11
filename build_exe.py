"""
Automated PyInstaller Build Script for MEMMS.
Builds a standalone, production-ready Windows .exe with all necessary fonts, assets, and hidden imports bundled.
"""
import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def build():
    print("=" * 60)
    print("MEMMS — Building Standalone Executable (.exe)")
    print("=" * 60)

    # Command line arguments for PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "MEMMS",
        "--add-data", f"{BASE_DIR / 'src'};src",
        "--collect-all", "qtawesome",
        "--collect-all", "sqlalchemy",
        "--hidden-import", "src.models",
        "--hidden-import", "src.models.user",
        "--hidden-import", "src.models.role",
        "--hidden-import", "src.models.equipment",
        "--hidden-import", "src.models.work_order",
        "--hidden-import", "src.models.preventive",
        "--hidden-import", "src.models.inventory",
        "--hidden-import", "src.models.contract",
        "--hidden-import", "src.models.technician",
        "--hidden-import", "src.models.hospital",
        "--hidden-import", "src.models.audit",
        "--hidden-import", "src.core.arabic_translations",
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        str(BASE_DIR / "main.py")
    ]

    print("Running command:")
    print(" ".join(cmd))
    print("\nBuilding... please wait.\n")

    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode == 0:
        dist_dir = BASE_DIR / "dist" / "MEMMS"
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Executable is located in: {dist_dir / 'MEMMS.exe'}")
        print("=" * 60)
    else:
        print("\nBUILD FAILED with exit code:", result.returncode)

if __name__ == "__main__":
    build()
