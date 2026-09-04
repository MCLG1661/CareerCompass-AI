"""
CareerCompass AI
Supabase Database Engine — Sprint 3

Cloud persistence adapter for PostgreSQL/Supabase.

Design goals:
- preserve the public API used by persistence_service.py;
- keep the current SQLite database_engine.py untouched as a local fallback;
- use Supabase PostgREST with server-side SUPABASE_SECRET_KEY;
- never log or expose secrets;
- preserve CareerCompass legacy field names at the adapter boundary;
- support a temporary single-user bootstrap until Supabase Auth is integrated.

IMPORTANT:
This module expects the Supabase schema created for Sprint 3 and server-side
privileges granted to service_role. It must only be used on a trusted server
environment such as Streamlit Cloud Secrets.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import streamlit as st
except Exception:  # pragma: no cover - optional outside Streamlit runtime
    st = None


SCHEMA_VERSION = "3.0-supabase"
DEFAULT_USER_NAME = "CareerCompass User"


# ============================================================
# CONFIGURATION
# ============================================================


class SupabaseConfigurationError(RuntimeError):
    """Raised when required Supabase configuration is unavailable."""


class SupabaseRequestError(RuntimeError):
    """Raised when Supabase/PostgREST returns an unexpected response."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


def _read_secret(name: str) -> str | None:
    """
    Read Streamlit Secrets first and environment variables second.
    Secret values are never printed.
    """

    if st is not None:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass

    value = os.getenv(name)
    return value.strip() if value else None


def get_supabase_config() -> tuple[str, str]:
    url = _read_secret("SUPABASE_URL")
    secret_key = _read_secret("SUPABASE_SECRET_KEY")

    missing = [
        name
        for name, value in (
            ("SUPABASE_URL", url),
            ("SUPABASE_SECRET_KEY", secret_key),
        )
        if not value
    ]

    if missing:
        raise SupabaseConfigurationError(
            "Configuração Supabase ausente: "
            + ", ".join(missing)
        )

    return url.rstrip("/"), secret_key


# ============================================================
# GENERIC HELPERS
# ============================================================


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_id(prefix: str | None = None) -> str:
    """
    Supabase schema uses UUID columns. Prefix is accepted for API compatibility
    but intentionally ignored.
    """

    return str(uuid.uuid4())


