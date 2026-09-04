"""
CareerCompass AI
Career Gap Intelligence Engine

Analisa o histórico de oportunidades e análises para identificar
gaps profissionais recorrentes e prioridades de desenvolvimento.

Objetivos:
- identificar gaps que aparecem repetidamente;
- medir frequência e recorrência;
- distinguir gaps obrigatórios de diferenciais;
- estimar impacto sobre ATS e Decision Score;
- produzir prioridades de desenvolvimento;
- preparar dados para Career Analytics e Executive Dashboard.

A implementação é determinística, explicável e baseada
exclusivamente nos dados persistidos.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any


# ============================================================
# DATA MODEL
# ============================================================


@dataclass
class GapInsight:
    gap: str

    total_occurrences: int
    mandatory_occurrences: int
    preferred_occurrences: int

    opportunities_count: int
    occurrence_rate: float

    avg_ats_score: float
    avg_career_fit_score: float

    priority: str
    impact_score: float

    recommendation: str

    evidence_type: str = "Gap recorrente"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CareerGapReport:
    total_analyses: int
    total_opportunities: int

    recurrent_gaps: list[GapInsight] = field(default_factory=list)

    top_mandatory_gaps: list[str] = field(default_factory=list)
    top_preferred_gaps: list[str] = field(default_factory=list)

    development_priorities: list[str] = field(default_factory=list)

    summary: str = ""

    confidence_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# CONFIGURAÇÃO
# ============================================================


PRIORITY_THRESHOLDS = {
    "CRITICAL": 75,
    "HIGH": 55,
    "MEDIUM": 30,
}


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


def normalize_string_list(
    values: Any,
) -> list[str]:
    if values is None:
        return []

    if isinstance(values, str):
        value = values.strip()
        return [value] if value else []

    try:
        iterable = list(values)
    except TypeError:
        return []

    result = []

    for item in iterable:
        text = str(item).strip()

        if text and text not in result:
            result.append(text)

    return result


def normalize_score(
    value: Any,
) -> float:
    if value is None:
        return 0.0

    if isinstance(value, bool):
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


# ============================================================
# GAP EXTRACTION
# ============================================================


def extract_mandatory_gaps(
    analysis: Any,
) -> list[str]:
    """
    Extrai gaps obrigatórios do relatório ATS persistido.
    """

    ats_report = get_value(
        analysis,
        "ats_report",
        {},
    )

    return normalize_string_list(
        get_value(
            ats_report,
            "mandatory_gaps",
            [],
        )
    )


def extract_preferred_gaps(
    analysis: Any,
) -> list[str]:
    """
    Extrai gaps diferenciais do relatório ATS persistido.
    """

    ats_report = get_value(
        analysis,
        "ats_report",
        {},
    )

    return normalize_string_list(
        get_value(
            ats_report,
            "preferred_gaps",
            [],
        )
    )


def extract_ats_score(
    analysis: Any,
) -> float:
    return normalize_score(
        get_value(
            analysis,
            "ats_score",
            0,
        )
    )


def extract_career_fit_score(
    analysis: Any,
) -> float:
    return normalize_score(
        get_value(
            analysis,
            "career_fit_score",
            0,
        )
    )


# ============================================================
# AGGREGATION
# ============================================================


def aggregate_gap_data(
    analyses: list[Any],
) -> dict[str, dict[str, Any]]:
    """
    Consolida informações por gap.
    """

    stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "mandatory_occurrences": 0,
            "preferred_occurrences": 0,
            "opportunities": set(),
            "ats_scores": [],
            "career_fit_scores": [],
        }
    )

    for index, analysis in enumerate(analyses):
        opportunity_id = (
            get_value(
                analysis,
                "opportunity_id",
            )
            or f"analysis_{index}"
        )

        mandatory_gaps = extract_mandatory_gaps(
            analysis
        )

        preferred_gaps = extract_preferred_gaps(
            analysis
        )

        ats_score = extract_ats_score(
            analysis
        )

        career_fit_score = (
            extract_career_fit_score(
                analysis
            )
        )

        all_gaps = set(
            mandatory_gaps
            + preferred_gaps
        )

        for gap in mandatory_gaps:
            stats[gap][
                "mandatory_occurrences"
            ] += 1

        for gap in preferred_gaps:
            stats[gap][
                "preferred_occurrences"
            ] += 1

        for gap in all_gaps:
            stats[gap][
                "opportunities"
            ].add(opportunity_id)

            stats[gap][
                "ats_scores"
            ].append(ats_score)

            stats[gap][
                "career_fit_scores"
            ].append(
                career_fit_score
            )

    return stats


# ============================================================
# SCORING
# ============================================================


def calculate_gap_impact_score(
    mandatory_occurrences: int,
    preferred_occurrences: int,
    occurrence_rate: float,
    avg_ats_score: float,
    avg_career_fit_score: float,
) -> float:
    """
    Calcula o impacto do gap.

    Fatores:
    - recorrência;
    - peso de requisitos obrigatórios;
    - impacto potencial sobre ATS;
    - impacto potencial sobre Career Fit.
    """

    mandatory_component = min(
        mandatory_occurrences * 12,
        36,
    )

    preferred_component = min(
        preferred_occurrences * 5,
        15,
    )

    recurrence_component = (
        occurrence_rate * 0.30
    )

    ats_penalty = (
        max(
            0,
            70 - avg_ats_score,
        )
        * 0.15
    )

    fit_penalty = (
        max(
            0,
            70 - avg_career_fit_score,
        )
        * 0.10
    )

    score = (
        mandatory_component
        + preferred_component
        + recurrence_component
        + ats_penalty
        + fit_penalty
    )

    return round(
        min(
            score,
            100,
        ),
        2,
    )


def classify_priority(
    impact_score: float,
) -> str:
    if (
        impact_score
        >= PRIORITY_THRESHOLDS[
            "CRITICAL"
        ]
    ):
        return "CRITICAL"

    if (
        impact_score
        >= PRIORITY_THRESHOLDS[
            "HIGH"
        ]
    ):
        return "HIGH"

    if (
        impact_score
        >= PRIORITY_THRESHOLDS[
            "MEDIUM"
        ]
    ):
        return "MEDIUM"

    return "LOW"


# ============================================================
# RECOMMENDATION
# ============================================================


def build_gap_recommendation(
    gap: str,
    priority: str,
    mandatory_occurrences: int,
    occurrence_rate: float,
) -> str:
    """
    Produz recomendação acionável.
    """

    if priority == "CRITICAL":
        return (
            f"{gap} aparece de forma recorrente e com forte peso "
            "como requisito obrigatório. Avalie se existe experiência "
            "real ainda não evidenciada no currículo; se existir, "
            "reposicione essa evidência imediatamente. Caso contrário, "
            "trate como prioridade de desenvolvimento."
        )

    if priority == "HIGH":
        return (
            f"{gap} deve ser tratado como prioridade alta. "
            f"O gap apareceu em {mandatory_occurrences} requisito(s) "
            f"obrigatório(s) e em {occurrence_rate:.1f}% "
            "das oportunidades analisadas."
        )

    if priority == "MEDIUM":
        return (
            f"{gap} apresenta recorrência relevante. "
            "Vale fortalecer evidências profissionais ou desenvolver "
            "a competência antes de priorizar vagas que a exijam."
        )

    return (
        f"{gap} aparece pontualmente no histórico. "
        "Monitore a recorrência antes de investir esforço significativo."
    )


# ============================================================
# REPORT BUILDING
# ============================================================


def build_gap_insights(
    analyses: list[Any],
) -> list[GapInsight]:
    """
    Constrói insights ordenados por impacto.
    """

    if not analyses:
        return []

    stats = aggregate_gap_data(
        analyses
    )

    total_opportunities = len(
        {
            get_value(
                analysis,
                "opportunity_id",
                f"analysis_{index}",
            )
            for index, analysis
            in enumerate(analyses)
        }
    )

    insights = []

    for gap, values in stats.items():

        mandatory_occurrences = (
            values[
                "mandatory_occurrences"
            ]
        )

        preferred_occurrences = (
            values[
                "preferred_occurrences"
            ]
        )

        opportunities_count = len(
            values["opportunities"]
        )

        occurrence_rate = (
            (
                opportunities_count
                / total_opportunities
            )
            * 100
            if total_opportunities
            else 0
        )

        ats_scores = (
            values[
                "ats_scores"
            ]
        )

        career_fit_scores = (
            values[
                "career_fit_scores"
            ]
        )

        avg_ats_score = (
            sum(ats_scores)
            / len(ats_scores)
            if ats_scores
            else 0
        )

        avg_career_fit_score = (
            sum(career_fit_scores)
            / len(career_fit_scores)
            if career_fit_scores
            else 0
        )

        impact_score = (
            calculate_gap_impact_score(
                mandatory_occurrences=mandatory_occurrences,
                preferred_occurrences=preferred_occurrences,
                occurrence_rate=occurrence_rate,
                avg_ats_score=avg_ats_score,
                avg_career_fit_score=avg_career_fit_score,
            )
        )

        priority = classify_priority(
            impact_score
        )

        recommendation = (
            build_gap_recommendation(
                gap=gap,
                priority=priority,
                mandatory_occurrences=mandatory_occurrences,
                occurrence_rate=occurrence_rate,
            )
        )

        insights.append(
            GapInsight(
                gap=gap,
                total_occurrences=(
                    mandatory_occurrences
                    + preferred_occurrences
                ),
                mandatory_occurrences=mandatory_occurrences,
                preferred_occurrences=preferred_occurrences,
                opportunities_count=opportunities_count,
                occurrence_rate=round(
                    occurrence_rate,
                    2,
                ),
                avg_ats_score=round(
                    avg_ats_score,
                    2,
                ),
                avg_career_fit_score=round(
                    avg_career_fit_score,
                    2,
                ),
                priority=priority,
                impact_score=impact_score,
                recommendation=recommendation,
            )
        )

    insights.sort(
        key=lambda item: (
            item.impact_score,
            item.mandatory_occurrences,
            item.total_occurrences,
        ),
        reverse=True,
    )

    return insights


# ============================================================
# SUMMARY
# ============================================================


def build_summary(
    insights: list[GapInsight],
    total_analyses: int,
) -> str:
    if not insights:
        return (
            "Ainda não há histórico suficiente "
            "para identificar gaps recorrentes."
        )

    top = insights[0]

    return (
        f"Foram identificados {len(insights)} gap(s) "
        f"em {total_analyses} análise(s). "
        f"O gap de maior impacto é '{top.gap}', "
        f"classificado como {top.priority}, "
        f"com recorrência de {top.occurrence_rate}%."
    )


def calculate_report_confidence(
    total_analyses: int,
) -> float:
    """
    A confiança aumenta com o histórico disponível.
    """

    if total_analyses <= 0:
        return 0.0

    if total_analyses == 1:
        return 35.0

    if total_analyses == 2:
        return 50.0

    if total_analyses <= 4:
        return 65.0

    if total_analyses <= 7:
        return 80.0

    return 95.0


# ============================================================
# MAIN ENGINE
# ============================================================


def analyze_career_gaps(
    analyses: list[Any],
) -> CareerGapReport:
    """
    Analisa o histórico de Career Intelligence.
    """

    analyses = analyses or []

    insights = build_gap_insights(
        analyses
    )

    total_opportunities = len(
        {
            get_value(
                analysis,
                "opportunity_id",
                f"analysis_{index}",
            )
            for index, analysis
            in enumerate(analyses)
        }
    )

    mandatory_counter = Counter()
    preferred_counter = Counter()

    for analysis in analyses:
        mandatory_counter.update(
            extract_mandatory_gaps(
                analysis
            )
        )

        preferred_counter.update(
            extract_preferred_gaps(
                analysis
            )
        )

    top_mandatory = [
        item
        for item, _
        in mandatory_counter.most_common(5)
    ]

    top_preferred = [
        item
        for item, _
        in preferred_counter.most_common(5)
    ]

    development_priorities = [
        insight.gap
        for insight in insights
        if insight.priority
        in {
            "CRITICAL",
            "HIGH",
        }
    ][:5]

    return CareerGapReport(
        total_analyses=len(analyses),
        total_opportunities=total_opportunities,
        recurrent_gaps=insights,
        top_mandatory_gaps=top_mandatory,
        top_preferred_gaps=top_preferred,
        development_priorities=development_priorities,
        summary=build_summary(
            insights,
            len(analyses),
        ),
        confidence_score=(
            calculate_report_confidence(
                len(analyses)
            )
        ),
    )


# ============================================================
# UI SUMMARY
# ============================================================


def build_gap_summary(
    report: CareerGapReport,
) -> dict[str, Any]:
    return report.to_dict()


# ============================================================
# SELF TEST
# ============================================================


def run_self_test() -> dict[str, Any]:
    """
    Simula quatro oportunidades para validar recorrência.
    """

    analyses = [
        {
            "opportunity_id": "opp_1",
            "career_fit_score": 68,
            "ats_score": 61,
            "ats_report": {
                "mandatory_gaps": [
                    "Gestão de Riscos",
                    "Planejamento Estratégico",
                ],
                "preferred_gaps": [
                    "SQL",
                ],
            },
        },
        {
            "opportunity_id": "opp_2",
            "career_fit_score": 72,
            "ats_score": 66,
            "ats_report": {
                "mandatory_gaps": [
                    "Gestão de Riscos",
                ],
                "preferred_gaps": [
                    "SQL",
                    "Inglês",
                ],
            },
        },
        {
            "opportunity_id": "opp_3",
            "career_fit_score": 59,
            "ats_score": 54,
            "ats_report": {
                "mandatory_gaps": [
                    "Gestão de Riscos",
                    "Planejamento Estratégico",
                ],
                "preferred_gaps": [
                    "Python",
                ],
            },
        },
        {
            "opportunity_id": "opp_4",
            "career_fit_score": 74,
            "ats_score": 69,
            "ats_report": {
                "mandatory_gaps": [
                    "Negociação",
                ],
                "preferred_gaps": [
                    "SQL",
                ],
            },
        },
    ]

    report = analyze_career_gaps(
        analyses
    )

    return {
        "status": "ok",
        "report": (
            build_gap_summary(
                report
            )
        ),
    }


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================


if __name__ == "__main__":
    result = run_self_test()

    print()
    print(
        "CareerCompass AI — "
        "Career Gap Intelligence Engine"
    )
    print(
        "----------------------------------------"
    )

    print(
        f"Status: {result['status']}"
    )

    report = result["report"]

    print(
        f"Análises: "
        f"{report['total_analyses']}"
    )

    print(
        f"Oportunidades: "
        f"{report['total_opportunities']}"
    )

    print(
        f"Confiança: "
        f"{report['confidence_score']}%"
    )

    print()
    print(
        report["summary"]
    )

    print()
    print(
        "Top Recurrent Gaps"
    )
    print(
        "------------------"
    )

    for index, item in enumerate(
        report["recurrent_gaps"][:5],
        start=1,
    ):
        print(
            f"{index}. {item['gap']}"
        )

        print(
            f"   Ocorrência: "
            f"{item['opportunities_count']} "
            f"oportunidade(s)"
        )

        print(
            f"   Recorrência: "
            f"{item['occurrence_rate']}%"
        )

        print(
            f"   Obrigatório: "
            f"{item['mandatory_occurrences']}"
        )

        print(
            f"   Diferencial: "
            f"{item['preferred_occurrences']}"
        )

        print(
            f"   Impact Score: "
            f"{item['impact_score']}"
        )

        print(
            f"   Prioridade: "
            f"{item['priority']}"
        )

        print()
