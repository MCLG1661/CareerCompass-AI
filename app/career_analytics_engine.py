"""
CareerCompass AI
Career Analytics Engine

Consolida o histórico de análises profissionais para gerar
Career Intelligence longitudinal.

Objetivos:
- medir evolução de Career Fit, ATS e Tailoring;
- identificar tendência das análises ao longo do tempo;
- detectar gaps recorrentes;
- identificar requisitos mais frequentes;
- produzir prioridades de desenvolvimento;
- gerar insights executivos para o dashboard.

O engine é determinístico e trabalha apenas com dados persistidos.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from gap_intelligence_engine import analyze_career_gaps


# ============================================================
# DATA MODELS
# ============================================================


@dataclass
class AnalyticsPoint:
    index: int
    created_at: str | None
    opportunity_id: str | None
    job_title: str | None
    company: str | None
    career_fit_score: float
    ats_score: float
    tailoring_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RequirementSignal:
    requirement: str
    occurrences: int
    mandatory_occurrences: int
    matched_occurrences: int
    gap_occurrences: int
    match_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CareerAnalyticsReport:
    total_analyses: int
    registered_analyses: int
    excluded_analyses: int

    avg_career_fit: float
    avg_ats_score: float
    avg_tailoring_score: float

    best_career_fit: float
    latest_career_fit: float

    career_fit_trend: float
    ats_trend: float
    tailoring_trend: float

    trend_label: str
    confidence_score: float

    trajectory: list[AnalyticsPoint] = field(default_factory=list)

    top_requirements: list[RequirementSignal] = field(default_factory=list)
    recurrent_gaps: list[dict[str, Any]] = field(default_factory=list)
    development_priorities: list[str] = field(default_factory=list)

    strongest_signals: list[str] = field(default_factory=list)
    risk_signals: list[str] = field(default_factory=list)
    executive_insights: list[str] = field(default_factory=list)

    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# HELPERS
# ============================================================


def get_value(
    source: Any,
    key: str,
    default: Any = None,
) -> Any:
    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(key, default)

    return getattr(source, key, default)


def normalize_score(
    value: Any,
) -> float:
    if value is None or isinstance(value, bool):
        return 0.0

    if isinstance(value, (int, float)):
        score = float(value)

    elif isinstance(value, str):
        cleaned = (
            value
            .replace("%", "")
            .replace(",", ".")
            .strip()
        )

        try:
            score = float(cleaned)
        except ValueError:
            return 0.0

    else:
        return 0.0

    if 0 <= score <= 1:
        score *= 100

    return round(
        max(
            0.0,
            min(score, 100.0),
        ),
        2,
    )


def deserialize_if_needed(
    value: Any,
) -> Any:
    """
    Converte relatórios persistidos em JSON string para dict/list.
    """

    if not isinstance(value, str):
        return value

    text = value.strip()

    if not text:
        return {}

    if not (
        text.startswith("{")
        or text.startswith("[")
    ):
        return value

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def normalize_analysis(
    analysis: Any,
) -> dict[str, Any]:
    """
    Normaliza registros vindos do SQLite/Persistence Service.
    """

    if isinstance(analysis, dict):
        normalized = dict(analysis)
    else:
        normalized = {
            key: getattr(analysis, key)
            for key in dir(analysis)
            if (
                not key.startswith("_")
                and not callable(getattr(analysis, key))
            )
        }

    for key in (
        "career_fit_report",
        "ats_report",
        "recommendation_report",
        "tailoring_report",
    ):
        normalized[key] = deserialize_if_needed(
            normalized.get(key)
        )

    return normalized


def parse_datetime(
    value: Any,
) -> datetime:
    if not value:
        return datetime.min

    text = str(value).strip()

    if not text:
        return datetime.min

    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )
    except ValueError:
        return datetime.min


def sort_analyses_chronologically(
    analyses: list[Any],
) -> list[dict[str, Any]]:
    normalized = [
        normalize_analysis(item)
        for item in analyses
    ]

    return sorted(
        normalized,
        key=lambda item: parse_datetime(
            item.get("created_at")
        ),
    )


def average(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        2,
    )


def score_from_analysis(
    analysis: dict[str, Any],
    direct_key: str,
    report_key: str,
    candidate_keys: tuple[str, ...],
) -> float:
    direct_value = analysis.get(
        direct_key
    )

    if direct_value is not None:
        return normalize_score(
            direct_value
        )

    report = analysis.get(
        report_key,
        {},
    )

    report = deserialize_if_needed(
        report
    )

    for key in candidate_keys:
        value = get_value(
            report,
            key,
        )

        if value is not None:
            return normalize_score(
                value
            )

    return 0.0


def analysis_scores(
    analysis: dict[str, Any],
) -> tuple[float, float, float]:
    """
    Extrai os três scores usados na inteligência longitudinal.
    """

    career_fit = score_from_analysis(
        analysis,
        "career_fit_score",
        "career_fit_report",
        (
            "score",
            "career_fit_score",
            "fit_score",
            "overall_score",
        ),
    )

    ats = score_from_analysis(
        analysis,
        "ats_score",
        "ats_report",
        (
            "score",
            "ats_score",
            "overall_score",
        ),
    )

    tailoring = score_from_analysis(
        analysis,
        "tailoring_score",
        "tailoring_report",
        (
            "tailoring_score",
            "score",
            "readiness_score",
        ),
    )

    return career_fit, ats, tailoring


def is_valid_longitudinal_analysis(
    analysis: Any,
) -> bool:
    """
    Uma análise entra nos KPIs longitudinais quando existe pelo menos
    um resultado analítico real.

    Registros 0/0/0 são preservados no banco, mas tratados como
    incompletos/técnicos e não alteram médias, tendência, gaps,
    confiança ou Career Intelligence Score.

    Um resultado genuinamente baixo (por exemplo 18/19/17) continua
    sendo válido e permanece na trajetória.
    """

    normalized = normalize_analysis(
        analysis
    )

    career_fit, ats, tailoring = analysis_scores(
        normalized
    )

    return any(
        score > 0
        for score in (
            career_fit,
            ats,
            tailoring,
        )
    )


def filter_valid_analyses(
    analyses: list[Any],
) -> tuple[list[dict[str, Any]], int]:
    normalized = [
        normalize_analysis(item)
        for item in (analyses or [])
    ]

    valid = [
        item
        for item in normalized
        if is_valid_longitudinal_analysis(item)
    ]

    excluded = len(normalized) - len(valid)

    return valid, excluded


# ============================================================
# TRAJECTORY
# ============================================================


def build_trajectory(
    analyses: list[Any],
) -> list[AnalyticsPoint]:
    ordered = sort_analyses_chronologically(
        analyses
    )

    result = []

    for index, analysis in enumerate(
        ordered,
        start=1,
    ):
        result.append(
            AnalyticsPoint(
                index=index,
                created_at=analysis.get(
                    "created_at"
                ),
                opportunity_id=analysis.get(
                    "opportunity_id"
                ),
                job_title=analysis.get(
                    "job_title"
                ),
                company=analysis.get(
                    "company"
                ),
                career_fit_score=score_from_analysis(
                    analysis,
                    "career_fit_score",
                    "career_fit_report",
                    (
                        "score",
                        "career_fit_score",
                        "fit_score",
                        "overall_score",
                    ),
                ),
                ats_score=score_from_analysis(
                    analysis,
                    "ats_score",
                    "ats_report",
                    (
                        "score",
                        "ats_score",
                        "overall_score",
                    ),
                ),
                tailoring_score=score_from_analysis(
                    analysis,
                    "tailoring_score",
                    "tailoring_report",
                    (
                        "tailoring_score",
                        "score",
                        "readiness_score",
                    ),
                ),
            )
        )

    return result


def calculate_trend(
    values: list[float],
) -> float:
    """
    Compara a média da metade mais recente com a metade inicial.
    Evita depender apenas do primeiro e do último registro.
    """

    usable = [
        value
        for value in values
        if value > 0
    ]

    if len(usable) < 2:
        return 0.0

    midpoint = max(
        1,
        len(usable) // 2,
    )

    first_group = usable[:midpoint]
    recent_group = usable[midpoint:]

    if not recent_group:
        recent_group = [
            usable[-1]
        ]

    return round(
        average(recent_group)
        - average(first_group),
        2,
    )


def classify_trend(
    career_fit_trend: float,
) -> str:
    if career_fit_trend >= 8:
        return "EVOLUÇÃO FORTE"

    if career_fit_trend >= 3:
        return "EVOLUÇÃO POSITIVA"

    if career_fit_trend <= -8:
        return "QUEDA RELEVANTE"

    if career_fit_trend <= -3:
        return "TENDÊNCIA NEGATIVA"

    return "ESTÁVEL"


# ============================================================
# REQUIREMENT INTELLIGENCE
# ============================================================


def extract_requirement_items(
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Procura requisitos estruturados no ATS e Career Fit.
    """

    ats_report = deserialize_if_needed(
        analysis.get(
            "ats_report",
            {},
        )
    )

    requirements = get_value(
        ats_report,
        "requirements",
        [],
    )

    if isinstance(
        requirements,
        list,
    ) and requirements:
        return [
            item
            for item in requirements
            if isinstance(item, dict)
        ]

    career_fit_report = deserialize_if_needed(
        analysis.get(
            "career_fit_report",
            {},
        )
    )

    matches = get_value(
        career_fit_report,
        "matches",
        [],
    )

    result = []

    if isinstance(matches, list):
        for item in matches:
            if isinstance(item, dict):
                result.append(item)
            else:
                skill = get_value(
                    item,
                    "skill",
                )

                if skill:
                    result.append(
                        {
                            "skill": skill,
                            "priority": get_value(
                                item,
                                "priority",
                                "",
                            ),
                            "status": get_value(
                                item,
                                "status",
                                "",
                            ),
                        }
                    )

    return result


