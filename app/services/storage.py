from __future__ import annotations

import os
import time
from typing import Optional

from app.config.settings import AppConfig


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



def resolve_storage_dir(storage_dir: Optional[str]) -> str:
    storage_dir = storage_dir or AppConfig.PROJECTS_DIR
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir
