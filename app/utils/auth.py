"""Local account management for Mantis Studio."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


ACCOUNTS_FILENAME = ".mantis_users.json"
PBKDF2_ROUNDS = 200_000


def _accounts_path(base_projects_dir: str) -> Path:
    root = Path(base_projects_dir or "projects")
    root.mkdir(parents=True, exist_ok=True)
    return root / ACCOUNTS_FILENAME


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _safe_username_slug(username: str) -> str:
    allowed = []
    for ch in _normalize_username(username):
        if ch.isalnum() or ch in {"_", "-"}:
            allowed.append(ch)
        elif ch in {" ", "."}:
            allowed.append("_")
    slug = "".join(allowed).strip("_")
    return slug or "user"


def _load_accounts(base_projects_dir: str) -> Dict[str, Any]:
    path = _accounts_path(base_projects_dir)
    if not path.exists():
        return {"version": 1, "users": []}
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("users"), list):
            data.setdefault("version", 1)
            return data
    except Exception:
        pass
    return {"version": 1, "users": []}


def _save_accounts(base_projects_dir: str, data: Dict[str, Any]) -> None:
    path = _accounts_path(base_projects_dir)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _hash_password(password: str, salt_hex: str) -> str:
    password_bytes = (password or "").encode("utf-8")
    salt_bytes = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password_bytes, salt_bytes, PBKDF2_ROUNDS)
    return digest.hex()


def _new_password_record(password: str) -> Tuple[str, str]:
    salt_hex = os.urandom(16).hex()
    return salt_hex, _hash_password(password, salt_hex)


def _sanitize_user_payload(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user.get("id"),
        "username": user.get("username", ""),
        "display_name": user.get("display_name") or user.get("username", ""),
        "created_at": float(user.get("created_at") or time.time()),
        "last_login": float(user.get("last_login") or time.time()),
    }


def register_user(
    username: str,
    password: str,
    display_name: str = "",
    *,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    username_clean = (username or "").strip()
    username_key = _normalize_username(username_clean)
    if len(username_key) < 3:
        return False, "Username must be at least 3 characters.", None
    if len(password or "") < 8:
        return False, "Password must be at least 8 characters.", None

    data = _load_accounts(base_projects_dir)
    users = data.setdefault("users", [])
    for existing in users:
        if _normalize_username(existing.get("username", "")) == username_key:
            return False, "Username already exists.", None

    now = time.time()
    salt_hex, password_hash = _new_password_record(password)
    user = {
        "id": str(uuid.uuid4()),
        "username": username_clean,
        "display_name": (display_name or "").strip() or username_clean,
        "username_key": username_key,
        "password_salt": salt_hex,
        "password_hash": password_hash,
        "created_at": now,
        "last_login": now,
        "disabled": False,
    }
    users.append(user)
    _save_accounts(base_projects_dir, data)
    return True, "Account created.", _sanitize_user_payload(user)


def authenticate_user(
    username: str,
    password: str,
    *,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    username_key = _normalize_username(username)
    if not username_key or not password:
        return False, "Enter username and password.", None

    data = _load_accounts(base_projects_dir)
    users = data.get("users", [])
    for user in users:
        if _normalize_username(user.get("username", "")) != username_key:
            continue
        if bool(user.get("disabled", False)):
            return False, "Account is disabled.", None
        salt_hex = user.get("password_salt", "")
        expected_hash = user.get("password_hash", "")
        if not salt_hex or not expected_hash:
            return False, "Account record is invalid.", None
        actual_hash = _hash_password(password, salt_hex)
        if not hmac.compare_digest(actual_hash, expected_hash):
            return False, "Invalid username or password.", None
        user["last_login"] = time.time()
        _save_accounts(base_projects_dir, data)
        return True, "Signed in.", _sanitize_user_payload(user)

    return False, "Invalid username or password.", None


def get_user_projects_dir(user_id: str, base_projects_dir: str = "projects") -> str:
    safe_user_id = _safe_username_slug(str(user_id or "user"))
    target = Path(base_projects_dir or "projects") / "users" / safe_user_id
    target.mkdir(parents=True, exist_ok=True)
    return str(target)


def apply_login_to_session(session_state: Any, user: Dict[str, Any], base_projects_dir: str = "projects") -> None:
    session_state["user_id"] = user.get("id")
    session_state["username"] = user.get("username", "")
    session_state["display_name"] = user.get("display_name") or user.get("username", "")
    session_state["projects_dir"] = get_user_projects_dir(session_state["user_id"], base_projects_dir)


def logout_session(session_state: Any) -> None:
    for key in (
        "user_id",
        "username",
        "display_name",
        "project",
        "projects_dir",
        "last_project_path",
    ):
        session_state[key] = None


def is_authenticated(session_state: Any) -> bool:
    return bool(session_state.get("user_id"))


def get_current_user(session_state: Any) -> Optional[Dict[str, Any]]:
    if not is_authenticated(session_state):
        return None
    return {
        "id": session_state.get("user_id"),
        "username": session_state.get("username", ""),
        "display_name": session_state.get("display_name") or session_state.get("username", ""),
    }

