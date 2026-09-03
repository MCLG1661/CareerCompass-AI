"""
CareerCompass AI
Database Engine — Persistent Career Intelligence

Responsável pela camada de persistência da plataforma.

Objetivos:
- armazenar perfis profissionais;
- armazenar oportunidades;
- preservar análises de Career Fit / ATS;
- registrar candidaturas;
- construir histórico longitudinal;
- preparar a arquitetura para PostgreSQL/Supabase.

A implementação inicial utiliza SQLite para permitir desenvolvimento
local sem dependências externas. A interface foi estruturada para
facilitar futura migração para PostgreSQL.
"""

from __future__ import annotations

import json
import sqlite3
import uuid

from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "careercompass.db"

SCHEMA_VERSION = "1.0"


# ============================================================
# UTILITÁRIOS
# ============================================================


def utc_now() -> str:
    """Retorna timestamp UTC padronizado em ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def generate_id(prefix: str) -> str:
    """Gera identificador legível e globalmente único."""
    return f"{prefix}_{uuid.uuid4().hex}"


def serialize_json(value: Any) -> str:
    """
    Serializa estruturas Python para JSON.

    Aceita:
    - dict
    - list
    - tuple
    - dataclass
    - objetos simples
    """
    if value is None:
        return "{}"

    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)

    return json.dumps(
        value,
        ensure_ascii=False,
        default=str,
    )


def deserialize_json(value: str | None) -> Any:
    """Converte JSON armazenado no banco novamente para Python."""
    if not value:
        return {}

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


# ============================================================
# CONEXÃO
# ============================================================


def ensure_data_directory() -> None:
    """Garante que o diretório de dados exista."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Abre conexão SQLite configurada para retornar registros
    semelhantes a dicionários.
    """
    ensure_data_directory()

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("PRAGMA foreign_keys = ON;")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# ============================================================
# SCHEMA
# ============================================================


def initialize_database() -> None:
    """
    Inicializa toda a estrutura persistente do CareerCompass AI.

    Pode ser executada várias vezes com segurança.
    """
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS system_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS career_profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                profile_name TEXT NOT NULL,
                raw_profile_text TEXT,
                structured_profile TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                job_title TEXT NOT NULL,
                company TEXT,
                job_description TEXT NOT NULL,
                source TEXT,
                source_url TEXT,
                status TEXT NOT NULL DEFAULT 'analyzed',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,

                career_fit_score REAL,
                ats_score REAL,
                tailoring_score REAL,

                classification TEXT,
                recommendation TEXT,

                career_fit_report TEXT,
                ats_report TEXT,
                recommendation_report TEXT,
                tailoring_report TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (profile_id)
                    REFERENCES career_profiles(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (opportunity_id)
                    REFERENCES opportunities(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,
                analysis_id TEXT,

                status TEXT NOT NULL DEFAULT 'planned',
                applied_at TEXT,
                interview_at TEXT,
                outcome TEXT,
                notes TEXT,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (opportunity_id)
                    REFERENCES opportunities(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (analysis_id)
                    REFERENCES analyses(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS career_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                event_data TEXT,
                created_at TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_profiles_user
            ON career_profiles(user_id);

            CREATE INDEX IF NOT EXISTS idx_opportunities_user
            ON opportunities(user_id);

            CREATE INDEX IF NOT EXISTS idx_analyses_user
            ON analyses(user_id);

            CREATE INDEX IF NOT EXISTS idx_analyses_opportunity
            ON analyses(opportunity_id);

            CREATE INDEX IF NOT EXISTS idx_applications_user
            ON applications(user_id);

            CREATE INDEX IF NOT EXISTS idx_events_user
            ON career_events(user_id);

            CREATE INDEX IF NOT EXISTS idx_events_type
            ON career_events(event_type);
            """
        )

        connection.execute(
            """
            INSERT INTO system_metadata (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key)
            DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (
                "schema_version",
                SCHEMA_VERSION,
                utc_now(),
            ),
        )


# ============================================================
# USERS
# ============================================================


def create_user(
    name: str | None = None,
    email: str | None = None,
) -> str:
    """Cria usuário e retorna seu ID."""
    user_id = generate_id("usr")
    timestamp = utc_now()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (
                id,
                name,
                email,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                email,
                timestamp,
                timestamp,
            ),
        )

    return user_id


def get_user(user_id: str) -> dict[str, Any] | None:
    """Recupera um usuário pelo ID."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    return dict(row) if row else None


# ============================================================
# CAREER PROFILE
# ============================================================


def save_career_profile(
    user_id: str,
    raw_profile_text: str,
    structured_profile: Any,
    profile_name: str = "Perfil principal",
) -> str:
    """Persiste um Career Intelligence Profile."""
    profile_id = generate_id("prf")
    timestamp = utc_now()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO career_profiles (
                id,
                user_id,
                profile_name,
                raw_profile_text,
                structured_profile,
                is_active,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                user_id,
                profile_name,
                raw_profile_text,
                serialize_json(structured_profile),
                1,
                timestamp,
                timestamp,
            ),
        )

    log_event(
        user_id=user_id,
        event_type="profile_created",
        entity_type="career_profile",
        entity_id=profile_id,
        event_data={
            "profile_name": profile_name,
        },
    )

    return profile_id


