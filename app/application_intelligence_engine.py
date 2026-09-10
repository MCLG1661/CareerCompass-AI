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

import json
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
class DecisionPerformance:
    segment: str
    applications: int
    interviews: int
    offers: int
    rejected: int
    interview_rate: float
    offer_rate: float
    rejection_rate: float
    avg_decision_score: float
    avg_strategic_fit: float

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

    # Sprint 6.4 — Decision Learning
    decision_learning_samples: int = 0
    decision_performance: list[DecisionPerformance] = field(default_factory=list)
    decision_score_performance: list[DecisionPerformance] = field(default_factory=list)
    decision_learning_signal: str = "SEM DADOS SUFICIENTES"
    decision_learning_summary: str = ""

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


def deserialize_if_needed(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    value = value.strip()

    if not value or not (value.startswith("{") or value.startswith("[")):
        return value

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def normalize_score(value: Any) -> float:
    if value is None or isinstance(value, bool):
        return 0.0

    if isinstance(value, (int, float)):
        score = float(value)
    elif isinstance(value, str):
        try:
            score = float(value.replace("%", "").replace(",", ".").strip())
        except ValueError:
            return 0.0
    else:
        return 0.0

    if 0 <= score <= 1:
        score *= 100

    return round(max(0.0, min(score, 100.0)), 2)


def extract_decision_context(
    analysis: Any,
) -> dict[str, Any]:
    decision_report = deserialize_if_needed(
        get_value(analysis, "decision_report", {})
    )
    if not isinstance(decision_report, dict):
        decision_report = {}

    career_decision = deserialize_if_needed(
        get_value(analysis, "career_decision", {})
    )
    if not isinstance(career_decision, dict) or not career_decision:
        career_decision = deserialize_if_needed(
            decision_report.get("career_decision", {})
        )
    if not isinstance(career_decision, dict):
        career_decision = {}

    strategic_fit = deserialize_if_needed(
        get_value(analysis, "strategic_fit_result", {})
    )
    if not isinstance(strategic_fit, dict) or not strategic_fit:
        strategic_fit = deserialize_if_needed(
            decision_report.get("strategic_fit_result", {})
        )
    if not isinstance(strategic_fit, dict):
        strategic_fit = {}

    decision_score = normalize_score(
        get_value(analysis, "decision_score")
        if get_value(analysis, "decision_score") is not None
        else career_decision.get(
            "decision_score",
            career_decision.get("score"),
        )
    )

    decision_classification = (
        career_decision.get("classification")
        or career_decision.get("decision")
        or decision_report.get("classification")
    )

    strategic_score = 0.0
    for key in (
        "strategic_fit_score",
        "score",
        "overall_score",
        "strategic_score",
    ):
        if strategic_fit.get(key) is not None:
            strategic_score = normalize_score(strategic_fit.get(key))
            break

    return {
        "decision_score": decision_score,
        "decision_classification": (
            str(decision_classification).strip()
            if decision_classification
            else ""
        ),
        "strategic_fit_score": strategic_score,
    }


def decision_score_band(score: float) -> str:
    if score >= 70:
        return "HIGH DECISION SCORE"
    if score >= 50:
        return "MEDIUM DECISION SCORE"
    return "LOW DECISION SCORE"


def build_decision_learning(
    applications: list[Any],
    analyses: list[Any] | None = None,
) -> tuple[
    int,
    list[DecisionPerformance],
    list[DecisionPerformance],
    str,
    str,
]:
    """
    Relaciona recomendações persistidas com resultados reais do pipeline.

    Apenas candidaturas efetivamente aplicadas ou encerradas entram na amostra
    de aprendizagem. Planned e withdrawn permanecem no pipeline, mas não são
    usados para inferir performance da recomendação.
    """

    analysis_map: dict[str, Any] = {}

    for analysis in analyses or []:
        analysis_id = get_value(analysis, "id")
        if analysis_id:
            analysis_map[str(analysis_id)] = analysis

    records: list[dict[str, Any]] = []

    for application in applications or []:
        item = normalize_application(application)
        status = normalize_status(item.get("status"))

        if status not in {"applied", "interview", "offer", "rejected"}:
            continue

        analysis_id = item.get("analysis_id")
        if not analysis_id:
            continue

        analysis = analysis_map.get(str(analysis_id))
        if analysis is None:
            continue

        context = extract_decision_context(analysis)

        if (
            context["decision_score"] <= 0
            and not context["decision_classification"]
        ):
            continue

        records.append(
            {
                "status": status,
                **context,
            }
        )

    def summarize(
        grouped: dict[str, list[dict[str, Any]]],
    ) -> list[DecisionPerformance]:
        result: list[DecisionPerformance] = []

        for segment, items in grouped.items():
            total = len(items)
            interviews = sum(
                1
                for item in items
                if item["status"] in {"interview", "offer"}
            )
            offers = sum(
                1
                for item in items
                if item["status"] == "offer"
            )
            rejected = sum(
                1
                for item in items
                if item["status"] == "rejected"
            )

            decision_scores = [
                item["decision_score"]
                for item in items
                if item["decision_score"] > 0
            ]
            strategic_scores = [
                item["strategic_fit_score"]
                for item in items
                if item["strategic_fit_score"] > 0
            ]

            result.append(
                DecisionPerformance(
                    segment=segment,
                    applications=total,
                    interviews=interviews,
                    offers=offers,
                    rejected=rejected,
                    interview_rate=percentage(interviews, total),
                    offer_rate=percentage(offers, total),
                    rejection_rate=percentage(rejected, total),
                    avg_decision_score=round(
                        sum(decision_scores) / len(decision_scores),
                        2,
                    )
                    if decision_scores
                    else 0.0,
                    avg_strategic_fit=round(
                        sum(strategic_scores) / len(strategic_scores),
                        2,
                    )
                    if strategic_scores
                    else 0.0,
                )
            )

        result.sort(
            key=lambda item: (
                item.offer_rate,
                item.interview_rate,
                item.avg_decision_score,
                item.applications,
            ),
            reverse=True,
        )

        return result

    by_classification: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_score_band: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        classification = (
            record["decision_classification"]
            or "SEM CLASSIFICAÇÃO"
        )
        by_classification[classification].append(record)

        if record["decision_score"] > 0:
            by_score_band[
                decision_score_band(record["decision_score"])
            ].append(record)

    classification_performance = summarize(by_classification)
    score_performance = summarize(by_score_band)

    sample_count = len(records)

    if sample_count < 3:
        signal = "SEM DADOS SUFICIENTES"
        summary = (
            f"{sample_count} candidatura(s) possuem recomendação vinculada a "
            "resultado real. São necessárias pelo menos 3 para iniciar "
            "Decision Learning confiável."
        )
        return (
            sample_count,
            classification_performance,
            score_performance,
            signal,
            summary,
        )

    score_map = {
        item.segment: item
        for item in score_performance
    }
    high = score_map.get("HIGH DECISION SCORE")
    low = score_map.get("LOW DECISION SCORE")

    if high and low:
        if (
            high.interview_rate >= low.interview_rate + 20
            and high.offer_rate >= low.offer_rate
        ):
            signal = "RECOMENDAÇÕES COM SINAL POSITIVO"
            summary = (
                "O histórico indica que candidaturas com Decision Score alto "
                "estão avançando mais que as de score baixo."
            )
        elif (
            low.interview_rate >= high.interview_rate + 20
            or low.offer_rate > high.offer_rate
        ):
            signal = "RECOMENDAÇÕES PEDEM RECALIBRAÇÃO"
            summary = (
                "O histórico ainda não confirma melhor performance das "
                "oportunidades com Decision Score alto."
            )
        else:
            signal = "SINAL AINDA MISTO"
            summary = (
                "Os resultados por faixa de Decision Score ainda são próximos; "
                "amplie a amostra antes de recalibrar o motor."
            )
    else:
        signal = "AMOSTRA PARCIAL"
        summary = (
            "Já existem resultados vinculados às recomendações, mas ainda "
            "faltam faixas comparáveis de Decision Score."
        )

    return (
        sample_count,
        classification_performance,
        score_performance,
        signal,
        summary,
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

    (
        decision_learning_samples,
        decision_performance,
        decision_score_performance,
        decision_learning_signal,
        decision_learning_summary,
    ) = build_decision_learning(
        applications=applications,
        analyses=analyses,
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
        decision_learning_samples=decision_learning_samples,
        decision_performance=decision_performance,
        decision_score_performance=decision_score_performance,
        decision_learning_signal=decision_learning_signal,
        decision_learning_summary=decision_learning_summary,
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
            "decision_score": 78,
            "career_decision": {
                "decision_score": 78,
                "classification": "STRONG OPPORTUNITY",
            },
            "strategic_fit_result": {
                "strategic_fit_score": 82,
            },
        },
        {
            "id": "ana_2",
            "profile_id": "prf_executivo",
            "decision_score": 88,
            "career_decision": {
                "decision_score": 88,
                "classification": "STRONG OPPORTUNITY",
            },
            "strategic_fit_result": {
                "strategic_fit_score": 90,
            },
        },
        {
            "id": "ana_3",
            "profile_id": "prf_comercial",
            "decision_score": 38,
            "career_decision": {
                "decision_score": 38,
                "classification": "LOW PRIORITY",
            },
            "strategic_fit_result": {
                "strategic_fit_score": 42,
            },
        },
        {
            "id": "ana_4",
            "profile_id": "prf_comercial",
            "decision_score": 58,
            "career_decision": {
                "decision_score": 58,
                "classification": "STRETCH OPPORTUNITY",
            },
            "strategic_fit_result": {
                "strategic_fit_score": 61,
            },
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

    assert report.decision_learning_samples == 4
    assert report.decision_learning_signal == "RECOMENDAÇÕES COM SINAL POSITIVO"
    assert len(report.decision_performance) == 3
    assert len(report.decision_score_performance) == 3

    high_band = next(
        item
        for item in report.decision_score_performance
        if item.segment == "HIGH DECISION SCORE"
    )
    low_band = next(
        item
        for item in report.decision_score_performance
        if item.segment == "LOW DECISION SCORE"
    )

    assert high_band.interview_rate == 100.0
    assert high_band.offer_rate == 50.0
    assert low_band.interview_rate == 0.0
    assert low_band.rejection_rate == 100.0

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
