import sys
import os
from pathlib import Path

# Base Paths (Supports source execution, PyInstaller onedir and onefile)
if getattr(sys, "frozen", False):
    # Running inside PyInstaller frozen executable
    BASE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = BASE_DIR

DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = DATA_DIR / "backups"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
LOGS_DIR = DATA_DIR / "logs"

# Ensure runtime writable directories exist
for directory in (DATA_DIR, BACKUPS_DIR, ATTACHMENTS_DIR, LOGS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Application Information
APP_NAME = "MEMMS"
APP_TITLE_AR = "نظام إدارة صيانة الأجهزة الطبية"
APP_TITLE_EN = "نظام إدارة صيانة الأجهزة الطبية"
APP_VERSION = "1.0.0"
APP_AUTHOR = "MEMMS Healthcare Engineering"

# Database Configuration
# Default is SQLite with WAL mode enabled; can be switched to PostgreSQL via MEMMS_DATABASE_URL environment variable
DEFAULT_SQLITE_PATH = DATA_DIR / "memms.db"
DATABASE_URL = os.getenv("MEMMS_DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")

# Security & Constraints
BCRYPT_ROUNDS = 12
MIN_PASSWORD_LENGTH = 6
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 Megabytes
ALLOWED_ATTACHMENT_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".txt", ".zip"
}

# UI & Localization (Arabic Only, RTL, Light Theme Only)
DEFAULT_LOCALE = "ar"
SUPPORTED_LOCALES = ["ar"]
DEFAULT_THEME = "light"
