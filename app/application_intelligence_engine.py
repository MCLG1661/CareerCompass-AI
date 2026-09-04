"""
CareerCompass AI
Application Intelligence Engine

Analisa o histórico de candidaturas para gerar inteligência sobre
pipeline, conversão, tempo em etapas e desempenho por perfil/CV.

Objetivos:
- medir conversões planned -> applied -> interview -> offer;
- identificar gargalos do pipeline;
- medir taxa de rejeição e desistência;
- comparar desempenho por profile_id quando disponível;
- produzir sinais executivos e próximos focos;
- alimentar o Executive Dashboard.

O engine é determinístico e usa apenas dados persistidos.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


# ============================================================
# DATA MODELS
# ============================================================


@dataclass
class ProfilePerformance:
    profile_id: str
    total_applications: int
    applied: int
    interviews: int
    offers: int
    rejected: int
    interview_rate: float
    offer_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ApplicationIntelligenceReport:
    total_applications: int

    planned: int
    applied: int
    interviews: int
    offers: int
    rejected: int
    withdrawn: int

    application_rate: float
    interview_rate: float
    offer_rate: float
    rejection_rate: float

    dominant_status: str
    bottleneck: str
    confidence_score: float

    status_distribution: dict[str, int] = field(default_factory=dict)
    profile_performance: list[ProfilePerformance] = field(default_factory=list)

    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    executive_insights: list[str] = field(default_factory=list)

    next_best_action: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# HELPERS
# ============================================================


VALID_STATUSES = {
    "planned",
    "applied",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
}


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


def normalize_status(
    value: Any,
) -> str:
    status = str(
        value or ""
    ).strip().lower()

    return (
        status
        if status in VALID_STATUSES
        else "planned"
    )


def normalize_application(
    application: Any,
) -> dict[str, Any]:
    if isinstance(application, dict):
        return dict(application)

    result = {}

    for key in (
        "id",
        "user_id",
        "opportunity_id",
        "analysis_id",
        "profile_id",
        "status",
        "applied_at",
        "interview_at",
        "outcome",
        "notes",
        "created_at",
        "updated_at",
        "job_title",
        "company",
    ):
        value = getattr(
            application,
            key,
            None,
        )

        if value is not None:
            result[key] = value

    return result


def percentage(
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return round(
        numerator / denominator * 100,
        2,
    )


# ============================================================
# STATUS METRICS
# ============================================================


def build_status_distribution(
    applications: list[Any],
) -> dict[str, int]:
    counter = Counter()

    for application in applications:
        normalized = normalize_application(
            application
        )

        counter.update(
            [
                normalize_status(
                    normalized.get(
                        "status"
                    )
                )
            ]
        )

    return {
        status: counter.get(
            status,
            0,
        )
        for status in (
            "planned",
            "applied",
            "interview",
            "offer",
            "rejected",
            "withdrawn",
        )
    }


def calculate_pipeline_metrics(
    status_distribution: dict[str, int],
) -> dict[str, float | int]:
    planned = status_distribution[
        "planned"
    ]

    applied_only = status_distribution[
        "applied"
    ]

    interviews_only = status_distribution[
        "interview"
    ]

    offers = status_distribution[
        "offer"
    ]

    rejected = status_distribution[
        "rejected"
    ]

    withdrawn = status_distribution[
        "withdrawn"
    ]

    total = sum(
        status_distribution.values()
    )

    # Candidaturas que avançaram além de planned.
    applied_total = (
        applied_only
        + interviews_only
        + offers
        + rejected
    )

    interview_total = (
        interviews_only
        + offers
    )

    return {
        "total": total,
        "planned": planned,
        "applied": applied_total,
        "interviews": interview_total,
        "offers": offers,
        "rejected": rejected,
        "withdrawn": withdrawn,
        "application_rate": percentage(
            applied_total,
            total,
        ),
        "interview_rate": percentage(
            interview_total,
            applied_total,
        ),
        "offer_rate": percentage(
            offers,
            interview_total,
        ),
        "rejection_rate": percentage(
            rejected,
            applied_total,
        ),
    }


# ============================================================
# PROFILE PERFORMANCE
# ============================================================


def build_profile_performance(
    applications: list[Any],
    analyses: list[Any] | None = None,
) -> list[ProfilePerformance]:
    """
    Usa profile_id da candidatura quando existir.
    Como fallback, procura profile_id pelo analysis_id.
    """

    analysis_profile_map = {}

    for analysis in analyses or []:
        analysis_id = get_value(
            analysis,
            "id",
        )

        profile_id = get_value(
            analysis,
            "profile_id",
        )

        if analysis_id and profile_id:
            analysis_profile_map[
                str(analysis_id)
            ] = str(profile_id)

    grouped: dict[
        str,
        list[dict[str, Any]]
    ] = defaultdict(list)

    for application in applications:
        item = normalize_application(
            application
        )

        profile_id = item.get(
            "profile_id"
        )

        if not profile_id:
            analysis_id = item.get(
                "analysis_id"
            )

            if analysis_id:
                profile_id = (
                    analysis_profile_map.get(
                        str(analysis_id)
                    )
                )

        if not profile_id:
            profile_id = (
                "perfil_nao_identificado"
            )

        grouped[
            str(profile_id)
        ].append(item)

    result = []

    for profile_id, items in grouped.items():
        distribution = (
            build_status_distribution(
                items
            )
        )

        metrics = (
            calculate_pipeline_metrics(
                distribution
            )
        )

        result.append(
            ProfilePerformance(
                profile_id=profile_id,
                total_applications=int(
                    metrics["total"]
                ),
                applied=int(
                    metrics["applied"]
                ),
                interviews=int(
                    metrics["interviews"]
                ),
                offers=int(
                    metrics["offers"]
                ),
                rejected=int(
                    metrics["rejected"]
                ),
                interview_rate=float(
                    metrics["interview_rate"]
                ),
                offer_rate=float(
                    metrics["offer_rate"]
                ),
            )
        )

    result.sort(
        key=lambda item: (
            item.offers,
            item.interviews,
            item.interview_rate,
            item.total_applications,
        ),
        reverse=True,
    )

    return result


# ============================================================
# BOTTLENECK
# ============================================================


def detect_bottleneck(
    total: int,
    applied: int,
    interviews: int,
    offers: int,
) -> str:
    if total == 0:
        return "SEM DADOS"

    application_rate = percentage(
        applied,
        total,
    )

    interview_rate = percentage(
        interviews,
        applied,
    )

    offer_rate = percentage(
        offers,
        interviews,
    )

    if application_rate < 50:
        return "PLANEJAMENTO → CANDIDATURA"

    if applied >= 3 and interview_rate < 25:
        return "CANDIDATURA → ENTREVISTA"

    if interviews >= 2 and offer_rate < 30:
        return "ENTREVISTA → OFERTA"

    return "SEM GARGALO CRÍTICO"


# ============================================================
# INSIGHTS
# ============================================================


def build_strengths(
    interview_rate: float,
    offer_rate: float,
) -> list[str]:
    strengths = []

    if interview_rate >= 40:
        strengths.append(
            "Boa conversão de candidaturas em entrevistas."
        )

    if offer_rate >= 35:
        strengths.append(
            "Boa conversão de entrevistas em ofertas."
        )

    return strengths


def build_risks(
    total: int,
    application_rate: float,
    interview_rate: float,
    rejection_rate: float,
) -> list[str]:
    risks = []

    if total < 3:
        risks.append(
            "Histórico ainda pequeno para conclusões robustas."
        )

    if total >= 3 and application_rate < 50:
        risks.append(
            "Muitas oportunidades permanecem planejadas sem candidatura."
        )

    if total >= 3 and interview_rate < 25:
        risks.append(
            "Baixa conversão de candidatura para entrevista."
        )

    if rejection_rate >= 50:
        risks.append(
            "Taxa de rejeição elevada no histórico."
        )

    return risks


def build_executive_insights(
    total: int,
    interview_rate: float,
    offer_rate: float,
    bottleneck: str,
    profile_performance: list[ProfilePerformance],
) -> list[str]:
    insights = []

    if total == 0:
        return [
            "Ainda não há candidaturas suficientes para Application Intelligence."
        ]

    insights.append(
        f"O pipeline possui {total} candidatura(s) registrada(s)."
    )

    if interview_rate > 0:
        insights.append(
            f"A conversão candidatura → entrevista é de {interview_rate:.1f}%."
        )

    if offer_rate > 0:
        insights.append(
            f"A conversão entrevista → oferta é de {offer_rate:.1f}%."
        )

    if bottleneck != "SEM GARGALO CRÍTICO":
        insights.append(
            f"Principal gargalo atual: {bottleneck}."
        )

    identified_profiles = [
        item
        for item in profile_performance
        if item.profile_id
        != "perfil_nao_identificado"
    ]

    if len(
        identified_profiles
    ) >= 2:
        best = identified_profiles[0]

        insights.append(
            "O histórico já permite comparar desempenho entre versões de CV; "
            f"o perfil {best.profile_id} aparece atualmente como o mais eficiente."
        )

    return insights[:6]


def build_next_best_action(
    bottleneck: str,
    total: int,
) -> str:
    if total == 0:
        return (
            "Registrar candidaturas e atualizar seus status para gerar "
            "Application Intelligence."
        )

    if bottleneck == "PLANEJAMENTO → CANDIDATURA":
        return (
            "Revisar oportunidades planejadas e priorizar candidaturas "
            "com maior Decision Score."
        )

    if bottleneck == "CANDIDATURA → ENTREVISTA":
        return (
            "Revisar seleção de vagas, CV utilizado e posicionamento ATS "
            "antes das próximas candidaturas."
        )

    if bottleneck == "ENTREVISTA → OFERTA":
        return (
            "Priorizar preparação de entrevistas e análise dos feedbacks "
            "das etapas finais."
        )

    return (
        "Manter o pipeline atualizado e ampliar o histórico para identificar "
        "padrões de conversão por vaga e versão de CV."
    )


def calculate_confidence(
    total: int,
) -> float:
    if total <= 0:
        return 0.0

    if total == 1:
        return 30.0

    if total <= 3:
        return 50.0

    if total <= 6:
        return 70.0

    if total <= 10:
        return 85.0

    return 95.0


# ============================================================
# MAIN ENGINE
# ============================================================


def analyze_application_history(
    applications: list[Any],
    analyses: list[Any] | None = None,
) -> ApplicationIntelligenceReport:
    applications = (
        applications or []
    )

    distribution = (
        build_status_distribution(
            applications
        )
    )

    metrics = (
        calculate_pipeline_metrics(
            distribution
        )
    )

    profile_performance = (
        build_profile_performance(
            applications,
            analyses=analyses,
        )
    )

    total = int(
        metrics["total"]
    )

    applied = int(
        metrics["applied"]
    )

    interviews = int(
        metrics["interviews"]
    )

    offers = int(
        metrics["offers"]
    )

    bottleneck = detect_bottleneck(
        total=total,
        applied=applied,
        interviews=interviews,
        offers=offers,
    )

    dominant_status = (
        max(
            distribution,
            key=distribution.get,
        )
        if total
        else "none"
    )

    strengths = build_strengths(
        interview_rate=float(
            metrics["interview_rate"]
        ),
        offer_rate=float(
            metrics["offer_rate"]
        ),
    )

    risks = build_risks(
        total=total,
        application_rate=float(
            metrics["application_rate"]
        ),
        interview_rate=float(
            metrics["interview_rate"]
        ),
        rejection_rate=float(
            metrics["rejection_rate"]
        ),
    )

    insights = (
        build_executive_insights(
            total=total,
            interview_rate=float(
                metrics["interview_rate"]
            ),
            offer_rate=float(
                metrics["offer_rate"]
            ),
            bottleneck=bottleneck,
            profile_performance=profile_performance,
        )
    )

    next_best_action = (
        build_next_best_action(
            bottleneck=bottleneck,
            total=total,
        )
    )

    summary = (
        f"{total} candidatura(s), "
        f"{applied} aplicada(s), "
        f"{interviews} entrevista(s) e "
        f"{offers} oferta(s). "
        f"Gargalo: {bottleneck}."
        if total
        else (
            "Ainda não há candidaturas suficientes "
            "para análise de pipeline."
        )
    )

    return ApplicationIntelligenceReport(
        total_applications=total,
        planned=int(
            metrics["planned"]
        ),
        applied=applied,
        interviews=interviews,
        offers=offers,
        rejected=int(
            metrics["rejected"]
        ),
        withdrawn=int(
            metrics["withdrawn"]
        ),
        application_rate=float(
            metrics["application_rate"]
        ),
        interview_rate=float(
            metrics["interview_rate"]
        ),
        offer_rate=float(
            metrics["offer_rate"]
        ),
        rejection_rate=float(
            metrics["rejection_rate"]
        ),
        dominant_status=dominant_status,
        bottleneck=bottleneck,
        confidence_score=calculate_confidence(
            total
        ),
        status_distribution=distribution,
        profile_performance=profile_performance,
        strengths=strengths,
        risks=risks,
        executive_insights=insights,
        next_best_action=next_best_action,
        summary=summary,
    )


def build_application_summary(
    report: ApplicationIntelligenceReport,
) -> dict[str, Any]:
    return report.to_dict()


# ============================================================
# SELF TEST
# ============================================================


def run_self_test() -> dict[str, Any]:
    analyses = [
        {
            "id": "ana_1",
            "profile_id": "prf_executivo",
        },
        {
            "id": "ana_2",
            "profile_id": "prf_executivo",
        },
        {
            "id": "ana_3",
            "profile_id": "prf_comercial",
        },
        {
            "id": "ana_4",
            "profile_id": "prf_comercial",
        },
    ]

    applications = [
        {
            "id": "app_1",
            "analysis_id": "ana_1",
            "status": "interview",
        },
        {
            "id": "app_2",
            "analysis_id": "ana_2",
            "status": "offer",
        },
        {
            "id": "app_3",
            "analysis_id": "ana_3",
            "status": "rejected",
        },
        {
            "id": "app_4",
            "analysis_id": "ana_4",
            "status": "applied",
        },
        {
            "id": "app_5",
            "analysis_id": None,
            "status": "planned",
        },
    ]

    report = (
        analyze_application_history(
            applications=applications,
            analyses=analyses,
        )
    )

    return {
        "status": "ok",
        "report": (
            build_application_summary(
                report
            )
        ),
    }


if __name__ == "__main__":
    result = run_self_test()

    print()
    print(
        "CareerCompass AI — Application Intelligence Engine"
    )
    print(
        "--------------------------------------------------"
    )
    print(
        f"Status: {result['status']}"
    )

    report = result[
        "report"
    ]

    print(
        f"Candidaturas: {report['total_applications']}"
    )
    print(
        f"Aplicadas: {report['applied']}"
    )
    print(
        f"Entrevistas: {report['interviews']}"
    )
    print(
        f"Ofertas: {report['offers']}"
    )
    print(
        f"Interview Rate: {report['interview_rate']}%"
    )
    print(
        f"Offer Rate: {report['offer_rate']}%"
    )
    print(
        f"Gargalo: {report['bottleneck']}"
    )
    print(
        f"Confiança: {report['confidence_score']}%"
    )

    print()
    print(
        "Profile Performance"
    )
    print(
        "-------------------"
    )

    for item in report[
        "profile_performance"
    ]:
        print(
            f"- {item['profile_id']}: "
            f"{item['total_applications']} candidatura(s), "
            f"{item['interviews']} entrevista(s), "
            f"{item['offers']} oferta(s)"
        )

    print()
    print(
        "Next Best Action"
    )
    print(
        "----------------"
    )
    print(
        report[
            "next_best_action"
        ]
    )
