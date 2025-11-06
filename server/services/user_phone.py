"""Simple service to store and retrieve the user's phone number."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from ..config import DATA_DIR
from ..logging_config import logger


_USER_PHONE_PATH = DATA_DIR / "user_phone.txt"


class UserPhoneStore:
    """Simple file-based storage for the user's phone number."""

    def __init__(self, file_path: Path = _USER_PHONE_PATH):
        self._file_path = file_path
        self._lock = threading.Lock()
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the data directory exists."""
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.warning(f"Failed to create user phone directory: {exc}")

    def set_phone(self, phone_number: str) -> None:
        """Store the user's phone number."""
        with self._lock:
            try:
                self._file_path.write_text(phone_number.strip(), encoding="utf-8")
                logger.info(f"Stored user phone number: {phone_number}")
            except Exception as exc:
                logger.error(f"Failed to store user phone number: {exc}")
                raise

    def get_phone(self) -> Optional[str]:
        """Get the stored phone number, or None if not set."""
        with self._lock:
            try:
                if not self._file_path.exists():
                    return None
                phone = self._file_path.read_text(encoding="utf-8").strip()
                return phone if phone else None
            except Exception as exc:
                logger.error(f"Failed to read user phone number: {exc}")
                return None

    def clear(self) -> None:
        """Clear the stored phone number."""
        with self._lock:
            try:
                if self._file_path.exists():
                    self._file_path.unlink()
                    logger.info("Cleared user phone number")
            except Exception as exc:
                logger.error(f"Failed to clear user phone number: {exc}")


# Singleton instance
_user_phone_store: Optional[UserPhoneStore] = None


def get_user_phone_store() -> UserPhoneStore:
    """Get the singleton user phone store instance."""
    global _user_phone_store
    if _user_phone_store is None:
        _user_phone_store = UserPhoneStore()
    return _user_phone_store


__all__ = ["UserPhoneStore", "get_user_phone_store"]