def serialize_json(value: Any) -> Any:
    """
    Convert dataclasses and arbitrary objects into JSON-compatible Python data.
    PostgREST will serialize the returned object.
    """

    if value is None:
        return {}

    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)

    if isinstance(value, (dict, list, str, int, float, bool)):
        return value

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()

    if hasattr(value, "__dict__"):
        return {
            key: serialize_json(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }

    return str(value)


def deserialize_json(value: Any) -> Any:
    if value is None:
        return {}

    if isinstance(value, (dict, list)):
        return value

    if not isinstance(value, str):
        return value

    text = value.strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return value


def _api_url(
    table: str,
    params: dict[str, Any] | None = None,
) -> str:
    base_url, _ = get_supabase_config()
    endpoint = f"{base_url}/rest/v1/{table}"

    if params:
        query = urlencode(
            {
                key: value
                for key, value in params.items()
                if value is not None
            },
            doseq=True,
        )
        if query:
            endpoint = f"{endpoint}?{query}"

    return endpoint


def _request(
    table: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    body: Any = None,
    return_representation: bool = True,
) -> Any:
    _, secret_key = get_supabase_config()

    headers = {
        "apikey": secret_key,
        "Authorization": f"Bearer {secret_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if method in {"POST", "PATCH"}:
        headers["Prefer"] = (
            "return=representation"
            if return_representation
            else "return=minimal"
        )

    data = None
    if body is not None:
        data = json.dumps(
            serialize_json(body),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")

    request = Request(
        _api_url(table, params),
        data=data,
        method=method,
        headers=headers,
    )

    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            if not raw:
                return []
            return json.loads(raw)

    except HTTPError as exc:
        raw = exc.read().decode(
            "utf-8",
            errors="replace",
        )
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"message": raw}

        message = (
            payload.get("message")
            if isinstance(payload, dict)
            else str(payload)
        ) or f"Supabase HTTP {exc.code}"

        raise SupabaseRequestError(
            message,
            status=exc.code,
            payload=payload,
        ) from exc

    except URLError as exc:
        raise SupabaseRequestError(
            f"Falha de rede ao acessar Supabase: {exc.reason}"
        ) from exc


def _first(rows: Any) -> dict[str, Any] | None:
    if isinstance(rows, list) and rows:
        row = rows[0]
        return row if isinstance(row, dict) else None
    return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "true",
            "yes",
            "sim",
        }
    return False


def _normalize_score(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return round(float(value), 2)

    if isinstance(value, str):
        cleaned = (
            value.replace("%", "")
            .replace(",", ".")
            .strip()
        )
        try:
            return round(float(cleaned), 2)
        except ValueError:
            return None

    return None


def _extract_text(
    report: Any,
    candidate_keys: tuple[str, ...],
) -> str | None:
    if report is None:
        return None

    for key in candidate_keys:
        if isinstance(report, dict):
            value = report.get(key)
        else:
            value = getattr(report, key, None)

        if value is not None:
            text = str(value).strip()
            if text:
                return text

    return None


# ============================================================
# HEALTH / INITIALIZATION
# ============================================================


def initialize_database() -> None:
    """
    Schema creation is managed in Supabase SQL Editor/migrations.
    Initialization only verifies connectivity and required tables.
    """

    health = database_health_check()
    if health["status"] != "ok":
        raise SupabaseRequestError(
            health.get(
                "error",
                "Supabase database is not healthy.",
            )
        )


def database_health_check() -> dict[str, Any]:
    required_tables = (
        "users",
        "career_profiles",
        "opportunities",
        "analyses",
        "applications",
        "career_events",
        "system_metadata",
    )

    try:
        for table in required_tables:
            _request(
                table,
                params={
                    "select": "id",
                    "limit": 1,
                },
            )

        return {
            "status": "ok",
            "backend": "supabase",
            "schema_version": SCHEMA_VERSION,
            "tables": list(required_tables),
        }

    except Exception as exc:
        return {
            "status": "error",
            "backend": "supabase",
            "schema_version": SCHEMA_VERSION,
            "error": str(exc),
        }


# ============================================================
# USERS
# ============================================================


def create_user(
    name: str | None = None,
    email: str | None = None,
    auth_user_id: str | None = None,
) -> str:
    payload = {
        "name": name or DEFAULT_USER_NAME,
        "email": email,
        "auth_user_id": auth_user_id,
    }

    rows = _request(
        "users",
        method="POST",
        body=payload,
    )

    row = _first(rows)
    if not row:
        raise SupabaseRequestError(
            "Supabase não retornou o usuário criado."
        )

    return str(row["id"])


def get_user(
    user_id: str,
) -> dict[str, Any] | None:
    rows = _request(
        "users",
        params={
            "select": "*",
            "id": f"eq.{user_id}",
            "limit": 1,
        },
    )
    return _first(rows)


def get_user_by_auth_id(
    auth_user_id: str,
) -> dict[str, Any] | None:
    rows = _request(
        "users",
        params={
            "select": "*",
            "auth_user_id": f"eq.{auth_user_id}",
            "limit": 1,
        },
    )
    return _first(rows)


def get_or_create_default_user(
    name: str | None = None,
    email: str | None = None,
) -> str:
    """
    Transitional single-user bootstrap.

    Sprint 3 Auth integration will replace this with auth.uid()-based identity.
    Until then, reuse a matching email/name instead of creating a new user at
    every Streamlit restart.
    """

    if email:
        rows = _request(
            "users",
            params={
                "select": "*",
                "email": f"eq.{email}",
                "limit": 1,
            },
        )
        existing = _first(rows)
        if existing:
            return str(existing["id"])

    clean_name = (
        name.strip()
        if name and name.strip()
        else DEFAULT_USER_NAME
    )

    rows = _request(
        "users",
        params={
            "select": "*",
            "name": f"eq.{clean_name}",
            "order": "created_at.asc",
            "limit": 1,
        },
    )

    existing = _first(rows)
    if existing:
        return str(existing["id"])

    return create_user(
        name=clean_name,
        email=email,
    )


# ============================================================
# METADATA
# ============================================================


def set_metadata(
    key: str,
    value: Any,
    user_id: str | None = None,
) -> None:
    rows = _request(
        "system_metadata",
        params={
            "select": "*",
            "metadata_key": f"eq.{key}",
            "user_id": (
                f"eq.{user_id}"
                if user_id
                else "is.null"
            ),
            "limit": 1,
        },
    )

    existing = _first(rows)
    payload = {
        "metadata_key": key,
        "metadata_value": serialize_json(value),
        "updated_at": utc_now(),
    }

    if user_id:
        payload["user_id"] = user_id

    if existing:
        _request(
            "system_metadata",
            method="PATCH",
            params={
                "id": f"eq.{existing['id']}",
            },
            body=payload,
        )
    else:
        _request(
            "system_metadata",
            method="POST",
            body=payload,
        )


def get_metadata(
    key: str,
    user_id: str | None = None,
) -> Any:
    rows = _request(
        "system_metadata",
        params={
            "select": "*",
            "metadata_key": f"eq.{key}",
            "user_id": (
                f"eq.{user_id}"
                if user_id
                else "is.null"
            ),
            "order": "updated_at.desc",
            "limit": 1,
        },
    )

    row = _first(rows)
    if not row:
        return None

    return deserialize_json(
        row.get("metadata_value")
    )


# ============================================================
# CAREER PROFILES / CV REPOSITORY
# ============================================================


def _legacy_profile(
    row: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not row:
        return None

    result = dict(row)
    profile_data = deserialize_json(
        result.get("profile_data")
    )

    if not isinstance(profile_data, dict):
        profile_data = {}

    result["raw_profile_text"] = (
        profile_data.get("raw_profile_text")
        or ""
    )
    result["structured_profile"] = (
        profile_data.get("structured_profile")
        or {}
    )

    # Preserve legacy integer-ish behavior where UI may inspect truthiness.
    result["is_active"] = _to_bool(
        result.get("is_active")
    )
    result["is_archived"] = _to_bool(
        result.get("is_archived")
    )

    return result


def save_career_profile(
    user_id: str,
    raw_profile_text: str,
    structured_profile: Any,
    profile_name: str = "Perfil principal",
    source_name: str | None = None,
    content_hash: str | None = None,
    profile_type: str = "resume",
) -> str:
    timestamp = utc_now()

    existing = None
    if content_hash:
        rows = _request(
            "career_profiles",
            params={
                "select": "*",
                "user_id": f"eq.{user_id}",
                "content_hash": f"eq.{content_hash}",
                "is_archived": "eq.false",
                "order": "updated_at.desc",
                "limit": 1,
            },
        )
        existing = _first(rows)

    _request(
        "career_profiles",
        method="PATCH",
        params={
            "user_id": f"eq.{user_id}",
            "is_active": "eq.true",
        },
        body={
            "is_active": False,
            "updated_at": timestamp,
        },
    )

    profile_data = {
        "raw_profile_text": raw_profile_text,
        "structured_profile": serialize_json(
            structured_profile
        ),
    }

    payload = {
        "user_id": user_id,
        "profile_name": profile_name,
        "profile_data": profile_data,
        "source_name": source_name,
        "content_hash": content_hash,
        "profile_type": profile_type,
        "is_active": True,
        "is_archived": False,
        "last_used_at": timestamp,
        "updated_at": timestamp,
    }

    if existing:
        profile_id = str(existing["id"])
        rows = _request(
            "career_profiles",
            method="PATCH",
            params={
                "id": f"eq.{profile_id}",
                "user_id": f"eq.{user_id}",
            },
            body=payload,
        )
        if not _first(rows):
            raise SupabaseRequestError(
                "Falha ao reativar perfil existente."
            )
        event_type = "profile_reactivated"
    else:
        rows = _request(
            "career_profiles",
            method="POST",
            body=payload,
        )
        row = _first(rows)
        if not row:
            raise SupabaseRequestError(
                "Falha ao criar perfil."
            )
        profile_id = str(row["id"])
        event_type = "profile_created"

    log_event(
        user_id=user_id,
        event_type=event_type,
        entity_type="career_profile",
        entity_id=profile_id,
        event_data={
            "profile_name": profile_name,
            "source_name": source_name,
            "profile_type": profile_type,
        },
    )

    return profile_id


def get_career_profile(
    profile_id: str,
) -> dict[str, Any] | None:
    rows = _request(
        "career_profiles",
        params={
            "select": "*",
            "id": f"eq.{profile_id}",
            "limit": 1,
        },
    )
    return _legacy_profile(
        _first(rows)
    )


def get_active_profile(
    user_id: str,
) -> dict[str, Any] | None:
    rows = _request(
        "career_profiles",
        params={
            "select": "*",
            "user_id": f"eq.{user_id}",
            "is_active": "eq.true",
            "is_archived": "eq.false",
            "order": "last_used_at.desc.nullslast,updated_at.desc",
            "limit": 1,
        },
    )
    return _legacy_profile(
        _first(rows)
    )


def list_career_profiles(
    user_id: str,
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "select": "*",
        "user_id": f"eq.{user_id}",
        "order": (
            "is_active.desc,"
            "last_used_at.desc.nullslast,"
            "updated_at.desc,"
            "created_at.desc"
        ),
    }

    if not include_archived:
        params["is_archived"] = "eq.false"

    rows = _request(
        "career_profiles",
        params=params,
    )

    result = []
    for row in rows or []:
        normalized = _legacy_profile(row)
        if normalized:
            result.append(normalized)

    return result


def activate_career_profile(
    user_id: str,
    profile_id: str,
) -> None:
    profile = get_career_profile(
        profile_id
    )

    if (
        not profile
        or str(profile.get("user_id")) != str(user_id)
        or profile.get("is_archived")
    ):
        raise ValueError(
            f"Perfil não encontrado: {profile_id}"
        )

    timestamp = utc_now()

    _request(
        "career_profiles",
        method="PATCH",
        params={
            "user_id": f"eq.{user_id}",
            "is_active": "eq.true",
        },
        body={
            "is_active": False,
            "updated_at": timestamp,
        },
    )

    rows = _request(
        "career_profiles",
        method="PATCH",
        params={
            "id": f"eq.{profile_id}",
            "user_id": f"eq.{user_id}",
        },
        body={
            "is_active": True,
            "last_used_at": timestamp,
            "updated_at": timestamp,
        },
    )

    if not _first(rows):
        raise ValueError(
            f"Perfil não encontrado: {profile_id}"
        )

    log_event(
        user_id=user_id,
        event_type="profile_activated",
        entity_type="career_profile",
        entity_id=profile_id,
    )


def rename_career_profile(
    user_id: str,
    profile_id: str,
    profile_name: str,
) -> None:
    clean_name = profile_name.strip()

    if not clean_name:
        raise ValueError(
            "O nome do perfil não pode ficar vazio."
        )

    rows = _request(
        "career_profiles",
        method="PATCH",
        params={
            "id": f"eq.{profile_id}",
            "user_id": f"eq.{user_id}",
            "is_archived": "eq.false",
        },
        body={
            "profile_name": clean_name,
            "updated_at": utc_now(),
        },
    )

    if not _first(rows):
        raise ValueError(
            f"Perfil não encontrado: {profile_id}"
        )

    log_event(
        user_id=user_id,
        event_type="profile_renamed",
        entity_type="career_profile",
        entity_id=profile_id,
        event_data={
            "profile_name": clean_name,
        },
    )


# ============================================================
# OPPORTUNITIES
# ============================================================


def _legacy_opportunity(
    row: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not row:
        return None

    result = dict(row)

    # Current persistence_service/main.py expect job_description.
    result["job_description"] = (
        result.get("description")
        or ""
    )

    return result


def save_opportunity(
    user_id: str,
    job_title: str,
    job_description: str,
    company: str | None = None,
    source: str | None = None,
    source_url: str | None = None,
) -> str:
    payload = {
        "user_id": user_id,
        "job_title": job_title,
        "company": company,
        "description": job_description,
        "source": source,
        "source_url": source_url,
        "status": "analyzed",
        "opportunity_data": {},
        "updated_at": utc_now(),
    }

    rows = _request(
        "opportunities",
        method="POST",
        body=payload,
    )

    row = _first(rows)
    if not row:
        raise SupabaseRequestError(
            "Falha ao criar oportunidade."
        )

    opportunity_id = str(row["id"])

    log_event(
        user_id=user_id,
        event_type="opportunity_created",
        entity_type="opportunity",
        entity_id=opportunity_id,
        event_data={
            "job_title": job_title,
            "company": company,
        },
    )

    return opportunity_id


def get_opportunity(
    opportunity_id: str,
) -> dict[str, Any] | None:
    rows = _request(
        "opportunities",
        params={
            "select": "*",
            "id": f"eq.{opportunity_id}",
            "limit": 1,
        },
    )
    return _legacy_opportunity(
        _first(rows)
    )


def list_opportunities(
    user_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = _request(
        "opportunities",
        params={
            "select": "*",
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
            "limit": limit,
        },
    )

    return [
        normalized
        for row in (rows or [])
        if (
            normalized := _legacy_opportunity(
                row
            )
        )
    ]


# ============================================================
# ANALYSES
# ============================================================


def _legacy_analysis(
    row: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not row:
        return None

    result = dict(row)

    result["career_fit_report"] = deserialize_json(
        result.get("curator_report")
    )
    result["ats_report"] = deserialize_json(
        result.get("ats_report")
    )
    result["tailoring_report"] = deserialize_json(
        result.get("tailoring_report")
    )

    decision_data = deserialize_json(
        result.get("decision_report")
    )
    if not isinstance(decision_data, dict):
        decision_data = {}

    result["recommendation_report"] = (
        decision_data.get(
            "recommendation_report",
            {},
        )
    )
    result["classification"] = (
        decision_data.get("classification")
    )
    result["recommendation"] = (
        decision_data.get("recommendation")
    )

    return result


def save_analysis(
    user_id: str,
    profile_id: str,
    opportunity_id: str,
    career_fit_score: float | None = None,
    ats_score: float | None = None,
    tailoring_score: float | None = None,
    classification: str | None = None,
    recommendation: str | None = None,
    career_fit_report: Any = None,
    ats_report: Any = None,
    recommendation_report: Any = None,
    tailoring_report: Any = None,
) -> str:
    decision_payload = {
        "classification": classification,
        "recommendation": recommendation,
        "recommendation_report": serialize_json(
            recommendation_report
        ),
    }

    payload = {
        "user_id": user_id,
        "profile_id": profile_id,
        "opportunity_id": opportunity_id,
        "career_fit_score": _normalize_score(
            career_fit_score
        ),
        "ats_score": _normalize_score(
            ats_score
        ),
        "tailoring_score": _normalize_score(
            tailoring_score
        ),
        "decision_score": None,
        "curator_report": serialize_json(
            career_fit_report
        ),
        "ats_report": serialize_json(
            ats_report
        ),
        "tailoring_report": serialize_json(
            tailoring_report
        ),
        "opportunity_report": {},
        "decision_report": decision_payload,
    }

    rows = _request(
        "analyses",
        method="POST",
        body=payload,
    )

    row = _first(rows)
    if not row:
        raise SupabaseRequestError(
            "Falha ao persistir análise."
        )

    analysis_id = str(row["id"])

    log_event(
        user_id=user_id,
        event_type="career_analysis_completed",
        entity_type="analysis",
        entity_id=analysis_id,
        event_data={
            "opportunity_id": opportunity_id,
            "career_fit_score": career_fit_score,
            "ats_score": ats_score,
            "tailoring_score": tailoring_score,
        },
    )

    return analysis_id


def get_analysis(
    analysis_id: str,
) -> dict[str, Any] | None:
    rows = _request(
        "analyses",
        params={
            "select": "*",
            "id": f"eq.{analysis_id}",
            "limit": 1,
        },
    )
    return _legacy_analysis(
        _first(rows)
    )


def _attach_opportunity_fields(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    opportunity_ids = {
        str(row.get("opportunity_id"))
        for row in rows
        if row.get("opportunity_id")
    }

    opportunity_map: dict[str, dict[str, Any]] = {}

    for opportunity_id in opportunity_ids:
        opportunity = get_opportunity(
            opportunity_id
        )
        if opportunity:
            opportunity_map[
                opportunity_id
            ] = opportunity

    result = []
    for row in rows:
        item = dict(row)
        opportunity = opportunity_map.get(
            str(item.get("opportunity_id")),
            {},
        )
        item["job_title"] = (
            opportunity.get("job_title")
        )
        item["company"] = (
            opportunity.get("company")
        )
        result.append(item)

    return result


def list_analyses(
    user_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = _request(
        "analyses",
        params={
            "select": "*",
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
            "limit": limit,
        },
    )

    normalized = [
        item
        for row in (rows or [])
        if (
            item := _legacy_analysis(
                row
            )
        )
    ]

    return _attach_opportunity_fields(
        normalized
    )


# ============================================================
# APPLICATIONS
# ============================================================


VALID_APPLICATION_STATUSES = {
    "planned",
    "applied",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
}


def create_application(
    user_id: str,
    opportunity_id: str,
    analysis_id: str | None = None,
    status: str = "planned",
    notes: str | None = None,
) -> str:
    normalized_status = status.strip().lower()

    if normalized_status not in VALID_APPLICATION_STATUSES:
        raise ValueError(
            f"Status inválido: {status}"
        )

    timestamp = utc_now()

    payload = {
        "user_id": user_id,
        "opportunity_id": opportunity_id,
        "analysis_id": analysis_id,
        "status": normalized_status,
        "applied_at": (
            timestamp
            if normalized_status == "applied"
            else None
        ),
        "interview_at": (
            timestamp
            if normalized_status == "interview"
            else None
        ),
        "notes": notes,
        "updated_at": timestamp,
    }

    rows = _request(
        "applications",
        method="POST",
        body=payload,
    )

    row = _first(rows)
    if not row:
        raise SupabaseRequestError(
            "Falha ao criar candidatura."
        )

    application_id = str(row["id"])

    log_event(
        user_id=user_id,
        event_type="application_created",
        entity_type="application",
        entity_id=application_id,
        event_data={
            "opportunity_id": opportunity_id,
            "status": normalized_status,
        },
    )

    return application_id


def update_application_status(
    application_id: str,
    status: str,
    outcome: str | None = None,
    notes: str | None = None,
) -> None:
    normalized_status = status.strip().lower()

    if normalized_status not in VALID_APPLICATION_STATUSES:
        raise ValueError(
            f"Status inválido: {status}"
        )

    rows = _request(
        "applications",
        params={
            "select": "*",
            "id": f"eq.{application_id}",
            "limit": 1,
        },
    )

    existing = _first(rows)
    if not existing:
        raise ValueError(
            f"Candidatura não encontrada: {application_id}"
        )

    timestamp = utc_now()

    payload: dict[str, Any] = {
        "status": normalized_status,
        "updated_at": timestamp,
    }

    if outcome is not None:
        payload["outcome"] = outcome

    if notes is not None:
        payload["notes"] = notes

    if (
        normalized_status == "applied"
        and not existing.get("applied_at")
    ):
        payload["applied_at"] = timestamp

    if (
        normalized_status == "interview"
        and not existing.get("interview_at")
    ):
        payload["interview_at"] = timestamp

    updated = _request(
        "applications",
        method="PATCH",
        params={
            "id": f"eq.{application_id}",
        },
        body=payload,
    )

    if not _first(updated):
        raise ValueError(
            f"Candidatura não encontrada: {application_id}"
        )

    log_event(
        user_id=str(existing["user_id"]),
        event_type="application_status_changed",
        entity_type="application",
        entity_id=application_id,
        event_data={
            "status": normalized_status,
            "outcome": outcome,
        },
    )


def list_applications(
    user_id: str,
) -> list[dict[str, Any]]:
    rows = _request(
        "applications",
        params={
            "select": "*",
            "user_id": f"eq.{user_id}",
            "order": "updated_at.desc",
        },
    )

    return _attach_opportunity_fields(
        list(rows or [])
    )


# ============================================================
# CAREER EVENTS
# ============================================================


def log_event(
    user_id: str,
    event_type: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    event_data: Any = None,
) -> str:
    payload_data = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "data": serialize_json(
            event_data
        ),
    }

    rows = _request(
        "career_events",
        method="POST",
        body={
            "user_id": user_id,
            "event_type": event_type,
            "event_data": payload_data,
        },
    )

    row = _first(rows)
    if not row:
        raise SupabaseRequestError(
            "Falha ao registrar evento."
        )

    return str(row["id"])


def list_events(
    user_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    rows = _request(
        "career_events",
        params={
            "select": "*",
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
            "limit": limit,
        },
    )

    result = []
    for row in rows or []:
        item = dict(row)
        stored = deserialize_json(
            item.get("event_data")
        )

        if not isinstance(stored, dict):
            stored = {}

        item["entity_type"] = (
            stored.get("entity_type")
        )
        item["entity_id"] = (
            stored.get("entity_id")
        )
        item["event_data"] = (
            stored.get("data")
            or {}
        )

        result.append(item)

    return result


# ============================================================
# CAREER METRICS
# ============================================================


def _average(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        2,
    )


def get_career_metrics(
    user_id: str,
) -> dict[str, Any]:
    analyses = list_analyses(
        user_id,
        limit=1000,
    )
    applications = list_applications(
        user_id
    )

    fit_values = [
        value
        for item in analyses
        if (
            value := _normalize_score(
                item.get("career_fit_score")
            )
        ) is not None
    ]

    ats_values = [
        value
        for item in analyses
        if (
            value := _normalize_score(
                item.get("ats_score")
            )
        ) is not None
    ]

    tailoring_values = [
        value
        for item in analyses
        if (
            value := _normalize_score(
                item.get("tailoring_score")
            )
        ) is not None
    ]

    applied = sum(
        1
        for item in applications
        if item.get("status")
        in {
            "applied",
            "interview",
            "offer",
            "rejected",
        }
    )

    interviews = sum(
        1
        for item in applications
        if item.get("status")
        in {
            "interview",
            "offer",
        }
    )

    offers = sum(
        1
        for item in applications
        if item.get("status") == "offer"
    )

    metrics = {
        "total_analyses": len(
            analyses
        ),
        "avg_career_fit": _average(
            fit_values
        ),
        "avg_ats_score": _average(
            ats_values
        ),
        "avg_tailoring_score": _average(
            tailoring_values
        ),
        "best_career_fit": (
            round(max(fit_values), 2)
            if fit_values
            else 0.0
        ),
        "total_applications": len(
            applications
        ),
        "applied": applied,
        "interviews": interviews,
        "offers": offers,
    }

    metrics["interview_conversion"] = (
        round(
            (
                interviews
                / applied
            )
            * 100,
            2,
        )
        if applied
        else 0.0
    )

    return metrics


# ============================================================
# CLEANUP / TEST SUPPORT
# ============================================================


def delete_user_cascade(
    user_id: str,
) -> None:
    """
    Test/support helper. PostgreSQL ON DELETE CASCADE removes dependent rows.
    Not intended for normal UI use.
    """

    _request(
        "users",
        method="DELETE",
        params={
            "id": f"eq.{user_id}",
        },
        return_representation=False,
    )


# ============================================================
# ISOLATED SELF TEST
# ============================================================


def run_self_test() -> dict[str, Any]:
    """
    Safe integration test against the configured Supabase project.

    Creates one temporary user and dependent records, validates the adapter,
    then deletes the test user. ON DELETE CASCADE cleans the dependent rows.
    """

    health = database_health_check()

    if health.get("status") != "ok":
        return {
            "status": "error",
            "stage": "health_check",
            "detail": health,
        }

    test_token = uuid.uuid4().hex[:10]
    user_id: str | None = None

    try:
        user_id = create_user(
            name=f"CareerCompass Adapter Test {test_token}",
            email=f"adapter-test-{test_token}@example.invalid",
        )

        profile_id = save_career_profile(
            user_id=user_id,
            raw_profile_text=(
                "Teste temporário de persistência Supabase."
            ),
            structured_profile={
                "candidate_name": "Adapter Test",
                "seniority": "Teste",
            },
            profile_name="CV Teste Supabase",
            source_name="test.docx",
            content_hash=f"hash-{test_token}",
            profile_type="resume",
        )

        deduplicated_profile_id = save_career_profile(
            user_id=user_id,
            raw_profile_text=(
                "Teste temporário de persistência Supabase."
            ),
            structured_profile={
                "candidate_name": "Adapter Test",
                "seniority": "Teste",
            },
            profile_name="CV Teste Supabase",
            source_name="test.docx",
            content_hash=f"hash-{test_token}",
            profile_type="resume",
        )

        if deduplicated_profile_id != profile_id:
            raise AssertionError(
                "Deduplicação de perfil falhou."
            )

        opportunity_id = save_opportunity(
            user_id=user_id,
            job_title="Opportunity Adapter Test",
            job_description=(
                "Temporary opportunity for Supabase adapter validation."
            ),
            company="CareerCompass Test Company",
            source="self_test",
        )

        analysis_id = save_analysis(
            user_id=user_id,
            profile_id=profile_id,
            opportunity_id=opportunity_id,
            career_fit_score=82,
            ats_score=88,
            tailoring_score=91,
            classification="Strong Fit",
            recommendation="Proceed",
            career_fit_report={
                "score": 82,
            },
            ats_report={
                "score": 88,
            },
            recommendation_report={
                "recommendation": "Proceed",
            },
            tailoring_report={
                "tailoring_score": 91,
            },
        )

        application_id = create_application(
            user_id=user_id,
            opportunity_id=opportunity_id,
            analysis_id=analysis_id,
            status="applied",
            notes="Self-test",
        )

        update_application_status(
            application_id=application_id,
            status="interview",
        )

        profiles = list_career_profiles(
            user_id
        )
        opportunities = list_opportunities(
            user_id
        )
        analyses = list_analyses(
            user_id
        )
        applications = list_applications(
            user_id
        )
        events = list_events(
            user_id
        )
        metrics = get_career_metrics(
            user_id
        )

        assert len(profiles) == 1
        assert len(opportunities) == 1
        assert len(analyses) == 1
        assert len(applications) == 1
        assert applications[0]["status"] == "interview"
        assert len(events) >= 5
        assert metrics["total_analyses"] == 1
        assert metrics["avg_career_fit"] == 82.0
        assert metrics["avg_ats_score"] == 88.0
        assert metrics["avg_tailoring_score"] == 91.0
        assert metrics["interviews"] == 1

        return {
            "status": "ok",
            "backend": "supabase",
            "profile_deduplication": "ok",
            "opportunities": len(
                opportunities
            ),
            "analyses": len(
                analyses
            ),
            "applications": len(
                applications
            ),
            "events": len(
                events
            ),
            "metrics": metrics,
        }

    except Exception as exc:
        return {
            "status": "error",
            "backend": "supabase",
            "error": str(exc),
            "error_type": type(exc).__name__,
        }

    finally:
        if user_id:
            try:
                delete_user_cascade(
                    user_id
                )
            except Exception:
                # Cleanup failure must not expose secrets or hide the test result.
                pass


def _running_in_streamlit() -> bool:
    if st is None:
        return False

    try:
        from streamlit.runtime.scriptrunner import (
            get_script_run_ctx,
        )
        return get_script_run_ctx() is not None
    except Exception:
        return False


def render_self_test() -> None:
    if st is None:
        return

    st.set_page_config(
        page_title="CareerCompass AI — Supabase Adapter Test",
        page_icon="🧭",
        layout="centered",
    )

    st.title("CareerCompass AI")
    st.subheader(
        "Sprint 3 — Supabase Database Engine"
    )

    st.caption(
        "Teste isolado de CRUD. Os registros temporários "
        "são removidos ao final."
    )

    with st.spinner(
        "Validando persistência cloud..."
    ):
        result = run_self_test()

    if result.get("status") == "ok":
        st.success("Status: OK")
        st.write(
            "Backend:",
            result.get("backend"),
        )
        st.write(
            "Profile deduplication:",
            result.get(
                "profile_deduplication"
            ),
        )
        st.write(
            "Opportunities:",
            result.get("opportunities"),
        )
        st.write(
            "Analyses:",
            result.get("analyses"),
        )
        st.write(
            "Applications:",
            result.get("applications"),
        )
        st.write(
            "Events:",
            result.get("events"),
        )
        st.json(
            result.get("metrics", {})
        )
    else:
        st.error("Status: ERROR")
        st.code(
            result.get(
                "error",
                str(result),
            ),
            language="text",
        )


if __name__ == "__main__":
    if _running_in_streamlit():
        render_self_test()
    else:
        result = run_self_test()
        print()
        print(
            "CareerCompass AI — Supabase Database Engine"
        )
        print(
            "-------------------------------------------"
        )
        print(
            f"Status: {result.get('status')}"
        )
        print(
            f"Backend: {result.get('backend', 'supabase')}"
        )

        if result.get("status") == "ok":
            print(
                "Profile deduplication: "
                f"{result.get('profile_deduplication')}"
            )
            print(
                f"Opportunities: {result.get('opportunities')}"
            )
            print(
                f"Analyses: {result.get('analyses')}"
            )
            print(
                f"Applications: {result.get('applications')}"
            )
            print(
                f"Events: {result.get('events')}"
            )
        else:
            print(
                f"Error: {result.get('error')}"
            )
