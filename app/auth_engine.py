"""
CareerCompass AI - Auth Engine (Sprint 4.1)
Supabase Auth via REST using SUPABASE_PUBLISHABLE_KEY.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import streamlit as st
except Exception:
    st = None

DEFAULT_REDIRECT_URL = "https://careercompass-intelligence.streamlit.app"


class AuthConfigurationError(RuntimeError):
    pass


class AuthRequestError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


@dataclass(slots=True)
class AuthUser:
    id: str
    email: str | None
    email_confirmed_at: str | None
    user_metadata: dict[str, Any]
    raw: dict[str, Any]


@dataclass(slots=True)
class AuthSession:
    access_token: str
    refresh_token: str
    expires_in: int | None
    expires_at: int | None
    token_type: str | None
    user: AuthUser
    raw: dict[str, Any]


@dataclass(slots=True)
class SignupResult:
    user: AuthUser | None
    session: AuthSession | None
    confirmation_required: bool
    message: str


def _read_setting(name: str) -> str | None:
    if st is not None:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass
    value = os.getenv(name)
    return value.strip() if value else None


def get_auth_config() -> tuple[str, str]:
    url = _read_setting("SUPABASE_URL")
    key = _read_setting("SUPABASE_PUBLISHABLE_KEY")
    missing = [n for n, v in (("SUPABASE_URL", url), ("SUPABASE_PUBLISHABLE_KEY", key)) if not v]
    if missing:
        raise AuthConfigurationError("Configuração Supabase Auth ausente: " + ", ".join(missing))
    return url.rstrip("/"), key


def _request(
    path: str,
    *,
    method: str = "POST",
    params: dict[str, Any] | None = None,
    body: Any = None,
    access_token: str | None = None,
) -> Any:
    base_url, key = get_auth_config()
    endpoint = f"{base_url}/auth/v1/{path.lstrip('/')}"
    if params:
        endpoint += "?" + urlencode({k: v for k, v in params.items() if v is not None})

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {access_token or key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = Request(endpoint, data=data, method=method, headers=headers)

    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"message": raw}
        message = (
            payload.get("msg")
            or payload.get("message")
            or payload.get("error_description")
            or payload.get("error")
            or f"Supabase Auth HTTP {exc.code}"
        ) if isinstance(payload, dict) else str(payload)
        raise AuthRequestError(message, exc.code, payload) from exc
    except URLError as exc:
        raise AuthRequestError(f"Falha de rede ao acessar Supabase Auth: {exc.reason}") from exc


def _user(payload: Any) -> AuthUser | None:
    if not isinstance(payload, dict) or not payload.get("id"):
        return None
    metadata = payload.get("user_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    return AuthUser(
        id=str(payload["id"]),
        email=payload.get("email"),
        email_confirmed_at=payload.get("email_confirmed_at") or payload.get("confirmed_at"),
        user_metadata=metadata,
        raw=payload,
    )


def _session(payload: Any) -> AuthSession | None:
    if not isinstance(payload, dict):
        return None
    if not payload.get("access_token") or not payload.get("refresh_token"):
        return None
    user = _user(payload.get("user"))
    if user is None:
        return None
    return AuthSession(
        access_token=str(payload["access_token"]),
        refresh_token=str(payload["refresh_token"]),
        expires_in=payload.get("expires_in"),
        expires_at=payload.get("expires_at"),
        token_type=payload.get("token_type"),
        user=user,
        raw=payload,
    )


def sign_up(
    email: str,
    password: str,
    *,
    full_name: str | None = None,
    redirect_to: str | None = None,
) -> SignupResult:
    email = email.strip().lower()
    if not email:
        raise ValueError("Informe um e-mail válido.")
    if len(password) < 6:
        raise ValueError("A senha deve ter pelo menos 6 caracteres.")

    payload = _request(
        "signup",
        params={"redirect_to": redirect_to or DEFAULT_REDIRECT_URL},
        body={
            "email": email,
            "password": password,
            "data": {"full_name": full_name.strip()} if full_name and full_name.strip() else {},
        },
    )
    user = _user(payload.get("user") if isinstance(payload, dict) else None)
    session = _session(payload)
    confirmation_required = session is None and user is not None and not user.email_confirmed_at
    message = (
        "Cadastro realizado. Confirme seu e-mail antes de entrar."
        if confirmation_required else
        "Cadastro realizado com sucesso."
    )
    return SignupResult(user, session, confirmation_required, message)


def sign_in_with_password(email: str, password: str) -> AuthSession:
    email = email.strip().lower()
    if not email or not password:
        raise ValueError("Informe e-mail e senha.")
    payload = _request(
        "token",
        params={"grant_type": "password"},
        body={"email": email, "password": password},
    )
    session = _session(payload)
    if session is None:
        raise AuthRequestError("Supabase não retornou uma sessão válida.")
    return session


def get_user(access_token: str) -> AuthUser:
    payload = _request("user", method="GET", access_token=access_token)
    user = _user(payload)
    if user is None:
        raise AuthRequestError("Usuário autenticado inválido.")
    return user


def refresh_session(refresh_token: str) -> AuthSession:
    payload = _request(
        "token",
        params={"grant_type": "refresh_token"},
        body={"refresh_token": refresh_token},
    )
    session = _session(payload)
    if session is None:
        raise AuthRequestError("Sessão renovada inválida.")
    return session


def send_password_recovery(email: str, *, redirect_to: str | None = None) -> None:
    email = email.strip().lower()
    if not email:
        raise ValueError("Informe um e-mail válido.")
    _request(
        "recover",
        params={"redirect_to": redirect_to or DEFAULT_REDIRECT_URL},
        body={"email": email},
    )


def sign_out(access_token: str) -> None:
    if not access_token:
        return
    try:
        _request("logout", access_token=access_token, body={})
    except AuthRequestError as exc:
        if exc.status not in {401, 403}:
            raise


def auth_health_check() -> dict[str, Any]:
    try:
        url, key = get_auth_config()
        return {
            "status": "ok",
            "provider": "supabase-auth",
            "url_configured": bool(url),
            "publishable_key_configured": bool(key),
        }
    except Exception as exc:
        return {"status": "error", "provider": "supabase-auth", "error": str(exc)}