def build_requirement_signals(
    analyses: list[Any],
) -> list[RequirementSignal]:
    normalized = [
        normalize_analysis(item)
        for item in analyses
    ]

    stats: dict[str, dict[str, int]] = {}

    for analysis in normalized:
        seen_in_analysis = set()

        for item in extract_requirement_items(
            analysis
        ):
            name = str(
                item.get(
                    "skill",
                    item.get(
                        "requirement",
                        "",
                    ),
                )
            ).strip()

            if not name:
                continue

            key = name.casefold()

            if key not in stats:
                stats[key] = {
                    "name": name,
                    "occurrences": 0,
                    "mandatory": 0,
                    "matched": 0,
                    "gaps": 0,
                }

            if key not in seen_in_analysis:
                stats[key][
                    "occurrences"
                ] += 1
                seen_in_analysis.add(
                    key
                )

            priority = str(
                item.get(
                    "priority",
                    "",
                )
            ).casefold()

            status = str(
                item.get(
                    "status",
                    "",
                )
            ).casefold()

            if (
                "obrig" in priority
                or "mandatory" in priority
                or "required" in priority
            ):
                stats[key][
                    "mandatory"
                ] += 1

            if (
                "atende" in status
                or "match" in status
                or "matched" in status
            ):
                stats[key][
                    "matched"
                ] += 1

            elif status:
                stats[key][
                    "gaps"
                ] += 1

    signals = []

    for values in stats.values():
        occurrences = values[
            "occurrences"
        ]

        matched = values[
            "matched"
        ]

        match_rate = (
            matched
            / occurrences
            * 100
            if occurrences
            else 0
        )

        signals.append(
            RequirementSignal(
                requirement=values[
                    "name"
                ],
                occurrences=occurrences,
                mandatory_occurrences=values[
                    "mandatory"
                ],
                matched_occurrences=matched,
                gap_occurrences=values[
                    "gaps"
                ],
                match_rate=round(
                    match_rate,
                    2,
                ),
            )
        )

    signals.sort(
        key=lambda item: (
            item.occurrences,
            item.mandatory_occurrences,
            item.gap_occurrences,
        ),
        reverse=True,
    )

    return signals


