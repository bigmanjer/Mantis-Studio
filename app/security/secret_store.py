"""Protected local secret storage.

On Windows this uses DPAPI, binding encrypted values to the current Windows
user profile.  Other platforms deliberately report protected storage as
unavailable so callers do not accidentally persist plaintext secrets.
"""
from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes
import os
from typing import Dict, Tuple


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def protected_storage_available() -> bool:
    return os.name == "nt"


def _blob_from_bytes(data: bytes) -> Tuple[_DATA_BLOB, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data)
    blob = _DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    return blob, buffer


def _bytes_from_blob(blob: _DATA_BLOB) -> bytes:
    return ctypes.string_at(blob.pbData, blob.cbData)


def protect_secret(value: str) -> Dict[str, str]:
    if not protected_storage_available():
        raise RuntimeError("Protected secret storage is unavailable on this OS.")
    raw = (value or "").encode("utf-8")
    in_blob, _in_buffer = _blob_from_bytes(raw)
    out_blob = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    ok = crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise RuntimeError("Windows DPAPI could not protect the secret.")
    try:
        encrypted = _bytes_from_blob(out_blob)
    finally:
        kernel32.LocalFree(out_blob.pbData)
    return {"kind": "windows-dpapi", "value": base64.b64encode(encrypted).decode("ascii")}


def reveal_secret(record: Dict[str, str]) -> str:
    if not record:
        return ""
    if record.get("kind") != "windows-dpapi":
        return ""
    if not protected_storage_available():
        return ""
    encrypted = base64.b64decode(record.get("value") or "")
    in_blob, _in_buffer = _blob_from_bytes(encrypted)
    out_blob = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        return ""
    try:
        return _bytes_from_blob(out_blob).decode("utf-8")
    finally:
        kernel32.LocalFree(out_blob.pbData)