def get_career_profile(profile_id: str) -> dict[str, Any] | None:
    """Recupera perfil profissional persistido."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM career_profiles
            WHERE id = ?
            """,
            (profile_id,),
        ).fetchone()

    if not row:
        return None

    profile = dict(row)
    profile["structured_profile"] = deserialize_json(
        profile.get("structured_profile")
    )

    return profile


def get_active_profile(user_id: str) -> dict[str, Any] | None:
    """Retorna o perfil ativo mais recente do usuário."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM career_profiles
            WHERE user_id = ?
              AND is_active = 1
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    if not row:
        return None

    profile = dict(row)
    profile["structured_profile"] = deserialize_json(
        profile.get("structured_profile")
    )

    return profile


# ============================================================
# OPPORTUNITIES
# ============================================================


def save_opportunity(
    user_id: str,
    job_title: str,
    job_description: str,
    company: str | None = None,
    source: str | None = None,
    source_url: str | None = None,
) -> str:
    """Persiste uma oportunidade analisada."""
    opportunity_id = generate_id("opp")
    timestamp = utc_now()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO opportunities (
                id,
                user_id,
                job_title,
                company,
                job_description,
                source,
                source_url,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity_id,
                user_id,
                job_title,
                company,
                job_description,
                source,
                source_url,
                "analyzed",
                timestamp,
                timestamp,
            ),
        )

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


def get_opportunity(opportunity_id: str) -> dict[str, Any] | None:
    """Recupera uma oportunidade."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM opportunities
            WHERE id = ?
            """,
            (opportunity_id,),
        ).fetchone()

    return dict(row) if row else None


def list_opportunities(
    user_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Lista oportunidades mais recentes do usuário."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM opportunities
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (
                user_id,
                limit,
            ),
        ).fetchall()

    return [dict(row) for row in rows]


# ============================================================
# ANALYSES
# ============================================================


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
    """Persiste uma análise completa de Career Intelligence."""
    analysis_id = generate_id("ana")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO analyses (
                id,
                user_id,
                profile_id,
                opportunity_id,
                career_fit_score,
                ats_score,
                tailoring_score,
                classification,
                recommendation,
                career_fit_report,
                ats_report,
                recommendation_report,
                tailoring_report,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                analysis_id,
                user_id,
                profile_id,
                opportunity_id,
                career_fit_score,
                ats_score,
                tailoring_score,
                classification,
                recommendation,
                serialize_json(career_fit_report),
                serialize_json(ats_report),
                serialize_json(recommendation_report),
                serialize_json(tailoring_report),
                utc_now(),
            ),
        )

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


def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    """Recupera análise persistida."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM analyses
            WHERE id = ?
            """,
            (analysis_id,),
        ).fetchone()

    if not row:
        return None

    analysis = dict(row)

    json_fields = (
        "career_fit_report",
        "ats_report",
        "recommendation_report",
        "tailoring_report",
    )

    for field in json_fields:
        analysis[field] = deserialize_json(analysis.get(field))

    return analysis


def list_analyses(
    user_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Lista análises recentes do usuário."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                analyses.*,
                opportunities.job_title,
                opportunities.company
            FROM analyses
            INNER JOIN opportunities
                ON opportunities.id = analyses.opportunity_id
            WHERE analyses.user_id = ?
            ORDER BY analyses.created_at DESC
            LIMIT ?
            """,
            (
                user_id,
                limit,
            ),
        ).fetchall()

    return [dict(row) for row in rows]


# ============================================================
# APPLICATION TRACKER
# ============================================================


def create_application(
    user_id: str,
    opportunity_id: str,
    analysis_id: str | None = None,
    status: str = "planned",
    notes: str | None = None,
) -> str:
    """Cria registro de candidatura."""
    application_id = generate_id("app")
    timestamp = utc_now()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO applications (
                id,
                user_id,
                opportunity_id,
                analysis_id,
                status,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                application_id,
                user_id,
                opportunity_id,
                analysis_id,
                status,
                notes,
                timestamp,
                timestamp,
            ),
        )

    log_event(
        user_id=user_id,
        event_type="application_created",
        entity_type="application",
        entity_id=application_id,
        event_data={
            "opportunity_id": opportunity_id,
            "status": status,
        },
    )

    return application_id