# ============================================================
# CAREER GAP ADAPTER
# ============================================================


def build_gap_compatible_analyses(
    analyses: list[Any],
) -> list[dict[str, Any]]:
    """
    Adapta histórico persistido para o Gap Intelligence Engine.
    """

    result = []

    for analysis in analyses:
        normalized = normalize_analysis(
            analysis
        )

        result.append(
            {
                "opportunity_id": normalized.get(
                    "opportunity_id"
                ),
                "career_fit_score": score_from_analysis(
                    normalized,
                    "career_fit_score",
                    "career_fit_report",
                    (
                        "score",
                        "career_fit_score",
                        "fit_score",
                    ),
                ),
                "ats_score": score_from_analysis(
                    normalized,
                    "ats_score",
                    "ats_report",
                    (
                        "score",
                        "ats_score",
                    ),
                ),
                "ats_report": normalized.get(
                    "ats_report",
                    {},
                ),
            }
        )

    return result


# ============================================================
# INSIGHTS
# ============================================================


def build_strength_signals(
    requirement_signals: list[RequirementSignal],
) -> list[str]:
    strong = [
        item
        for item in requirement_signals
        if (
            item.occurrences >= 2
            and item.match_rate >= 70
        )
    ]

    strong.sort(
        key=lambda item: (
            item.occurrences,
            item.match_rate,
        ),
        reverse=True,
    )

    return [
        item.requirement
        for item in strong[:5]
    ]


