"""
CareerCompass AI
Persistence Service

Service layer between the application engines and the persistence layer.
"""

from __future__ import annotations

from typing import Any

# Storage backend selection:
# - Streamlit Cloud / environment with Supabase Secrets -> Supabase
# - Local development without Supabase Secrets -> existing SQLite
#
# CAREERCOMPASS_STORAGE_BACKEND can explicitly force "sqlite" or "supabase".
import os

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None


def _secret_exists(name: str) -> bool:
    if st is not None:
        try:
            if st.secrets.get(name):
                return True
        except Exception:
            pass
    return bool(os.getenv(name))


def _select_storage_backend() -> str:
    forced = os.getenv("CAREERCOMPASS_STORAGE_BACKEND", "").strip().lower()
    if forced in {"sqlite", "supabase"}:
        return forced

    if _secret_exists("SUPABASE_URL") and _secret_exists("SUPABASE_SECRET_KEY"):
        return "supabase"

    return "sqlite"


STORAGE_BACKEND = _select_storage_backend()

if STORAGE_BACKEND == "supabase":
    from supabase_database_engine import (
        create_application,
        database_health_check,
        activate_career_profile,
        get_active_profile,
        get_analysis,
        get_career_metrics,
        get_career_profile,
        get_opportunity,
        get_or_create_default_user,
        get_user,
        initialize_database,
        list_analyses,
        list_career_profiles,
        list_applications,
        list_events,
        list_opportunities,
        log_event,
        rename_career_profile,
        save_analysis,
        save_career_profile,
        save_opportunity,
        update_application_status,
    )
else:
    from database_engine import (
        create_application,
        database_health_check,
        activate_career_profile,
        get_active_profile,
        get_analysis,
        get_career_metrics,
        get_career_profile,
        get_opportunity,
        get_or_create_default_user,
        get_user,
        initialize_database,
        list_analyses,
        list_career_profiles,
        list_applications,
        list_events,
        list_opportunities,
        log_event,
        rename_career_profile,
        save_analysis,
        save_career_profile,
        save_opportunity,
        update_application_status,
    )


def get_storage_backend() -> str:
    """Return the active persistence backend: 'sqlite' or 'supabase'."""
    return STORAGE_BACKEND

DEFAULT_USER_NAME = "CareerCompass User"
DEFAULT_PROFILE_NAME = "Perfil principal"


def initialize_persistence() -> dict[str, Any]:
    initialize_database()
    health = database_health_check()
    if isinstance(health, dict):
        return {
            **health,
            "backend": STORAGE_BACKEND,
        }
    return {
        "status": "ok",
        "backend": STORAGE_BACKEND,
        "health": health,
    }


def ensure_user(
    user_id: str | None = None,
    name: str | None = None,
    email: str | None = None,
) -> str:
    """Return an existing user or the same persistent local user across restarts."""
    if user_id:
        existing_user = get_user(user_id)
        if existing_user:
            return user_id

    return get_or_create_default_user(
        name=name or DEFAULT_USER_NAME,
        email=email,
    )


def persist_profile(
    user_id: str,
    raw_profile_text: str,
    structured_profile: Any,
    profile_name: str = DEFAULT_PROFILE_NAME,
    source_name: str | None = None,
    content_hash: str | None = None,
    profile_type: str = "resume",
) -> str:
    if not user_id:
        raise ValueError("user_id é obrigatório.")
    if not raw_profile_text and not structured_profile:
        raise ValueError(
            "É necessário fornecer conteúdo para o perfil profissional."
        )
    return save_career_profile(
        user_id=user_id,
        raw_profile_text=raw_profile_text,
        structured_profile=structured_profile,
        profile_name=profile_name,
        source_name=source_name,
        content_hash=content_hash,
        profile_type=profile_type,
    )


def get_profile_repository(user_id: str) -> list[dict[str, Any]]:
    return list_career_profiles(user_id) if user_id else []


def activate_profile(user_id: str, profile_id: str) -> dict[str, Any] | None:
    if not user_id or not profile_id:
        raise ValueError("user_id e profile_id são obrigatórios.")
    activate_career_profile(user_id, profile_id)
    return get_career_profile(profile_id)


def rename_profile(user_id: str, profile_id: str, profile_name: str) -> None:
    if not user_id or not profile_id:
        raise ValueError("user_id e profile_id são obrigatórios.")
    rename_career_profile(user_id, profile_id, profile_name)


def get_user_active_profile(user_id: str) -> dict[str, Any] | None:
    return get_active_profile(user_id) if user_id else None


def load_profile(profile_id: str) -> dict[str, Any] | None:
    return get_career_profile(profile_id) if profile_id else None


def persist_opportunity(
    user_id: str,
    job_title: str,
    job_description: str,
    company: str | None = None,
    source: str | None = None,
    source_url: str | None = None,
) -> str:
    if not user_id:
        raise ValueError("user_id é obrigatório.")
    if not job_title.strip():
        raise ValueError("job_title é obrigatório.")
    if not job_description.strip():
        raise ValueError("job_description é obrigatório.")

    return save_opportunity(
        user_id=user_id,
        job_title=job_title.strip(),
        job_description=job_description.strip(),
        company=company.strip() if company else None,
        source=source,
        source_url=source_url,
    )


def load_opportunity(opportunity_id: str) -> dict[str, Any] | None:
    return get_opportunity(opportunity_id) if opportunity_id else None


