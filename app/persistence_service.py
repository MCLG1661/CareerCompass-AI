"""
CareerCompass AI
Persistence Service

Camada de serviço responsável por conectar os engines de Career Intelligence
à camada de persistência.

Objetivos:
- centralizar operações de persistência;
- reduzir acoplamento entre main.py e database_engine.py;
- preparar futura migração SQLite -> PostgreSQL/Supabase;
- manter histórico longitudinal de análises;
- padronizar criação de usuário, perfil, oportunidade e candidatura.
"""

from __future__ import annotations

from typing import Any

from database_engine import (
    create_application,
    create_user,
    database_health_check,
    get_active_profile,
    get_analysis,
    get_career_metrics,
    get_career_profile,
    get_opportunity,
    get_user,
    initialize_database,
    list_analyses,
    list_applications,
    list_events,
    list_opportunities,
    log_event,
    save_analysis,
    save_career_profile,
    save_opportunity,
    update_application_status,
)


# ============================================================
# CONSTANTES
# ============================================================

DEFAULT_USER_NAME = "CareerCompass User"

DEFAULT_PROFILE_NAME = "Perfil principal"


# ============================================================
# BOOTSTRAP
# ============================================================


def initialize_persistence() -> dict[str, Any]:
    """
    Inicializa a infraestrutura persistente.

    Deve ser chamada na inicialização da aplicação.
    """
    initialize_database()

    return database_health_check()


# ============================================================
# USER SERVICE
# ============================================================


def ensure_user(
    user_id: str | None = None,
    name: str | None = None,
    email: str | None = None,
) -> str:
    """
    Retorna um usuário existente ou cria um novo.

    Enquanto o CareerCompass ainda não possui autenticação,
    essa função permite manter um usuário persistente simples.
    """
    if user_id:
        existing_user = get_user(user_id)

        if existing_user:
            return user_id

    return create_user(
        name=name or DEFAULT_USER_NAME,
        email=email,
    )


# ============================================================
# PROFILE SERVICE
# ============================================================


def persist_profile(
    user_id: str,
    raw_profile_text: str,
    structured_profile: Any,
    profile_name: str = DEFAULT_PROFILE_NAME,
) -> str:
    """
    Persiste um Career Intelligence Profile.
    """
    if not user_id:
        raise ValueError("user_id é obrigatório.")

    if not raw_profile_text and not structured_profile:
        raise ValueError(
            "É necessário fornecer conteúdo para o perfil profissional."
        )

    profile_id = save_career_profile(
        user_id=user_id,
        raw_profile_text=raw_profile_text,
        structured_profile=structured_profile,
        profile_name=profile_name,
    )

    return profile_id


def get_user_active_profile(
    user_id: str,
) -> dict[str, Any] | None:
    """
    Retorna o perfil profissional ativo do usuário.
    """
    if not user_id:
        return None

    return get_active_profile(user_id)


def load_profile(
    profile_id: str,
) -> dict[str, Any] | None:
    """
    Recupera um perfil específico.
    """
    if not profile_id:
        return None

    return get_career_profile(profile_id)


# ============================================================
# OPPORTUNITY SERVICE
# ============================================================


def persist_opportunity(
    user_id: str,
    job_title: str,
    job_description: str,
    company: str | None = None,
    source: str | None = None,
    source_url: str | None = None,
) -> str:
    """
    Registra uma oportunidade profissional.
    """
    if not user_id:
        raise ValueError("user_id é obrigatório.")

    if not job_title.strip():
        raise ValueError("job_title é obrigatório.")

    if not job_description.strip():
        raise ValueError("job_description é obrigatório.")

    opportunity_id = save_opportunity(
        user_id=user_id,
        job_title=job_title.strip(),
        job_description=job_description.strip(),
        company=company.strip() if company else None,
        source=source,
        source_url=source_url,
    )

    return opportunity_id


def load_opportunity(
    opportunity_id: str,
) -> dict[str, Any] | None:
    """
    Recupera uma oportunidade pelo ID.
    """
    if not opportunity_id:
        return None

    return get_opportunity(opportunity_id)