def build_risk_signals(
    requirement_signals: list[RequirementSignal],
) -> list[str]:
    risks = [
        item
        for item in requirement_signals
        if (
            item.occurrences >= 2
            and item.gap_occurrences
            > item.matched_occurrences
        )
    ]

    risks.sort(
        key=lambda item: (
            item.mandatory_occurrences,
            item.gap_occurrences,
            item.occurrences,
        ),
        reverse=True,
    )

    return [
        item.requirement
        for item in risks[:5]
    ]


def build_executive_insights(
    total_analyses: int,
    avg_fit: float,
    latest_fit: float,
    fit_trend: float,
    trend_label: str,
    development_priorities: list[str],
    strongest_signals: list[str],
    risk_signals: list[str],
) -> list[str]:
    insights = []

    if total_analyses < 3:
        insights.append(
            "O histórico ainda é pequeno; novas análises aumentarão "
            "a confiabilidade das tendências."
        )

    if trend_label in {
        "EVOLUÇÃO FORTE",
        "EVOLUÇÃO POSITIVA",
    }:
        insights.append(
            f"O Career Fit recente está em trajetória positiva "
            f"({fit_trend:+.1f} pontos em relação ao período inicial)."
        )

    elif trend_label in {
        "QUEDA RELEVANTE",
        "TENDÊNCIA NEGATIVA",
    }:
        insights.append(
            f"O Career Fit apresenta queda no histórico "
            f"({fit_trend:+.1f} pontos), indicando possível dispersão "
            "na seleção de oportunidades."
        )

    elif total_analyses >= 2:
        insights.append(
            "O Career Fit permanece relativamente estável ao longo "
            "das oportunidades analisadas."
        )

    if latest_fit >= avg_fit + 8:
        insights.append(
            "A oportunidade mais recente está significativamente acima "
            "da aderência média histórica."
        )

    elif (
        latest_fit > 0
        and latest_fit <= avg_fit - 8
    ):
        insights.append(
            "A oportunidade mais recente está abaixo da aderência média "
            "histórica e merece menor prioridade."
        )

    if strongest_signals:
        insights.append(
            "Competências com evidência recorrente: "
            + ", ".join(
                strongest_signals[:3]
            )
            + "."
        )

    if risk_signals:
        insights.append(
            "Gaps recorrentes que reduzem competitividade: "
            + ", ".join(
                risk_signals[:3]
            )
            + "."
        )

    if development_priorities:
        insights.append(
            "Prioridades de desenvolvimento sugeridas pelo histórico: "
            + ", ".join(
                development_priorities[:3]
            )
            + "."
        )

    return insights[:6]


def calculate_confidence(
    total_analyses: int,
) -> float:
    if total_analyses <= 0:
        return 0.0

    if total_analyses == 1:
        return 30.0

    if total_analyses == 2:
        return 45.0

    if total_analyses <= 4:
        return 60.0

    if total_analyses <= 7:
        return 75.0

    if total_analyses <= 12:
        return 88.0

    return 95.0


def build_summary(
    total_analyses: int,
    avg_fit: float,
    latest_fit: float,
    trend_label: str,
    development_priorities: list[str],
) -> str:
    if total_analyses == 0:
        return (
            "Ainda não há análises suficientes para construir "
            "Career Analytics longitudinal."
        )

    text = (
        f"O histórico contém {total_analyses} análise(s), "
        f"com Career Fit médio de {avg_fit:.1f}% e "
        f"último Career Fit de {latest_fit:.1f}%. "
        f"Tendência: {trend_label}."
    )

    if development_priorities:
        text += (
            " Principal prioridade de desenvolvimento: "
            f"{development_priorities[0]}."
        )

    return text


# ============================================================
# MAIN ENGINE
# ============================================================