def get_opportunity_history(
    user_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return list_opportunities(user_id, limit) if user_id else []


def persist_career_analysis(
    user_id: str,
    profile_id: str,
    opportunity_id: str,
    career_fit_report: Any = None,
    ats_report: Any = None,
    recommendation_report: Any = None,
    tailoring_report: Any = None,
) -> str:
    career_fit_score = extract_score(
        career_fit_report,
        ("score", "career_fit_score", "fit_score", "overall_score"),
    )
    ats_score = extract_score(
        ats_report,
        ("score", "ats_score", "overall_score"),
    )
    tailoring_score = extract_score(
        tailoring_report,
        ("tailoring_score", "score", "readiness_score"),
    )
    classification = extract_text(
        ats_report,
        ("classification", "classificacao"),
    )
    recommendation = extract_text(
        recommendation_report,
        ("recommendation", "decision", "positioning", "next_action"),
    )

    return save_analysis(
        user_id=user_id,
        profile_id=profile_id,
        opportunity_id=opportunity_id,
        career_fit_score=career_fit_score,
        ats_score=ats_score,
        tailoring_score=tailoring_score,
        classification=classification,
        recommendation=recommendation,
        career_fit_report=career_fit_report,
        ats_report=ats_report,
        recommendation_report=recommendation_report,
        tailoring_report=tailoring_report,
    )


def load_analysis(analysis_id: str) -> dict[str, Any] | None:
    return get_analysis(analysis_id) if analysis_id else None


def get_analysis_history(
    user_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return list_analyses(user_id, limit) if user_id else []


def persist_application(
    user_id: str,
    opportunity_id: str,
    analysis_id: str | None = None,
    status: str = "planned",
    notes: str | None = None,
) -> str:
    valid_statuses = {
        "planned",
        "applied",
        "interview",
        "offer",
        "rejected",
        "withdrawn",
    }
    normalized_status = status.strip().lower()
    if normalized_status not in valid_statuses:
        raise ValueError(
            f"Status inválido: {status}. Valores aceitos: {sorted(valid_statuses)}"
        )

    return create_application(
        user_id=user_id,
        opportunity_id=opportunity_id,
        analysis_id=analysis_id,
        status=normalized_status,
        notes=notes,
    )


def change_application_status(
    application_id: str,
    status: str,
    outcome: str | None = None,
    notes: str | None = None,
) -> None:
    valid_statuses = {
        "planned",
        "applied",
        "interview",
        "offer",
        "rejected",
        "withdrawn",
    }
    normalized_status = status.strip().lower()
    if normalized_status not in valid_statuses:
        raise ValueError(
            f"Status inválido: {status}. Valores aceitos: {sorted(valid_statuses)}"
        )

    update_application_status(
        application_id=application_id,
        status=normalized_status,
        outcome=outcome,
        notes=notes,
    )


def get_application_pipeline(user_id: str) -> list[dict[str, Any]]:
    return list_applications(user_id) if user_id else []


def get_career_dashboard_metrics(user_id: str) -> dict[str, Any]:
    if not user_id:
        return empty_metrics()
    return {
        **empty_metrics(),
        **get_career_metrics(user_id),
    }


def empty_metrics() -> dict[str, Any]:
    return {
        "total_analyses": 0,
        "avg_career_fit": 0.0,
        "avg_ats_score": 0.0,
        "avg_tailoring_score": 0.0,
        "best_career_fit": 0.0,
        "total_applications": 0,
        "applied": 0,
        "interviews": 0,
        "offers": 0,
        "interview_conversion": 0.0,
    }


def register_product_event(
    user_id: str,
    event_type: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    event_data: Any = None,
) -> str:
    if not user_id:
        raise ValueError("user_id é obrigatório.")
    if not event_type:
        raise ValueError("event_type é obrigatório.")
    return log_event(
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        event_data=event_data,
    )


def get_event_history(
    user_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return list_events(user_id, limit) if user_id else []


def extract_score(
    report: Any,
    candidate_keys: tuple[str, ...],
) -> float | None:
    if report is None:
        return None
    for key in candidate_keys:
        value = extract_value(report, key)
        if value is None:
            continue
        score = normalize_numeric_score(value)
        if score is not None:
            return score
    return None


def extract_text(
    report: Any,
    candidate_keys: tuple[str, ...],
) -> str | None:
    if report is None:
        return None
    for key in candidate_keys:
        value = extract_value(report, key)
        if value is not None:
            text = str(value).strip()
            if text:
                return text
    return None


def extract_value(report: Any, key: str) -> Any:
    if isinstance(report, dict):
        return report.get(key)
    return getattr(report, key, None)


def normalize_numeric_score(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    if isinstance(value, str):
        cleaned = value.replace("%", "").replace(",", ".").strip()
        try:
            return round(float(cleaned), 2)
        except ValueError:
            return None
    return None


def build_career_snapshot(user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "active_profile": get_user_active_profile(user_id),
        "profiles": get_profile_repository(user_id),
        "metrics": get_career_dashboard_metrics(user_id),
        "recent_opportunities": get_opportunity_history(user_id, limit=20),
        "recent_analyses": get_analysis_history(user_id, limit=20),
        "applications": get_application_pipeline(user_id),
    }


def run_self_test() -> dict[str, Any]:
    initialize_persistence()
    user_id = ensure_user(name="CareerCompass User")
    return {
        "status": "ok",
        "backend": STORAGE_BACKEND,
        "user_id": user_id,
        "metrics": get_career_dashboard_metrics(user_id),
    }


if __name__ == "__main__":
    result = run_self_test()
    print()
    print("CareerCompass AI — Persistence Service")
    print("--------------------------------------")
    print(f"Status: {result['status']}")
    print(f"Backend: {result.get('backend', STORAGE_BACKEND)}")
    print(f"User: {result['user_id']}")
    print()
    print("Career Metrics")
    print("--------------------------------------")
    for key, value in result["metrics"].items():
        print(f"{key}: {value}")