def update_application_status(
    application_id: str,
    status: str,
    outcome: str | None = None,
    notes: str | None = None,
) -> None:
    """Atualiza estágio da candidatura."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT user_id
            FROM applications
            WHERE id = ?
            """,
            (application_id,),
        ).fetchone()

        if not row:
            raise ValueError(
                f"Candidatura não encontrada: {application_id}"
            )

        user_id = row["user_id"]

        applied_at = None
        interview_at = None

        if status == "applied":
            applied_at = utc_now()

        if status == "interview":
            interview_at = utc_now()

        connection.execute(
            """
            UPDATE applications
            SET
                status = ?,
                outcome = COALESCE(?, outcome),
                notes = COALESCE(?, notes),
                applied_at = COALESCE(?, applied_at),
                interview_at = COALESCE(?, interview_at),
                updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                outcome,
                notes,
                applied_at,
                interview_at,
                utc_now(),
                application_id,
            ),
        )

    log_event(
        user_id=user_id,
        event_type="application_status_changed",
        entity_type="application",
        entity_id=application_id,
        event_data={
            "status": status,
            "outcome": outcome,
        },
    )


def list_applications(
    user_id: str,
) -> list[dict[str, Any]]:
    """Lista pipeline de candidaturas."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                applications.*,
                opportunities.job_title,
                opportunities.company
            FROM applications
            INNER JOIN opportunities
                ON opportunities.id = applications.opportunity_id
            WHERE applications.user_id = ?
            ORDER BY applications.updated_at DESC
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


# ============================================================
# EVENT / PRODUCT ANALYTICS
# ============================================================


def log_event(
    user_id: str,
    event_type: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    event_data: Any = None,
) -> str:
    """
    Registra eventos de utilização.

    Essa tabela será a base para Career Analytics e
    Product Analytics.
    """
    event_id = generate_id("evt")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO career_events (
                id,
                user_id,
                event_type,
                entity_type,
                entity_id,
                event_data,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                user_id,
                event_type,
                entity_type,
                entity_id,
                serialize_json(event_data),
                utc_now(),
            ),
        )

    return event_id


def list_events(
    user_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Retorna eventos recentes."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM career_events
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (
                user_id,
                limit,
            ),
        ).fetchall()

    events: list[dict[str, Any]] = []

    for row in rows:
        event = dict(row)
        event["event_data"] = deserialize_json(
            event.get("event_data")
        )
        events.append(event)

    return events


# ============================================================
# CAREER ANALYTICS
# ============================================================


def get_career_metrics(user_id: str) -> dict[str, Any]:
    """
    Calcula indicadores longitudinais básicos do usuário.

    Esses dados futuramente alimentarão o
    Career Intelligence Dashboard.
    """
    with get_connection() as connection:
        analysis_metrics = connection.execute(
            """
            SELECT
                COUNT(*) AS total_analyses,
                AVG(career_fit_score) AS avg_career_fit,
                AVG(ats_score) AS avg_ats_score,
                AVG(tailoring_score) AS avg_tailoring_score,
                MAX(career_fit_score) AS best_career_fit
            FROM analyses
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        application_metrics = connection.execute(
            """
            SELECT
                COUNT(*) AS total_applications,

                SUM(
                    CASE
                        WHEN status = 'applied'
                        THEN 1
                        ELSE 0
                    END
                ) AS applied,

                SUM(
                    CASE
                        WHEN status = 'interview'
                        THEN 1
                        ELSE 0
                    END
                ) AS interviews,

                SUM(
                    CASE
                        WHEN status = 'offer'
                        THEN 1
                        ELSE 0
                    END
                ) AS offers

            FROM applications
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    metrics = {
        "total_analyses": analysis_metrics["total_analyses"] or 0,
        "avg_career_fit": round(
            analysis_metrics["avg_career_fit"] or 0,
            2,
        ),
        "avg_ats_score": round(
            analysis_metrics["avg_ats_score"] or 0,
            2,
        ),
        "avg_tailoring_score": round(
            analysis_metrics["avg_tailoring_score"] or 0,
            2,
        ),
        "best_career_fit": round(
            analysis_metrics["best_career_fit"] or 0,
            2,
        ),
        "total_applications": (
            application_metrics["total_applications"] or 0
        ),
        "applied": application_metrics["applied"] or 0,
        "interviews": application_metrics["interviews"] or 0,
        "offers": application_metrics["offers"] or 0,
    }

    if metrics["total_applications"]:
        metrics["interview_conversion"] = round(
            (
                metrics["interviews"]
                / metrics["total_applications"]
            )
            * 100,
            2,
        )
    else:
        metrics["interview_conversion"] = 0.0

    return metrics


# ============================================================
# HEALTH CHECK
# ============================================================


def database_health_check() -> dict[str, Any]:
    """Verifica se a camada de persistência está operacional."""
    initialize_database()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT value
            FROM system_metadata
            WHERE key = 'schema_version'
            """
        ).fetchone()

        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

    return {
        "status": "ok",
        "database": str(DATABASE_PATH),
        "schema_version": row["value"] if row else None,
        "tables": [table["name"] for table in tables],
    }


# ============================================================
# BOOTSTRAP
# ============================================================

if __name__ == "__main__":
    result = database_health_check()

    print("CareerCompass AI — Database Engine")
    print("----------------------------------")
    print(f"Status: {result['status']}")
    print(f"Schema: {result['schema_version']}")
    print(f"Database: {result['database']}")
    print("Tables:")

    for table_name in result["tables"]:
        print(f" - {table_name}")
