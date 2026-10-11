"""
Database Backup and Maintenance Service.
Manages automatic and manual SQLite backups and file size monitoring.
"""
import os
import shutil
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from config import DEFAULT_SQLITE_PATH, BACKUPS_DIR, BASE_DIR

# Resolve to string paths
DB_PATH = str(DEFAULT_SQLITE_PATH)


class BackupService:
    @staticmethod
    def get_backups_dir() -> str:
        b_dir = str(BACKUPS_DIR)
        os.makedirs(b_dir, exist_ok=True)
        return b_dir

    @staticmethod
    def create_backup() -> str:
        """Create a full snapshot backup of SQLite database using sqlite3 online backup API."""
        backups_dir = BackupService.get_backups_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"memms_backup_{timestamp}.db"
        backup_path = os.path.join(backups_dir, backup_filename)

        # Use SQLite backup API for safe live copying without locking conflicts
        src_conn = sqlite3.connect(DB_PATH)
        dst_conn = sqlite3.connect(backup_path)
        try:
            with dst_conn:
                src_conn.backup(dst_conn, pages=100)
        finally:
            dst_conn.close()
            src_conn.close()

        return backup_path

    @staticmethod
    def restore_backup(backup_path: str) -> bool:
        """Restore database from a given backup file."""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found at: {backup_path}")

        # Dispose SQLAlchemy connections before live restore to avoid file lock conflicts
        try:
            from src.core.database import engine
            engine.dispose()
        except Exception:
            pass

        # Live restore via SQLite backup API
        src_conn = sqlite3.connect(backup_path)
        dst_conn = sqlite3.connect(DB_PATH)
        try:
            with dst_conn:
                src_conn.backup(dst_conn, pages=100)
        finally:
            dst_conn.close()
            src_conn.close()

        return True

    @staticmethod
    def get_database_info() -> Dict[str, Any]:
        """Return file size and last modified date of database."""
        if not os.path.exists(DB_PATH):
            return {"exists": False, "size_bytes": 0, "size_mb": 0.0, "last_modified": None}

        stat = os.stat(DB_PATH)
        size_bytes = stat.st_size
        size_mb = round(size_bytes / (1024 * 1024), 2)
        mod_time = datetime.fromtimestamp(stat.st_mtime)

        return {
            "exists": True,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "last_modified": mod_time.strftime("%Y-%m-%d %H:%M:%S")
        }


backup_service = BackupService()