def get_opportunity_history(
    user_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Retorna o histórico de oportunidades analisadas.
    """
    if not user_id:
        return []

    return list_opportunities(
        user_id=user_id,
        limit=limit,
    )


# ============================================================
# ANALYSIS SERVICE
# ============================================================


def persist_career_analysis(
    user_id: str,
    profile_id: str,
    opportunity_id: str,
    career_fit_report: Any = None,
    ats_report: Any = None,
    recommendation_report: Any = None,
    tailoring_report: Any = None,
) -> str:
    """
    Persiste uma análise completa de Career Intelligence.

    Extrai automaticamente scores dos relatórios quando possível.
    """

    career_fit_score = extract_score(
        career_fit_report,
        (
            "score",
            "career_fit_score",
            "fit_score",
            "overall_score",
        ),
    )

    ats_score = extract_score(
        ats_report,
        (
            "score",
            "ats_score",
            "overall_score",
        ),
    )

    tailoring_score = extract_score(
        tailoring_report,
        (
            "tailoring_score",
            "score",
            "readiness_score",
        ),
    )

    classification = extract_text(
        ats_report,
        (
            "classification",
            "classificacao",
        ),
    )

    recommendation = extract_text(
        recommendation_report,
        (
            "recommendation",
            "decision",
            "positioning",
            "next_action",
        ),
    )

    analysis_id = save_analysis(
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

    return analysis_id


def load_analysis(
    analysis_id: str,
) -> dict[str, Any] | None:
    """
    Recupera uma análise completa.
    """
    if not analysis_id:
        return None

    return get_analysis(analysis_id)


def get_analysis_history(
    user_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Retorna histórico de análises.
    """
    if not user_id:
        return []

    return list_analyses(
        user_id=user_id,
        limit=limit,
    )


# ============================================================
# APPLICATION TRACKER SERVICE
# ============================================================


def persist_application(
    user_id: str,
    opportunity_id: str,
    analysis_id: str | None = None,
    status: str = "planned",
    notes: str | None = None,
) -> str:
    """
    Cria uma candidatura no pipeline.
    """
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
            f"Status inválido: {status}. "
            f"Valores aceitos: {sorted(valid_statuses)}"
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
    """
    Atualiza uma candidatura existente.
    """
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
            f"Status inválido: {status}. "
            f"Valores aceitos: {sorted(valid_statuses)}"
        )

    update_application_status(
        application_id=application_id,
        status=normalized_status,
        outcome=outcome,
        notes=notes,
    )


def get_application_pipeline(
    user_id: str,
) -> list[dict[str, Any]]:
    """
    Retorna candidaturas do usuário.
    """
    if not user_id:
        return []

    return list_applications(user_id)


# ============================================================
# CAREER ANALYTICS SERVICE
# ============================================================


def get_career_dashboard_metrics(
    user_id: str,
) -> dict[str, Any]:
    """
    Retorna métricas consolidadas para o futuro
    Career Intelligence Dashboard.
    """
    if not user_id:
        return empty_metrics()

    metrics = get_career_metrics(user_id)

    return {
        **empty_metrics(),
        **metrics,
    }


def empty_metrics() -> dict[str, Any]:
    """
    Estrutura padrão de métricas.
    """
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


# ============================================================
# EVENT SERVICE
# ============================================================


def register_product_event(
    user_id: str,
    event_type: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    event_data: Any = None,
) -> str:
    """
    Registra evento de Career Analytics / Product Analytics.
    """
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
    """
    Retorna eventos recentes do usuário.
    """
    if not user_id:
        return []

    return list_events(
        user_id=user_id,
        limit=limit,
    )


# ============================================================
# SCORE HELPERS
# ============================================================


def extract_score(
    report: Any,
    candidate_keys: tuple[str, ...],
) -> float | None:
    """
    Extrai score numérico de um relatório.

    Aceita dict ou objeto com atributos.
    """
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
    """
    Extrai campo textual de um relatório.
    """
    if report is None:
        return None

    for key in candidate_keys:
        value = extract_value(report, key)

        if value is not None:
            text = str(value).strip()

            if text:
                return text

    return None


