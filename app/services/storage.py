from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Iterator, Optional

from app.config.settings import AppConfig

logger = logging.getLogger("MANTIS")


def _acquire_lock(lock_path: str, timeout: int, retry_sleep: float) -> bool:
    start = time.time()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
                lock_file.write(str(os.getpid()))
            return True
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(lock_path)
            except OSError:
                age = 0
            if age > max(timeout * 5, 5):
                try:
                    os.remove(lock_path)
                except OSError:
                    pass
            if time.time() - start >= timeout:
                return False
            time.sleep(retry_sleep)


def _release_lock(lock_path: str) -> None:
    try:
        os.remove(lock_path)
    except OSError:
        pass


@contextmanager
def file_lock(
    path: str,
    timeout: int = AppConfig.SAVE_LOCK_TIMEOUT,
    retry_sleep: float = AppConfig.SAVE_LOCK_RETRY_SLEEP,
) -> Iterator[bool]:
    """Context manager for file locking.

    Yields ``True`` when the lock was acquired, ``False`` otherwise.
    The lock is always released on exit when it was acquired.

    Usage::

        with file_lock(filepath) as acquired:
            if not acquired:
                logger.error("Could not acquire lock")
                return
            # ... safe file operations ...
    """
    lock_path = path + ".lock"
    acquired = _acquire_lock(lock_path, timeout, retry_sleep)
    if not acquired:
        logger.error("Lock timeout for %s after %ss", path, timeout)
    try:
        yield acquired
    finally:
        if acquired:
            _release_lock(lock_path)


def resolve_storage_dir(storage_dir: Optional[str]) -> str:
    storage_dir = storage_dir or AppConfig.PROJECTS_DIR
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir
