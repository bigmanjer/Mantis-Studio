"""Local account management for Mantis Studio."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from urllib.parse import urlencode
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple


ACCOUNTS_FILENAME = ".mantis_users.json"
PBKDF2_ROUNDS = 200_000
DEFAULT_PASSWORD_ALGO = "sha256"
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 15 * 60
RESET_TOKEN_TTL_SECONDS = 60 * 60
BUILTIN_ADMIN_EMAIL = "ADMIN"
BUILTIN_ADMIN_USERNAME = "ADMIN"
BUILTIN_ADMIN_PASSWORD = "Admin@13319!"


def _accounts_path(base_projects_dir: str) -> Path:
    root = Path(base_projects_dir or "projects")
    root.mkdir(parents=True, exist_ok=True)
    return root / ACCOUNTS_FILENAME


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _is_valid_email(email: str) -> bool:
    email_clean = _normalize_email(email)
    if email_clean == _normalize_email(BUILTIN_ADMIN_EMAIL):
        return True
    if not email_clean or "@" not in email_clean:
        return False
    local, _, domain = email_clean.partition("@")
    return bool(local and "." in domain and not email_clean.startswith("@"))


def _new_account_id(users: list[Dict[str, Any]]) -> str:
    existing = {str(user.get("account_id", "")).upper() for user in users}
    while True:
        candidate = f"MNT-{uuid.uuid4().hex[:8].upper()}"
        if candidate not in existing:
            return candidate


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
        data = {"version": 1, "users": []}
        _ensure_builtin_admin(data)
        return data
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("users"), list):
            data.setdefault("version", 1)
            _ensure_account_identifiers(data)
            _ensure_builtin_admin(data)
            return data
    except Exception:
        pass
    data = {"version": 1, "users": []}
    _ensure_builtin_admin(data)
    return data


def _save_accounts(base_projects_dir: str, data: Dict[str, Any]) -> None:
    _ensure_account_identifiers(data)
    _ensure_builtin_admin(data)
    path = _accounts_path(base_projects_dir)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _hash_password(password: str, salt_hex: str, algo: str = DEFAULT_PASSWORD_ALGO) -> str:
    password_bytes = (password or "").encode("utf-8")
    salt_bytes = bytes.fromhex(salt_hex)
    normalized_algo = "sha1" if str(algo or "").lower() == "sha1" else "sha256"
    digest = hashlib.pbkdf2_hmac(normalized_algo, password_bytes, salt_bytes, PBKDF2_ROUNDS)
    return digest.hex()


def _new_password_record(password: str, algo: str = DEFAULT_PASSWORD_ALGO) -> Tuple[str, str]:
    salt_hex = os.urandom(16).hex()
    return salt_hex, _hash_password(password, salt_hex, algo=algo)


def _validate_password_strength(password: str) -> Optional[str]:
    value = password or ""
    if len(value) < 10:
        return "Password must be at least 10 characters."
    if not any(ch.islower() for ch in value):
        return "Password must include a lowercase letter."
    if not any(ch.isupper() for ch in value):
        return "Password must include an uppercase letter."
    if not any(ch.isdigit() for ch in value):
        return "Password must include a number."
    return None


def _new_recovery_code() -> str:
    raw = os.urandom(12).hex().upper()
    return "-".join(raw[i:i + 4] for i in range(0, len(raw), 4))


def _new_recovery_record(recovery_code: str) -> Tuple[str, str]:
    return _new_password_record(recovery_code)


def _new_reset_token_record(reset_token: str) -> Tuple[str, str]:
    return _new_password_record(reset_token)


def _verify_reset_token(reset_token: str, user: Dict[str, Any]) -> bool:
    salt_hex = user.get("reset_token_salt", "")
    expected_hash = user.get("reset_token_hash", "")
    expires_at = float(user.get("reset_token_expires_at") or 0)
    if not salt_hex or not expected_hash or not reset_token:
        return False
    if expires_at <= time.time():
        return False
    current_hash = _hash_password(reset_token, salt_hex, algo=DEFAULT_PASSWORD_ALGO)
    return hmac.compare_digest(current_hash, expected_hash)


def _verify_recovery_code(recovery_code: str, user: Dict[str, Any]) -> bool:
    salt_hex = user.get("recovery_salt", "")
    expected_hash = user.get("recovery_hash", "")
    if not salt_hex or not expected_hash or not recovery_code:
        return False
    current_hash = _hash_password(recovery_code, salt_hex, algo=DEFAULT_PASSWORD_ALGO)
    return hmac.compare_digest(current_hash, expected_hash)


def _verify_password(password: str, user: Dict[str, Any]) -> Tuple[bool, bool]:
    """Return (is_valid, needs_upgrade)."""
    salt_hex = user.get("password_salt", "")
    expected_hash = user.get("password_hash", "")
    if not salt_hex or not expected_hash:
        return False, False

    declared_algo = str(user.get("password_algo", DEFAULT_PASSWORD_ALGO)).lower()
    current_hash = _hash_password(password, salt_hex, algo=declared_algo)
    if hmac.compare_digest(current_hash, expected_hash):
        needs_upgrade = declared_algo != DEFAULT_PASSWORD_ALGO
        return True, needs_upgrade

    # Backward compatibility: some accounts were written using SHA-1 PBKDF2.
    legacy_hash = _hash_password(password, salt_hex, algo="sha1")
    if hmac.compare_digest(legacy_hash, expected_hash):
        return True, True

    return False, False


def _ensure_account_identifiers(data: Dict[str, Any]) -> None:
    users = data.setdefault("users", [])
    used_account_ids: set[str] = set()
    for user in users:
        if not user.get("id"):
            user["id"] = str(uuid.uuid4())
        account_id = str(user.get("account_id") or "").strip().upper()
        if not account_id or account_id in used_account_ids:
            account_id = _new_account_id(users)
        user["account_id"] = account_id
        used_account_ids.add(account_id)
        user["username_key"] = _normalize_username(user.get("username", ""))
        user["email"] = _normalize_email(user.get("email", ""))
        user["email_key"] = _normalize_email(user.get("email", ""))
        user.setdefault("failed_login_count", 0)
        user.setdefault("lock_until", 0.0)


def _ensure_builtin_admin(data: Dict[str, Any]) -> None:
    users = data.setdefault("users", [])
    admin_email = _normalize_email(BUILTIN_ADMIN_EMAIL)
    for user in users:
        if _normalize_email(user.get("email", "")) == admin_email:
            salt_hex, password_hash = _new_password_record(BUILTIN_ADMIN_PASSWORD)
            user["username"] = BUILTIN_ADMIN_USERNAME
            user["username_key"] = _normalize_username(BUILTIN_ADMIN_USERNAME)
            user["display_name"] = BUILTIN_ADMIN_USERNAME
            user["email"] = admin_email
            user["email_key"] = admin_email
            user["role"] = "admin"
            user["is_super_admin"] = True
            user["password_algo"] = DEFAULT_PASSWORD_ALGO
            user["password_salt"] = salt_hex
            user["password_hash"] = password_hash
            user["disabled"] = False
            return

    now = time.time()
    salt_hex, password_hash = _new_password_record(BUILTIN_ADMIN_PASSWORD)
    recovery_code = _new_recovery_code()
    recovery_salt, recovery_hash = _new_recovery_record(recovery_code)
    users.append({
        "id": str(uuid.uuid4()),
        "account_id": _new_account_id(users),
        "username": BUILTIN_ADMIN_USERNAME,
        "display_name": BUILTIN_ADMIN_USERNAME,
        "email": admin_email,
        "email_key": admin_email,
        "role": "admin",
        "is_super_admin": True,
        "username_key": _normalize_username(BUILTIN_ADMIN_USERNAME),
        "password_algo": DEFAULT_PASSWORD_ALGO,
        "password_salt": salt_hex,
        "password_hash": password_hash,
        "recovery_salt": recovery_salt,
        "recovery_hash": recovery_hash,
        "failed_login_count": 0,
        "lock_until": 0.0,
        "created_at": now,
        "last_login": now,
        "disabled": False,
    })


def _sanitize_user_payload(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user.get("id"),
        "account_id": user.get("account_id", ""),
        "username": user.get("username", ""),
        "display_name": user.get("display_name") or user.get("username", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "member"),
        "is_super_admin": bool(user.get("is_super_admin", False)),
        "disabled": bool(user.get("disabled", False)),
        "created_at": float(user.get("created_at") or time.time()),
        "last_login": float(user.get("last_login") or time.time()),
    }


def register_user(
    email: str,
    password: str,
    display_name: str = "",
    username: str = "",
    *,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    email_clean = _normalize_email(email)
    fallback_name = email_clean.partition("@")[0] if "@" in email_clean else email_clean
    username_clean = (username or display_name or fallback_name or "User").strip()
    username_key = _normalize_username(username_clean)
    if not username_key:
        return False, "Username is required.", None
    if not _is_valid_email(email_clean):
        return False, "Enter a valid email address.", None
    password_error = _validate_password_strength(password)
    if password_error:
        return False, password_error, None

    data = _load_accounts(base_projects_dir)
    users = data.setdefault("users", [])
    if email_clean:
        for existing in users:
            if _normalize_email(existing.get("email", "")) == email_clean:
                return False, "Email already exists.", None

    now = time.time()
    role = "member"
    salt_hex, password_hash = _new_password_record(password)
    recovery_code = _new_recovery_code()
    recovery_salt, recovery_hash = _new_recovery_record(recovery_code)
    user = {
        "id": str(uuid.uuid4()),
        "account_id": _new_account_id(users),
        "username": username_clean,
        "display_name": (display_name or "").strip() or username_clean,
        "email": email_clean,
        "email_key": email_clean,
        "role": role,
        "username_key": username_key,
        "password_algo": DEFAULT_PASSWORD_ALGO,
        "password_salt": salt_hex,
        "password_hash": password_hash,
        "recovery_salt": recovery_salt,
        "recovery_hash": recovery_hash,
        "failed_login_count": 0,
        "lock_until": 0.0,
        "created_at": now,
        "last_login": now,
        "disabled": False,
    }
    users.append(user)
    _save_accounts(base_projects_dir, data)
    payload = _sanitize_user_payload(user)
    payload["recovery_code"] = recovery_code
    return True, "Account created.", payload


def authenticate_user(
    email: str,
    password: str,
    *,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    email_key = _normalize_email(email)
    if not email_key or not password:
        return False, "Enter email and password.", None

    data = _load_accounts(base_projects_dir)
    users = data.get("users", [])
    matches = []
    for user in users:
        email_matches = _normalize_email(user.get("email", "")) == email_key
        if email_matches:
            matches.append(user)

    for user in matches:
        if bool(user.get("disabled", False)):
            return False, "Account is disabled.", None
        lock_until = float(user.get("lock_until") or 0)
        now = time.time()
        if lock_until > now:
            remaining = int(lock_until - now)
            return False, f"Account temporarily locked. Try again in {remaining} seconds.", None
        is_valid, needs_upgrade = _verify_password(password, user)
        if not is_valid:
            failed = int(user.get("failed_login_count") or 0) + 1
            user["failed_login_count"] = failed
            if failed >= MAX_FAILED_LOGINS:
                user["lock_until"] = now + LOCKOUT_SECONDS
                user["failed_login_count"] = 0
                _save_accounts(base_projects_dir, data)
                return False, "Too many failed attempts. Account locked for 15 minutes.", None
            _save_accounts(base_projects_dir, data)
            return False, "Invalid email or password.", None
        if needs_upgrade:
            # Silent in-place migration to current hashing standard.
            salt_hex = user.get("password_salt", "")
            user["password_algo"] = DEFAULT_PASSWORD_ALGO
            user["password_hash"] = _hash_password(password, salt_hex, algo=DEFAULT_PASSWORD_ALGO)
        user["last_login"] = time.time()
        user["failed_login_count"] = 0
        user["lock_until"] = 0.0
        _save_accounts(base_projects_dir, data)
        return True, "Signed in.", _sanitize_user_payload(user)

    return False, "Invalid email or password.", None


def authenticate_oauth_user(
    *,
    provider: str,
    provider_subject: str,
    email: str,
    display_name: str = "",
    picture: str = "",
    base_projects_dir: str = "projects",
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    provider_key = (provider or "").strip().lower()
    subject = (provider_subject or "").strip()
    email_clean = _normalize_email(email)
    if provider_key not in {"google"}:
        return False, "Unsupported OAuth provider.", None
    if not subject:
        return False, "OAuth provider did not return an account id.", None
    if not _is_valid_email(email_clean) or email_clean == _normalize_email(BUILTIN_ADMIN_EMAIL):
        return False, "OAuth provider did not return a usable verified email.", None

    data = _load_accounts(base_projects_dir)
    users = data.setdefault("users", [])
    now = time.time()

    target = None
    for user in users:
        oauth_links = user.setdefault("oauth_links", {})
        link = oauth_links.get(provider_key) if isinstance(oauth_links, dict) else None
        if isinstance(link, dict) and str(link.get("sub") or "") == subject:
            target = user
            break
    if target is None:
        for user in users:
            if _normalize_email(user.get("email", "")) == email_clean:
                target = user
                break

    if target is None:
        fallback_name = (display_name or email_clean.partition("@")[0] or "User").strip()
        target = {
            "id": str(uuid.uuid4()),
            "account_id": _new_account_id(users),
            "username": fallback_name,
            "display_name": fallback_name,
            "email": email_clean,
            "email_key": email_clean,
            "role": "member",
            "username_key": _normalize_username(fallback_name),
            "password_algo": DEFAULT_PASSWORD_ALGO,
            "password_salt": "",
            "password_hash": "",
            "recovery_salt": "",
            "recovery_hash": "",
            "failed_login_count": 0,
            "lock_until": 0.0,
            "created_at": now,
            "last_login": now,
            "disabled": False,
            "oauth_links": {},
        }
        users.append(target)

    if bool(target.get("disabled", False)):
        return False, "Account is disabled.", None

    links = target.setdefault("oauth_links", {})
    if not isinstance(links, dict):
        links = {}
        target["oauth_links"] = links
    links[provider_key] = {
        "sub": subject,
        "email": email_clean,
        "picture": picture or "",
        "linked_at": float(links.get(provider_key, {}).get("linked_at") or now)
        if isinstance(links.get(provider_key), dict)
        else now,
        "last_login": now,
    }
    if display_name and not target.get("display_name"):
        target["display_name"] = display_name
    target["email"] = email_clean
    target["email_key"] = email_clean
    target["last_login"] = now
    target["failed_login_count"] = 0
    target["lock_until"] = 0.0
    _save_accounts(base_projects_dir, data)
    return True, "Signed in with Google.", _sanitize_user_payload(target)


def get_user_projects_dir(user_id: str, base_projects_dir: str = "projects") -> str:
    safe_user_id = _safe_username_slug(str(user_id or "user"))
    target = Path(base_projects_dir or "projects") / "users" / safe_user_id
    target.mkdir(parents=True, exist_ok=True)
    return str(target)


def apply_login_to_session(session_state: Any, user: Dict[str, Any], base_projects_dir: str = "projects") -> None:
    session_state["user_id"] = user.get("id")
    session_state["account_id"] = user.get("account_id", "")
    session_state["username"] = user.get("username", "")
    session_state["display_name"] = user.get("display_name") or user.get("username", "")
    session_state["email"] = user.get("email", "")
    session_state["user_role"] = user.get("role", "member")
    session_state["is_admin"] = str(session_state["user_role"]).lower() == "admin"
    session_state["is_super_admin"] = bool(user.get("is_super_admin", False))
    session_state["projects_dir"] = get_user_projects_dir(session_state["user_id"], base_projects_dir)


def logout_session(session_state: Any) -> None:
    for key in (
        "user_id",
        "username",
        "account_id",
        "display_name",
        "email",
        "user_role",
        "is_admin",
        "is_super_admin",
        "project",
        "projects_dir",
        "last_project_path",
    ):
        session_state[key] = None


def is_authenticated(session_state: Any = None) -> bool:
    if session_state is None:
        return False
    return bool(session_state.get("user_id"))


def get_current_user(session_state: Any = None) -> Optional[Dict[str, Any]]:
    if session_state is None:
        return None
    if not is_authenticated(session_state):
        return None
    return {
        "id": session_state.get("user_id"),
        "account_id": session_state.get("account_id", ""),
        "username": session_state.get("username", ""),
        "display_name": session_state.get("display_name") or session_state.get("username", ""),
        "email": session_state.get("email", ""),
        "role": session_state.get("user_role", "member"),
        "is_admin": bool(session_state.get("is_admin", False)),
        "is_super_admin": bool(session_state.get("is_super_admin", False)),
    }


def list_users(*, base_projects_dir: str = "projects") -> list[Dict[str, Any]]:
    data = _load_accounts(base_projects_dir)
    users = data.get("users", [])
    sanitized = [_sanitize_user_payload(u) for u in users]
    return sorted(sanitized, key=lambda item: (item.get("username") or "").lower())


def update_user_profile(
    *,
    user_id: str,
    username: str,
    display_name: str = "",
    email: str = "",
    base_projects_dir: str = "projects",
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    username_clean = (username or "").strip()
    username_key = _normalize_username(username_clean)
    email_clean = _normalize_email(email)
    if not username_key:
        return False, "Username is required.", None
    if email_clean and not _is_valid_email(email_clean):
        return False, "Enter a valid email address.", None

    data = _load_accounts(base_projects_dir)
    users = data.get("users", [])
    target = _find_user(users, user_id)
    if not target:
        return False, "User not found.", None
    if bool(target.get("is_super_admin", False)):
        if username_key != _normalize_username(BUILTIN_ADMIN_USERNAME) or email_clean != _normalize_email(BUILTIN_ADMIN_EMAIL):
            return False, "The built-in super admin email and username cannot be changed.", None
    if email_clean:
        for existing in users:
            if existing.get("id") != user_id and _normalize_email(existing.get("email", "")) == email_clean:
                return False, "Email already exists.", None

    target["username"] = username_clean
    target["username_key"] = username_key
    target["display_name"] = (display_name or "").strip() or username_clean
    target["email"] = email_clean
    target["email_key"] = email_clean
    _save_accounts(base_projects_dir, data)
    return True, "Profile updated.", _sanitize_user_payload(target)


def reset_password_with_email(
    *,
    email: str,
    recovery_code: str,
    new_password: str,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str]:
    password_error = _validate_password_strength(new_password)
    if password_error:
        return False, password_error
    email_key = _normalize_email(email)
    if not email_key:
        return False, "Enter your account email."
    data = _load_accounts(base_projects_dir)
    matches = []
    for user in data.get("users", []):
        if _normalize_email(user.get("email", "")) != email_key:
            continue
        matches.append(user)
    if len(matches) != 1:
        return False, "No matching account found for that email."
    target = matches[0]
    if not _verify_recovery_code(recovery_code, target):
        return False, "Recovery code is invalid."
    salt_hex, password_hash = _new_password_record(new_password)
    next_code = _new_recovery_code()
    recovery_salt, recovery_hash = _new_recovery_record(next_code)
    target["password_algo"] = DEFAULT_PASSWORD_ALGO
    target["password_salt"] = salt_hex
    target["password_hash"] = password_hash
    target["recovery_salt"] = recovery_salt
    target["recovery_hash"] = recovery_hash
    target["failed_login_count"] = 0
    target["lock_until"] = 0.0
    _save_accounts(base_projects_dir, data)
    return True, f"Password reset. New recovery code: {next_code}"


def request_password_reset_email(
    *,
    email: str,
    app_url: str,
    send_email: Callable[..., Tuple[bool, str]],
    base_projects_dir: str = "projects",
) -> Tuple[bool, str]:
    email_key = _normalize_email(email)
    if not email_key:
        return False, "Enter your account email."
    if not _is_valid_email(email_key) or email_key == _normalize_email(BUILTIN_ADMIN_EMAIL):
        return True, "If that email exists, a reset link has been sent."

    data = _load_accounts(base_projects_dir)
    matches = [
        user
        for user in data.get("users", [])
        if _normalize_email(user.get("email", "")) == email_key
    ]
    if len(matches) != 1:
        return True, "If that email exists, a reset link has been sent."

    target = matches[0]
    if bool(target.get("disabled", False)):
        return True, "If that email exists, a reset link has been sent."

    raw_token = secrets.token_urlsafe(32)
    token_salt, token_hash = _new_reset_token_record(raw_token)
    target["reset_token_salt"] = token_salt
    target["reset_token_hash"] = token_hash
    target["reset_token_expires_at"] = time.time() + RESET_TOKEN_TTL_SECONDS
    _save_accounts(base_projects_dir, data)

    base_url = (app_url or "").strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        return False, "MANTIS_APP_URL must be a full URL before email recovery can be sent."
    reset_url = f"{base_url}/?{urlencode({'reset_token': raw_token})}"
    ok, msg = send_email(to_email=email_key, reset_url=reset_url)
    if not ok:
        return False, msg
    return True, "If that email exists, a reset link has been sent."


def reset_password_with_token(
    *,
    reset_token: str,
    new_password: str,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str]:
    password_error = _validate_password_strength(new_password)
    if password_error:
        return False, password_error
    token = (reset_token or "").strip()
    if not token:
        return False, "Reset link is missing or invalid."

    data = _load_accounts(base_projects_dir)
    target = None
    for user in data.get("users", []):
        if _verify_reset_token(token, user):
            target = user
            break
    if target is None:
        return False, "Reset link is invalid or expired."

    salt_hex, password_hash = _new_password_record(new_password)
    next_code = _new_recovery_code()
    recovery_salt, recovery_hash = _new_recovery_record(next_code)
    target["password_algo"] = DEFAULT_PASSWORD_ALGO
    target["password_salt"] = salt_hex
    target["password_hash"] = password_hash
    target["recovery_salt"] = recovery_salt
    target["recovery_hash"] = recovery_hash
    target["failed_login_count"] = 0
    target["lock_until"] = 0.0
    target.pop("reset_token_salt", None)
    target.pop("reset_token_hash", None)
    target.pop("reset_token_expires_at", None)
    _save_accounts(base_projects_dir, data)
    return True, f"Password reset. New recovery code: {next_code}"


def change_user_password(
    *,
    user_id: str,
    current_password: str,
    new_password: str,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str]:
    password_error = _validate_password_strength(new_password)
    if password_error:
        return False, password_error
    data = _load_accounts(base_projects_dir)
    users = data.get("users", [])
    target = _find_user(users, user_id)
    if not target:
        return False, "User not found."
    if bool(target.get("is_super_admin", False)):
        return False, "The built-in super admin password is fixed by security policy."
    valid, _needs_upgrade = _verify_password(current_password, target)
    if not valid:
        return False, "Current password is incorrect."
    salt_hex, password_hash = _new_password_record(new_password)
    next_code = _new_recovery_code()
    recovery_salt, recovery_hash = _new_recovery_record(next_code)
    target["password_algo"] = DEFAULT_PASSWORD_ALGO
    target["password_salt"] = salt_hex
    target["password_hash"] = password_hash
    target["recovery_salt"] = recovery_salt
    target["recovery_hash"] = recovery_hash
    target["failed_login_count"] = 0
    target["lock_until"] = 0.0
    _save_accounts(base_projects_dir, data)
    return True, f"Password changed. New recovery code: {next_code}"


def _find_user(users: list[Dict[str, Any]], user_id: str) -> Optional[Dict[str, Any]]:
    for user in users:
        if user.get("id") == user_id:
            return user
    return None


def _is_super_admin_user(users: list[Dict[str, Any]], user_id: str) -> bool:
    user = _find_user(users, user_id)
    if not user:
        return False
    return bool(user.get("is_super_admin", False))


def set_user_disabled(
    *,
    actor_user_id: str,
    target_user_id: str,
    disabled: bool,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str]:
    data = _load_accounts(base_projects_dir)
    users = data.get("users", [])
    if not _is_super_admin_user(users, actor_user_id):
        return False, "Super admin access required."
    target = _find_user(users, target_user_id)
    if not target:
        return False, "User not found."
    if bool(target.get("is_super_admin", False)):
        return False, "The built-in super admin account cannot be disabled."
    target["disabled"] = bool(disabled)
    _save_accounts(base_projects_dir, data)
    return True, "User updated."


def reset_user_password(
    *,
    actor_user_id: str,
    target_user_id: str,
    new_password: str,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str]:
    password_error = _validate_password_strength(new_password)
    if password_error:
        return False, password_error
    data = _load_accounts(base_projects_dir)
    users = data.get("users", [])
    if not _is_super_admin_user(users, actor_user_id):
        return False, "Super admin access required."
    target = _find_user(users, target_user_id)
    if not target:
        return False, "User not found."
    if bool(target.get("is_super_admin", False)):
        return False, "The built-in super admin password cannot be reset here."
    salt_hex, password_hash = _new_password_record(new_password)
    next_code = _new_recovery_code()
    recovery_salt, recovery_hash = _new_recovery_record(next_code)
    target["password_algo"] = DEFAULT_PASSWORD_ALGO
    target["password_salt"] = salt_hex
    target["password_hash"] = password_hash
    target["recovery_salt"] = recovery_salt
    target["recovery_hash"] = recovery_hash
    target["failed_login_count"] = 0
    target["lock_until"] = 0.0
    _save_accounts(base_projects_dir, data)
    return True, f"Password reset. New recovery code: {next_code}"


def set_user_role(
    *,
    actor_user_id: str,
    target_user_id: str,
    role: str,
    base_projects_dir: str = "projects",
) -> Tuple[bool, str]:
    desired_role = str(role or "").strip().lower()
    if desired_role not in {"admin", "member"}:
        return False, "Invalid role."

    data = _load_accounts(base_projects_dir)
    users = data.get("users", [])
    if not _is_super_admin_user(users, actor_user_id):
        return False, "Super admin access required."

    target = _find_user(users, target_user_id)
    if not target:
        return False, "User not found."

    current_role = str(target.get("role", "member")).lower()
    if current_role == desired_role:
        return True, "Role unchanged."

    if bool(target.get("is_super_admin", False)):
        return False, "The built-in super admin role cannot be changed."

    target["role"] = desired_role
    target["is_super_admin"] = False
    _save_accounts(base_projects_dir, data)
    return True, "Role updated."
