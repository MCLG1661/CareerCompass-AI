"""
CareerCompass AI
Executive Intelligence Engine

Consolida Career Analytics e Application Intelligence para gerar
uma visão executiva da trajetória profissional.

Objetivos:
- criar um Career Intelligence Score longitudinal;
- resumir trajetória, competitividade e pipeline;
- detectar momentum;
- destacar riscos e prioridades;
- gerar Next Best Action executivo;
- preparar dados para o Executive Dashboard.

O engine é determinístico e usa somente dados produzidos pelos
engines já validados.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from application_intelligence_engine import analyze_application_history
from career_analytics_engine import analyze_career_history


# ============================================================
# DATA MODEL
# ============================================================


@dataclass
class ExecutiveIntelligenceReport:
    career_intelligence_score: float
    confidence_score: float
    data_quality_score: float

    registered_analyses: int
    valid_analyses: int
    excluded_analyses: int

    momentum: str
    career_fit_average: float
    ats_average: float

    applications: int
    interviews: int
    offers: int

    interview_rate: float
    offer_rate: float

    top_strengths: list[str] = field(default_factory=list)
    top_risks: list[str] = field(default_factory=list)
    development_priorities: list[str] = field(default_factory=list)

    executive_insights: list[str] = field(default_factory=list)

    next_best_action: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# HELPERS
# ============================================================


def weighted_score(
    components: list[tuple[float, float, bool]],
) -> float:
    """
    Repondera somente os componentes disponíveis.
    Cada item: (valor, peso, disponível).
    """

    available = [
        (value, weight)
        for value, weight, is_available in components
        if is_available
    ]

    if not available:
        return 0.0

    weight_sum = sum(
        weight
        for _, weight in available
    )

    if weight_sum <= 0:
        return 0.0

    score = sum(
        value * weight
        for value, weight in available
    ) / weight_sum

    return round(
        max(
            0.0,
            min(score, 100.0),
        ),
        2,
    )


def classify_momentum(
    fit_trend: float,
    interview_rate: float,
    offer_rate: float,
    total_applications: int,
) -> str:
    positive_signals = 0
    negative_signals = 0

    if fit_trend >= 5:
        positive_signals += 1
    elif fit_trend <= -5:
        negative_signals += 1

    if total_applications >= 3:
        if interview_rate >= 40:
            positive_signals += 1
        elif interview_rate < 20:
            negative_signals += 1

    if offer_rate >= 30:
        positive_signals += 1

    if positive_signals >= 2:
        return "POSITIVO"

    if negative_signals >= 2:
        return "NEGATIVO"

    return "ESTÁVEL"


def calculate_confidence(
    career_report: Any,
    application_report: Any,
) -> tuple[float, float]:
    """
    Calcula confiança executiva usando duas dimensões:

    1. maturidade da evidência:
       - quantidade de análises válidas;
       - quantidade de candidaturas registradas.

    2. qualidade do histórico:
       - proporção entre análises válidas e análises registradas.

    Registros incompletos não destroem a confiança acumulada, mas
    reduzem proporcionalmente o indicador. Isso evita que volume
    técnico/testes aumentem artificialmente a confiança do sistema.

    Retorna:
        (confidence_score, data_quality_score)
    """

    valid_analyses = int(
        getattr(
            career_report,
            "total_analyses",
            0,
        )
        or 0
    )

    registered_analyses = int(
        getattr(
            career_report,
            "registered_analyses",
            valid_analyses,
        )
        or valid_analyses
    )

    applications_count = int(
        getattr(
            application_report,
            "total_applications",
            0,
        )
        or 0
    )

    maturity_score = 0.0

    if valid_analyses >= 1:
        maturity_score += 20

    if valid_analyses >= 3:
        maturity_score += 20

    if valid_analyses >= 6:
        maturity_score += 15

    if applications_count >= 1:
        maturity_score += 15

    if applications_count >= 3:
        maturity_score += 15

    if applications_count >= 6:
        maturity_score += 15

    maturity_score = min(
        maturity_score,
        100.0,
    )

    if registered_analyses > 0:
        valid_ratio = (
            valid_analyses
            / registered_analyses
        )
    else:
        valid_ratio = 0.0

    valid_ratio = max(
        0.0,
        min(
            valid_ratio,
            1.0,
        ),
    )

    data_quality_score = round(
        valid_ratio * 100,
        1,
    )

    # A qualidade modula a confiança sem apagar toda a maturidade
    # já construída. Com histórico 100% válido, não há penalização.
    quality_factor = (
        0.65
        + 0.35 * valid_ratio
    )

    confidence_score = round(
        maturity_score
        * quality_factor,
        1,
    )

    return (
        min(confidence_score, 100.0),
        data_quality_score,
    )


# ============================================================
# SCORE
# ============================================================


def calculate_career_intelligence_score(
    career_report: Any,
    application_report: Any,
) -> float:
    avg_fit = float(
        career_report.avg_career_fit
    )

    avg_ats = float(
        career_report.avg_ats_score
    )

    interview_rate = float(
        application_report.interview_rate
    )

    offer_rate = float(
        application_report.offer_rate
    )

    return weighted_score(
        [
            (
                avg_fit,
                0.40,
                career_report.total_analyses > 0,
            ),
            (
                avg_ats,
                0.25,
                career_report.total_analyses > 0,
            ),
            (
                interview_rate,
                0.20,
                application_report.applied > 0,
            ),
            (
                offer_rate,
                0.15,
                application_report.interviews > 0,
            ),
        ]
    )


# ============================================================
# INSIGHTS
# ============================================================


def merge_unique(
    *collections: list[str],
    limit: int = 6,
) -> list[str]:
    result = []

    for collection in collections:
        for item in collection:
            text = str(item).strip()

            if text and text not in result:
                result.append(text)

            if len(result) >= limit:
                return result

    return result


def build_next_best_action(
    career_report: Any,
    application_report: Any,
) -> str:
    if career_report.total_analyses == 0:
        return (
            "Analisar novas oportunidades para construir uma base "
            "de Career Intelligence."
        )

    if application_report.total_applications == 0:
        return (
            "Transformar as melhores análises em candidaturas e "
            "registrar seus status no pipeline."
        )

    if application_report.bottleneck != "SEM GARGALO CRÍTICO":
        return application_report.next_best_action

    if career_report.development_priorities:
        return (
            "Priorizar oportunidades de alta aderência e fortalecer "
            f"a competência '{career_report.development_priorities[0]}'."
        )

    if career_report.career_fit_trend < -5:
        return (
            "Revisar os critérios de seleção de vagas e concentrar "
            "esforço em oportunidades mais aderentes."
        )

    return (
        "Manter o pipeline atualizado e priorizar oportunidades com "
        "Career Fit e Decision Score mais altos."
    )


def build_summary(
    score: float,
    momentum: str,
    career_report: Any,
    application_report: Any,
) -> str:
    return (
        f"Career Intelligence Score de {score:.1f}/100, "
        f"momentum {momentum}. "
        f"Career Fit médio de {career_report.avg_career_fit:.1f}% "
        f"em {career_report.total_analyses} análise(s), com "
        f"{application_report.interviews} entrevista(s) e "
        f"{application_report.offers} oferta(s) no pipeline."
    )


# ============================================================
# MAIN ENGINE
# ============================================================


def build_executive_intelligence(
    analyses: list[Any],
    applications: list[Any],
) -> ExecutiveIntelligenceReport:
    career_report = analyze_career_history(
        analyses or []
    )

    application_report = analyze_application_history(
        applications=applications or [],
        analyses=analyses or [],
    )

    score = calculate_career_intelligence_score(
        career_report=career_report,
        application_report=application_report,
    )

    momentum = classify_momentum(
        fit_trend=career_report.career_fit_trend,
        interview_rate=application_report.interview_rate,
        offer_rate=application_report.offer_rate,
        total_applications=application_report.total_applications,
    )

    confidence, data_quality = calculate_confidence(
        career_report=career_report,
        application_report=application_report,
    )

    strengths = merge_unique(
        career_report.strongest_signals,
        application_report.strengths,
        limit=5,
    )

    risks = merge_unique(
        career_report.risk_signals,
        application_report.risks,
        limit=5,
    )

    insights = merge_unique(
        career_report.executive_insights,
        application_report.executive_insights,
        limit=6,
    )

    next_best_action = build_next_best_action(
        career_report=career_report,
        application_report=application_report,
    )

    return ExecutiveIntelligenceReport(
        career_intelligence_score=score,
        confidence_score=confidence,
        data_quality_score=data_quality,
        registered_analyses=int(
            getattr(
                career_report,
                "registered_analyses",
                career_report.total_analyses,
            )
        ),
        valid_analyses=career_report.total_analyses,
        excluded_analyses=int(
            getattr(
                career_report,
                "excluded_analyses",
                0,
            )
        ),
        momentum=momentum,
        career_fit_average=career_report.avg_career_fit,
        ats_average=career_report.avg_ats_score,
        applications=application_report.total_applications,
        interviews=application_report.interviews,
        offers=application_report.offers,
        interview_rate=application_report.interview_rate,
        offer_rate=application_report.offer_rate,
        top_strengths=strengths,
        top_risks=risks,
        development_priorities=list(
            career_report.development_priorities
        )[:5],
        executive_insights=insights,
        next_best_action=next_best_action,
        summary=build_summary(
            score=score,
            momentum=momentum,
            career_report=career_report,
            application_report=application_report,
        ),
    )


def build_executive_summary(
    report: ExecutiveIntelligenceReport,
) -> dict[str, Any]:
    return report.to_dict()


# ============================================================
# SELF TEST
# ============================================================


def run_self_test() -> dict[str, Any]:
    analyses = [
        {
            "id": "ana_technical",
            "profile_id": "prf_exec",
            "opportunity_id": "opp_technical",
            "created_at": "2026-07-30T10:00:00",
            "career_fit_score": 0,
            "ats_score": 0,
            "tailoring_score": 0,
            "ats_report": {},
        },
        {
            "id": "ana_1",
            "profile_id": "prf_exec",
            "opportunity_id": "opp_1",
            "created_at": "2026-08-01T10:00:00",
            "career_fit_score": 60,
            "ats_score": 58,
            "tailoring_score": 62,
            "ats_report": {
                "mandatory_gaps": [
                    "Gestão de Riscos"
                ],
                "preferred_gaps": [],
            },
        },
        {
            "id": "ana_2",
            "profile_id": "prf_exec",
            "opportunity_id": "opp_2",
            "created_at": "2026-08-15T10:00:00",
            "career_fit_score": 72,
            "ats_score": 68,
            "tailoring_score": 74,
            "ats_report": {
                "mandatory_gaps": [
                    "Gestão de Riscos"
                ],
                "preferred_gaps": [],
            },
        },
        {
            "id": "ana_3",
            "profile_id": "prf_exec",
            "opportunity_id": "opp_3",
            "created_at": "2026-08-30T10:00:00",
            "career_fit_score": 82,
            "ats_score": 78,
            "tailoring_score": 84,
            "ats_report": {
                "mandatory_gaps": [],
                "preferred_gaps": [],
            },
        },
    ]

    applications = [
        {
            "id": "app_1",
            "analysis_id": "ana_1",
            "status": "rejected",
        },
        {
            "id": "app_2",
            "analysis_id": "ana_2",
            "status": "interview",
        },
        {
            "id": "app_3",
            "analysis_id": "ana_3",
            "status": "offer",
        },
    ]

    report = build_executive_intelligence(
        analyses=analyses,
        applications=applications,
    )

    assert report.registered_analyses == 4
    assert report.valid_analyses == 3
    assert report.excluded_analyses == 1
    assert report.data_quality_score == 75.0
    assert report.confidence_score < 70.0

    return {
        "status": "ok",
        "report": build_executive_summary(
            report
        ),
    }


if __name__ == "__main__":
    result = run_self_test()

    print()
    print(
        "CareerCompass AI — Executive Intelligence Engine"
    )
    print(
        "------------------------------------------------"
    )
    print(
        f"Status: {result['status']}"
    )

    report = result["report"]

    print(
        f"Career Intelligence Score: "
        f"{report['career_intelligence_score']}"
    )
    print(
        f"Confidence: "
        f"{report['confidence_score']}%"
    )
    print(
        f"Data Quality: "
        f"{report['data_quality_score']}%"
    )
    print(
        f"Análises válidas/registradas: "
        f"{report['valid_analyses']}/"
        f"{report['registered_analyses']}"
    )
    print(
        f"Momentum: "
        f"{report['momentum']}"
    )
    print(
        f"Career Fit médio: "
        f"{report['career_fit_average']}%"
    )
    print(
        f"ATS médio: "
        f"{report['ats_average']}%"
    )
    print(
        f"Entrevistas: "
        f"{report['interviews']}"
    )
    print(
        f"Ofertas: "
        f"{report['offers']}"
    )

    print()
    print(
        "Next Best Action"
    )
    print(
        "----------------"
    )
    print(
        report["next_best_action"]
    )

    print()
    print(
        "Summary"
    )
    print(
        "-------"
    )
    print(
        report["summary"]
    )