def analyze_career_history(
    analyses: list[Any],
) -> CareerAnalyticsReport:
    """
    Gera Career Intelligence longitudinal a partir do histórico.

    Registros incompletos 0/0/0 permanecem persistidos para
    rastreabilidade, mas são excluídos dos indicadores longitudinais.
    """

    analyses = analyses or []

    registered_analyses = len(
        analyses
    )

    valid_analyses, excluded_analyses = (
        filter_valid_analyses(
            analyses
        )
    )

    trajectory = build_trajectory(
        valid_analyses
    )

    fit_values = [
        point.career_fit_score
        for point in trajectory
    ]

    ats_values = [
        point.ats_score
        for point in trajectory
    ]

    tailoring_values = [
        point.tailoring_score
        for point in trajectory
    ]

    valid_fit = [
        value
        for value in fit_values
        if value > 0
    ]

    valid_ats = [
        value
        for value in ats_values
        if value > 0
    ]

    valid_tailoring = [
        value
        for value in tailoring_values
        if value > 0
    ]

    avg_fit = average(
        valid_fit
    )

    avg_ats = average(
        valid_ats
    )

    avg_tailoring = average(
        valid_tailoring
    )

    best_fit = (
        max(valid_fit)
        if valid_fit
        else 0.0
    )

    latest_fit = (
        valid_fit[-1]
        if valid_fit
        else 0.0
    )

    fit_trend = calculate_trend(
        fit_values
    )

    ats_trend = calculate_trend(
        ats_values
    )

    tailoring_trend = calculate_trend(
        tailoring_values
    )

    trend_label = classify_trend(
        fit_trend
    )

    requirement_signals = (
        build_requirement_signals(
            valid_analyses
        )
    )

    gap_report = analyze_career_gaps(
        build_gap_compatible_analyses(
            valid_analyses
        )
    )

    recurrent_gaps = [
        item.to_dict()
        for item in gap_report.recurrent_gaps[:10]
    ]

    development_priorities = list(
        gap_report.development_priorities
    )

    strongest_signals = (
        build_strength_signals(
            requirement_signals
        )
    )

    risk_signals = (
        build_risk_signals(
            requirement_signals
        )
    )

    valid_count = len(
        valid_analyses
    )

    executive_insights = (
        build_executive_insights(
            total_analyses=valid_count,
            avg_fit=avg_fit,
            latest_fit=latest_fit,
            fit_trend=fit_trend,
            trend_label=trend_label,
            development_priorities=development_priorities,
            strongest_signals=strongest_signals,
            risk_signals=risk_signals,
        )
    )

    if excluded_analyses > 0:
        executive_insights.insert(
            0,
            (
                f"{valid_count} análise(s) válida(s) de "
                f"{registered_analyses} registrada(s); "
                f"{excluded_analyses} registro(s) incompleto(s) "
                "0/0/0 foram excluídos dos KPIs."
            ),
        )

    return CareerAnalyticsReport(
        total_analyses=valid_count,
        registered_analyses=registered_analyses,
        excluded_analyses=excluded_analyses,
        avg_career_fit=avg_fit,
        avg_ats_score=avg_ats,
        avg_tailoring_score=avg_tailoring,
        best_career_fit=round(
            best_fit,
            2,
        ),
        latest_career_fit=round(
            latest_fit,
            2,
        ),
        career_fit_trend=fit_trend,
        ats_trend=ats_trend,
        tailoring_trend=tailoring_trend,
        trend_label=trend_label,
        confidence_score=calculate_confidence(
            valid_count
        ),
        trajectory=trajectory,
        top_requirements=requirement_signals[:10],
        recurrent_gaps=recurrent_gaps,
        development_priorities=development_priorities,
        strongest_signals=strongest_signals,
        risk_signals=risk_signals,
        executive_insights=executive_insights,
        summary=build_summary(
            total_analyses=valid_count,
            avg_fit=avg_fit,
            latest_fit=latest_fit,
            trend_label=trend_label,
            development_priorities=development_priorities,
        ),
    )

def build_analytics_summary(
    report: CareerAnalyticsReport,
) -> dict[str, Any]:
    return report.to_dict()


# ============================================================
# SELF TEST
# ============================================================