def extract_value(
    report: Any,
    key: str,
) -> Any:
    """
    Extrai valor de dict ou objeto.
    """
    if isinstance(report, dict):
        return report.get(key)

    return getattr(
        report,
        key,
        None,
    )


def normalize_numeric_score(
    value: Any,
) -> float | None:
    """
    Normaliza diferentes representações de score.

    Exemplos aceitos:
    78
    78.5
    "78"
    "78%"
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(
        value,
        (int, float),
    ):
        return round(float(value), 2)

    if isinstance(value, str):
        cleaned = (
            value
            .replace("%", "")
            .replace(",", ".")
            .strip()
        )

        try:
            return round(float(cleaned), 2)
        except ValueError:
            return None

    return None


# ============================================================
# CAREER INTELLIGENCE SNAPSHOT
# ============================================================


def build_career_snapshot(
    user_id: str,
) -> dict[str, Any]:
    """
    Cria um snapshot consolidado da jornada profissional.

    Essa estrutura poderá ser utilizada posteriormente pelo:
    - dashboard;
    - Career Digital Twin;
    - Recommendation Engine;
    - LLM;
    - relatórios executivos.
    """

    active_profile = get_user_active_profile(user_id)

    opportunities = get_opportunity_history(
        user_id,
        limit=20,
    )

    analyses = get_analysis_history(
        user_id,
        limit=20,
    )

    applications = get_application_pipeline(
        user_id,
    )

    metrics = get_career_dashboard_metrics(
        user_id,
    )

    return {
        "user_id": user_id,
        "active_profile": active_profile,
        "metrics": metrics,
        "recent_opportunities": opportunities,
        "recent_analyses": analyses,
        "applications": applications,
    }


# ============================================================
# SELF TEST
# ============================================================


def run_self_test() -> dict[str, Any]:
    """
    Executa teste seguro da camada de persistência.

    Cria dados de teste somente no banco SQLite local.
    """

    initialize_persistence()

    user_id = ensure_user(
        name="CareerCompass Test User",
    )

    profile_id = persist_profile(
        user_id=user_id,
        raw_profile_text=(
            "Profissional de gestão de projetos, operações e dados."
        ),
        structured_profile={
            "seniority": "Senior",
            "skills": [
                "Gestão de Projetos",
                "Data Analytics",
                "Leadership",
            ],
        },
        profile_name="Perfil de teste",
    )

    opportunity_id = persist_opportunity(
        user_id=user_id,
        job_title="Senior Project Manager",
        company="CareerCompass Test Company",
        job_description=(
            "Buscamos profissional com experiência em gestão "
            "de projetos, liderança e análise de dados."
        ),
        source="self_test",
    )

    analysis_id = persist_career_analysis(
        user_id=user_id,
        profile_id=profile_id,
        opportunity_id=opportunity_id,
        career_fit_report={
            "score": 82,
        },
        ats_report={
            "score": 76,
            "classification": "Alta aderência",
        },
        recommendation_report={
            "recommendation": "Apply after tailoring",
        },
        tailoring_report={
            "tailoring_score": 88,
        },
    )

    application_id = persist_application(
        user_id=user_id,
        opportunity_id=opportunity_id,
        analysis_id=analysis_id,
        status="planned",
    )

    snapshot = build_career_snapshot(
        user_id,
    )

    return {
        "status": "ok",
        "user_id": user_id,
        "profile_id": profile_id,
        "opportunity_id": opportunity_id,
        "analysis_id": analysis_id,
        "application_id": application_id,
        "metrics": snapshot["metrics"],
    }


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================


if __name__ == "__main__":
    result = run_self_test()

    print()
    print("CareerCompass AI — Persistence Service")
    print("--------------------------------------")
    print(f"Status: {result['status']}")
    print(f"User: {result['user_id']}")
    print(f"Profile: {result['profile_id']}")
    print(f"Opportunity: {result['opportunity_id']}")
    print(f"Analysis: {result['analysis_id']}")
    print(f"Application: {result['application_id']}")

    print()
    print("Career Metrics")
    print("--------------------------------------")

    for key, value in result["metrics"].items():
        print(f"{key}: {value}")
