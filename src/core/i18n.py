"""
Internationalization and Localization Manager for MEMMS.
Pure Arabic (RTL) engine with embedded dictionary fallback for 100% executable reliability.
"""
from typing import Dict, Any, Callable, List
from src.core.arabic_translations import ARABIC_DICTIONARY

try:
    from PySide6.QtCore import Qt, QObject, Signal
    from PySide6.QtWidgets import QApplication
    HAS_PYSIDE = True
except ImportError:
    HAS_PYSIDE = False
    Qt = None
    QApplication = None


_DEFAULT_SENTINEL = object()


class I18nManager:
    """
    Central Internationalization engine.
    Ensures 100% pure Arabic translation in all environments (source, PyInstaller, standalone EXE).
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18nManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.current_locale = "ar"
        # Initialize with fully embedded Arabic dictionary
        self.translations: Dict[str, Dict[str, Any]] = {
            "ar": ARABIC_DICTIONARY
        }
        self._listeners: List[Callable[[], None]] = []
        self._initialized = True

    def set_locale(self, locale_code: str = "ar"):
        """Enforces Arabic locale and updates Qt layout direction to RTL."""
        self.current_locale = "ar"
        self.apply_qt_direction()

        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                print(f"[i18n] Error in locale change listener: {e}")

    def apply_qt_direction(self):
        """Sets the Qt Application layout direction to RTL."""
        if HAS_PYSIDE and QApplication.instance() is not None:
            QApplication.instance().setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def is_rtl(self) -> bool:
        """Always True for Arabic UI."""
        return True

    def register_listener(self, callback: Callable[[], None]):
        """Registers a callback when the locale changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[], None]):
        """Unregisters a callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def tr(self, key_path: str, default: Any = _DEFAULT_SENTINEL, **kwargs) -> Any:
        """
        Translates a dotted key path like 'app.title' or 'common.save' from Arabic dictionary.
        """
        current_dict = self.translations.get("ar", {})
        keys = key_path.split(".")
        val = current_dict
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                val = None
                break
        
        if val is None:
            if default is not _DEFAULT_SENTINEL:
                return default
            return key_path
        
        if isinstance(val, str) and kwargs:
            try:
                return val.format(**kwargs)
            except Exception:
                return val
        return str(val) if val is not None else key_path


# Global singleton instance and shortcut helper
i18n = I18nManager()

def tr(key_path: str, default: Any = _DEFAULT_SENTINEL, **kwargs) -> Any:
    """Convenience shortcut for translation lookup."""
    return i18n.tr(key_path, default=default, **kwargs)