def run_self_test() -> dict[str, Any]:
    analyses = [
        {
            "opportunity_id": "opp_technical",
            "job_title": "Registro Técnico",
            "company": "CareerCompass Test Company",
            "created_at": "2026-07-30T10:00:00",
            "career_fit_score": 0,
            "ats_score": 0,
            "tailoring_score": 0,
            "ats_report": {},
        },
        {
            "opportunity_id": "opp_1",
            "job_title": "Gerente de Projetos",
            "company": "Empresa A",
            "created_at": "2026-08-01T10:00:00",
            "career_fit_score": 58,
            "ats_score": 55,
            "tailoring_score": 60,
            "ats_report": {
                "mandatory_gaps": [
                    "Gestão de Riscos",
                ],
                "preferred_gaps": [
                    "SQL",
                ],
                "requirements": [
                    {
                        "skill": "Liderança",
                        "priority": "Obrigatório",
                        "status": "Atende",
                    },
                    {
                        "skill": "Gestão de Riscos",
                        "priority": "Obrigatório",
                        "status": "Não identificado no perfil",
                    },
                ],
            },
        },
        {
            "opportunity_id": "opp_2",
            "job_title": "Gerente de Operações",
            "company": "Empresa B",
            "created_at": "2026-08-10T10:00:00",
            "career_fit_score": 66,
            "ats_score": 63,
            "tailoring_score": 69,
            "ats_report": json.dumps(
                {
                    "mandatory_gaps": [
                        "Gestão de Riscos",
                    ],
                    "preferred_gaps": [],
                    "requirements": [
                        {
                            "skill": "Liderança",
                            "priority": "Obrigatório",
                            "status": "Atende",
                        },
                        {
                            "skill": "Gestão de Riscos",
                            "priority": "Obrigatório",
                            "status": "Não identificado no perfil",
                        },
                    ],
                },
                ensure_ascii=False,
            ),
        },
        {
            "opportunity_id": "opp_3",
            "job_title": "Head de Operações",
            "company": "Empresa C",
            "created_at": "2026-08-20T10:00:00",
            "career_fit_score": 74,
            "ats_score": 71,
            "tailoring_score": 78,
            "ats_report": {
                "mandatory_gaps": [],
                "preferred_gaps": [
                    "SQL",
                ],
                "requirements": [
                    {
                        "skill": "Liderança",
                        "priority": "Obrigatório",
                        "status": "Atende",
                    },
                    {
                        "skill": "Gestão de Riscos",
                        "priority": "Obrigatório",
                        "status": "Atende",
                    },
                ],
            },
        },
        {
            "opportunity_id": "opp_4",
            "job_title": "Diretor de Operações",
            "company": "Empresa D",
            "created_at": "2026-08-30T10:00:00",
            "career_fit_score": 82,
            "ats_score": 79,
            "tailoring_score": 84,
            "ats_report": {
                "mandatory_gaps": [],
                "preferred_gaps": [],
                "requirements": [
                    {
                        "skill": "Liderança",
                        "priority": "Obrigatório",
                        "status": "Atende",
                    },
                    {
                        "skill": "Gestão de Riscos",
                        "priority": "Obrigatório",
                        "status": "Atende",
                    },
                ],
            },
        },
    ]

    report = analyze_career_history(
        analyses
    )

    assert report.registered_analyses == 5
    assert report.total_analyses == 4
    assert report.excluded_analyses == 1
    assert all(
        (
            point.career_fit_score,
            point.ats_score,
            point.tailoring_score,
        ) != (0.0, 0.0, 0.0)
        for point in report.trajectory
    )

    return {
        "status": "ok",
        "report": build_analytics_summary(
            report
        ),
    }


if __name__ == "__main__":
    result = run_self_test()

    print()
    print(
        "CareerCompass AI — Career Analytics Engine"
    )
    print(
        "------------------------------------------"
    )
    print(
        f"Status: {result['status']}"
    )

    report = result["report"]

    print(
        f"Análises: {report['total_analyses']}"
    )
    print(
        f"Career Fit médio: {report['avg_career_fit']}%"
    )
    print(
        f"Último Career Fit: {report['latest_career_fit']}%"
    )
    print(
        f"Melhor Career Fit: {report['best_career_fit']}%"
    )
    print(
        f"Tendência: {report['trend_label']}"
    )
    print(
        f"Variação Career Fit: {report['career_fit_trend']:+.2f}"
    )
    print(
        f"Confiança: {report['confidence_score']}%"
    )

    print()
    print(
        "Top Requirements"
    )
    print(
        "----------------"
    )

    for item in report[
        "top_requirements"
    ][:5]:
        print(
            f"- {item['requirement']}: "
            f"{item['occurrences']} ocorrência(s), "
            f"match {item['match_rate']}%"
        )

    print()
    print(
        "Development Priorities"
    )
    print(
        "----------------------"
    )

    for item in report[
        "development_priorities"
    ][:5]:
        print(
            f"- {item}"
        )

    print()
    print(
        "Executive Insights"
    )
    print(
        "------------------"
    )

    for item in report[
        "executive_insights"
    ]:
        print(
            f"- {item}"
        )
