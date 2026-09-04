"""
CareerCompass AI
Decision Engine

Consolida sinais de Career Intelligence e produz uma recomendação
executiva para cada oportunidade.

O engine combina:
- Career Fit;
- ATS Intelligence;
- CV Tailoring Readiness;
- Opportunity Intelligence;
- requisitos obrigatórios;
- gaps;
- senioridade;
- qualidade da informação disponível.

Princípios:
- não inventar evidências;
- penalizar gaps obrigatórios;
- diferenciar oportunidade aderente de oportunidade apenas atraente;
- produzir decisão explicável;
- apoiar priorização de tempo do candidato.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


# ============================================================
# DECISION MODEL
# ============================================================


class DecisionType(str, Enum):
    APPLY_NOW = "APPLY NOW"
    APPLY_AFTER_TAILORING = "APPLY AFTER TAILORING"
    STRETCH_OPPORTUNITY = "STRETCH OPPORTUNITY"
    LOW_PRIORITY = "LOW PRIORITY"
    DO_NOT_PRIORITIZE = "DO NOT PRIORITIZE"


@dataclass
class CareerDecision:
    decision: str

    decision_score: float
    confidence_score: float

    career_fit_score: float
    ats_score: float
    tailoring_score: float

    mandatory_coverage: float
    seniority_score: float | None

    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    mandatory_gaps: list[str] = field(default_factory=list)

    rationale: list[str] = field(default_factory=list)

    next_best_action: str = ""

    opportunity_quality: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# CONFIGURAÇÃO
# ============================================================


WEIGHTS = {
    "career_fit": 0.30,
    "ats": 0.25,
    "mandatory": 0.20,
    "tailoring": 0.15,
    "seniority": 0.10,
}


DECISION_THRESHOLDS = {
    DecisionType.APPLY_NOW: 80,
    DecisionType.APPLY_AFTER_TAILORING: 68,
    DecisionType.STRETCH_OPPORTUNITY: 55,
    DecisionType.LOW_PRIORITY: 40,
}


# ============================================================
# HELPERS
# ============================================================


def get_value(
    source: Any,
    key: str,
    default: Any = None,
) -> Any:
    """
    Recupera valor de dict ou objeto.
    """

    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(
            key,
            default,
        )

    return getattr(
        source,
        key,
        default,
    )


def normalize_score(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Normaliza scores para escala de 0 a 100.
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return default

    if isinstance(
        value,
        (int, float),
    ):
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
            return default

    else:
        return default

    if 0 <= score <= 1:
        score *= 100

    return round(
        max(
            0.0,
            min(
                score,
                100.0,
            ),
        ),
        2,
    )


def normalize_string_list(
    values: Any,
) -> list[str]:
    """
    Normaliza listas de strings.
    """

    if values is None:
        return []

    if isinstance(values, str):
        value = values.strip()

        if value:
            return [value]

        return []

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


# ============================================================
# INPUT EXTRACTION
# ============================================================


def extract_career_fit_score(
    career_fit_report: Any,
) -> float:
    """
    Extrai Career Fit de diferentes formatos de relatório.
    """

    for key in (
        "score",
        "career_fit_score",
        "fit_score",
        "overall_score",
    ):
        value = get_value(
            career_fit_report,
            key,
        )

        if value is not None:
            return normalize_score(value)

    return 0.0


def extract_ats_score(
    ats_report: Any,
) -> float:
    """
    Extrai ATS Score.
    """

    for key in (
        "score",
        "ats_score",
        "overall_score",
    ):
        value = get_value(
            ats_report,
            key,
        )

        if value is not None:
            return normalize_score(value)

    return 0.0


def extract_tailoring_score(
    tailoring_report: Any,
) -> float:
    """
    Extrai Tailoring Readiness.
    """

    for key in (
        "tailoring_score",
        "score",
        "readiness_score",
    ):
        value = get_value(
            tailoring_report,
            key,
        )

        if value is not None:
            return normalize_score(value)

    return 0.0


def extract_mandatory_coverage(
    ats_report: Any,
) -> float:
    """
    Extrai cobertura dos requisitos obrigatórios.
    """

    value = get_value(
        ats_report,
        "mandatory_coverage",
    )

    return normalize_score(value)


def extract_seniority_score(
    ats_report: Any,
) -> float | None:
    """
    Extrai compatibilidade de senioridade.
    """

    value = get_value(
        ats_report,
        "seniority_score",
    )

    if value is None:
        return None

    return normalize_score(value)


def extract_mandatory_gaps(
    ats_report: Any,
) -> list[str]:
    """
    Extrai gaps obrigatórios.
    """

    return normalize_string_list(
        get_value(
            ats_report,
            "mandatory_gaps",
            [],
        )
    )


def extract_strengths(
    career_fit_report: Any,
    ats_report: Any,
) -> list[str]:
    """
    Consolida pontos fortes identificados pelos engines.
    """

    strengths = []

    fit_strengths = normalize_string_list(
        get_value(
            career_fit_report,
            "strengths",
            [],
        )
    )

    ats_strengths = normalize_string_list(
        get_value(
            ats_report,
            "strengths",
            [],
        )
    )

    for item in (
        fit_strengths
        + ats_strengths
    ):
        if item not in strengths:
            strengths.append(item)

    return strengths


# ============================================================
# OPPORTUNITY QUALITY
# ============================================================


def calculate_opportunity_quality(
    opportunity_profile: Any,
) -> float:
    """
    Mede qualidade estrutural da oportunidade.

    Não representa compatibilidade do candidato.
    Representa o quanto a vaga está suficientemente descrita
    para suportar uma decisão confiável.
    """

    if opportunity_profile is None:
        return 50.0

    confidence = normalize_score(
        get_value(
            opportunity_profile,
            "confidence_score",
            0,
        )
    )

    mandatory_requirements = normalize_string_list(
        get_value(
            opportunity_profile,
            "mandatory_requirements",
            [],
        )
    )

    responsibilities = normalize_string_list(
        get_value(
            opportunity_profile,
            "responsibilities",
            [],
        )
    )

    skills = normalize_string_list(
        get_value(
            opportunity_profile,
            "skills",
            [],
        )
    )

    score = confidence * 0.60

    if mandatory_requirements:
        score += 15

    if responsibilities:
        score += 15

    if skills:
        score += 10

    return round(
        min(
            score,
            100,
        ),
        2,
    )


# ============================================================
# CORE SCORE
# ============================================================


def calculate_decision_score(
    career_fit_score: float,
    ats_score: float,
    tailoring_score: float,
    mandatory_coverage: float,
    seniority_score: float | None,
    mandatory_gaps: list[str],
) -> float:
    """
    Calcula o Opportunity Decision Score.

    Gaps obrigatórios recebem penalização explícita.
    """

    seniority_component = (
        seniority_score
        if seniority_score is not None
        else 65.0
    )

    score = (
        career_fit_score
        * WEIGHTS["career_fit"]
        +
        ats_score
        * WEIGHTS["ats"]
        +
        mandatory_coverage
        * WEIGHTS["mandatory"]
        +
        tailoring_score
        * WEIGHTS["tailoring"]
        +
        seniority_component
        * WEIGHTS["seniority"]
    )

    gap_penalty = min(
        len(mandatory_gaps) * 6,
        24,
    )

    score -= gap_penalty

    return round(
        max(
            0,
            min(
                score,
                100,
            ),
        ),
        2,
    )


# ============================================================
# DECISION RULES
# ============================================================


def classify_decision(
    decision_score: float,
    mandatory_coverage: float,
    mandatory_gaps: list[str],
    career_fit_score: float,
    ats_score: float,
) -> DecisionType:
    """
    Classifica a oportunidade.

    A classificação não depende apenas do score agregado.
    Regras críticas protegem contra falsos positivos.
    """

    gap_count = len(
        mandatory_gaps
    )

    # --------------------------------------------------------
    # HARD STOP
    # --------------------------------------------------------

    if (
        mandatory_coverage < 30
        and gap_count >= 3
    ):
        return (
            DecisionType.DO_NOT_PRIORITIZE
        )

    if (
        career_fit_score < 35
        and ats_score < 35
    ):
        return (
            DecisionType.DO_NOT_PRIORITIZE
        )

    # --------------------------------------------------------
    # APPLY NOW
    # --------------------------------------------------------

    if (
        decision_score
        >= DECISION_THRESHOLDS[
            DecisionType.APPLY_NOW
        ]
        and mandatory_coverage >= 80
        and gap_count <= 1
    ):
        return DecisionType.APPLY_NOW

    # --------------------------------------------------------
    # APPLY AFTER TAILORING
    # --------------------------------------------------------

    if (
        decision_score
        >= DECISION_THRESHOLDS[
            DecisionType.APPLY_AFTER_TAILORING
        ]
        and mandatory_coverage >= 60
        and gap_count <= 3
    ):
        return (
            DecisionType.APPLY_AFTER_TAILORING
        )

    # --------------------------------------------------------
    # STRETCH
    # --------------------------------------------------------

    if (
        decision_score
        >= DECISION_THRESHOLDS[
            DecisionType.STRETCH_OPPORTUNITY
        ]
    ):
        return (
            DecisionType.STRETCH_OPPORTUNITY
        )

    # --------------------------------------------------------
    # LOW PRIORITY
    # --------------------------------------------------------

    if (
        decision_score
        >= DECISION_THRESHOLDS[
            DecisionType.LOW_PRIORITY
        ]
    ):
        return DecisionType.LOW_PRIORITY

    return DecisionType.DO_NOT_PRIORITIZE


# ============================================================
# EXPLANATION ENGINE
# ============================================================


def build_rationale(
    decision: DecisionType,
    career_fit_score: float,
    ats_score: float,
    tailoring_score: float,
    mandatory_coverage: float,
    seniority_score: float | None,
    mandatory_gaps: list[str],
    opportunity_quality: float,
) -> tuple[
    list[str],
    list[str],
    list[str],
]:
    """
    Produz explicação executiva da decisão.
    """

    rationale = []
    strengths = []
    risks = []

    # Career Fit

    if career_fit_score >= 80:
        message = (
            "O perfil apresenta forte aderência "
            "global à oportunidade."
        )
        rationale.append(message)
        strengths.append(message)

    elif career_fit_score >= 65:
        message = (
            "O perfil apresenta aderência "
            "competitiva à oportunidade."
        )
        rationale.append(message)
        strengths.append(message)

    elif career_fit_score < 45:
        message = (
            "A aderência global do perfil "
            "à oportunidade é baixa."
        )
        rationale.append(message)
        risks.append(message)

    # ATS

    if ats_score >= 75:
        message = (
            "O currículo possui boa cobertura "
            "para triagem ATS."
        )
        rationale.append(message)
        strengths.append(message)

    elif ats_score < 55:
        message = (
            "A cobertura ATS ainda exige "
            "otimização antes da candidatura."
        )
        rationale.append(message)
        risks.append(message)

    # Mandatory

    if mandatory_coverage >= 85:
        message = (
            "A maior parte dos requisitos "
            "obrigatórios possui evidência."
        )
        rationale.append(message)
        strengths.append(message)

    elif mandatory_coverage < 60:
        message = (
            "A cobertura de requisitos "
            "obrigatórios é insuficiente."
        )
        rationale.append(message)
        risks.append(message)

    # Gaps

    if mandatory_gaps:
        gap_count = len(
            mandatory_gaps
        )

        message = (
            f"{gap_count} requisito(s) obrigatório(s) "
            "não possui(em) evidência suficiente."
        )

        rationale.append(message)
        risks.append(message)

    # Seniority

    if seniority_score is not None:

        if seniority_score >= 85:
            message = (
                "A senioridade do perfil é "
                "compatível com a posição."
            )
            rationale.append(message)
            strengths.append(message)

        elif seniority_score < 55:
            message = (
                "Existe risco de desalinhamento "
                "de senioridade."
            )
            rationale.append(message)
            risks.append(message)

    # Tailoring

    if tailoring_score >= 80:
        message = (
            "O currículo pode ser customizado "
            "com boa base de evidências existentes."
        )
        rationale.append(message)
        strengths.append(message)

    elif tailoring_score < 50:
        message = (
            "A customização do currículo possui "
            "limitações por falta de evidências."
        )
        rationale.append(message)
        risks.append(message)

    # Opportunity Quality

    if opportunity_quality < 50:
        message = (
            "A descrição da vaga possui pouca "
            "informação estruturada, reduzindo "
            "a confiança da recomendação."
        )
        rationale.append(message)
        risks.append(message)

    # Decision-specific explanation

    if decision == DecisionType.APPLY_NOW:
        rationale.insert(
            0,
            (
                "A oportunidade apresenta combinação "
                "favorável entre aderência, requisitos "
                "e posicionamento."
            ),
        )

    elif (
        decision
        == DecisionType.APPLY_AFTER_TAILORING
    ):
        rationale.insert(
            0,
            (
                "A oportunidade é competitiva, "
                "mas o currículo deve ser ajustado "
                "antes da candidatura."
            ),
        )

    elif (
        decision
        == DecisionType.STRETCH_OPPORTUNITY
    ):
        rationale.insert(
            0,
            (
                "A vaga é uma oportunidade de expansão, "
                "com aderência parcial e alguns gaps "
                "relevantes."
            ),
        )

    elif (
        decision
        == DecisionType.LOW_PRIORITY
    ):
        rationale.insert(
            0,
            (
                "O potencial de retorno da candidatura "
                "é limitado frente aos gaps identificados."
            ),
        )

    else:
        rationale.insert(
            0,
            (
                "Os gaps e a baixa aderência tornam "
                "esta candidatura pouco eficiente "
                "neste momento."
            ),
        )

    return (
        rationale,
        strengths,
        risks,
    )


# ============================================================
# NEXT BEST ACTION
# ============================================================


def build_next_best_action(
    decision: DecisionType,
    mandatory_gaps: list[str],
) -> str:
    """
    Define ação recomendada para o candidato.
    """

    if decision == DecisionType.APPLY_NOW:
        return (
            "Finalizar a versão customizada do currículo "
            "e priorizar a candidatura."
        )

    if (
        decision
        == DecisionType.APPLY_AFTER_TAILORING
    ):
        return (
            "Customizar headline, resumo, competências "
            "e evidências do currículo antes de aplicar."
        )

    if (
        decision
        == DecisionType.STRETCH_OPPORTUNITY
    ):
        if mandatory_gaps:
            return (
                "Avaliar se os gaps obrigatórios podem "
                "ser sustentados por experiências ainda "
                "não evidenciadas no currículo antes de aplicar."
            )

        return (
            "Considerar a candidatura como movimento "
            "de expansão profissional e preparar uma "
            "narrativa forte para os gaps."
        )

    if decision == DecisionType.LOW_PRIORITY:
        return (
            "Priorizar oportunidades com maior aderência "
            "antes de investir tempo nesta candidatura."
        )

    return (
        "Não priorizar esta oportunidade neste momento. "
        "Direcionar esforço para vagas com maior aderência."
    )


# ============================================================
# CONFIDENCE
# ============================================================


def calculate_decision_confidence(
    opportunity_quality: float,
    career_fit_score: float,
    ats_score: float,
    mandatory_coverage: float,
) -> float:
    """
    Estima a confiabilidade da decisão.

    Quanto mais dados úteis houver, maior a confiança.
    """

    score = (
        opportunity_quality * 0.35
        + career_fit_score * 0.20
        + ats_score * 0.20
        + mandatory_coverage * 0.25
    )

    return round(
        max(
            0,
            min(
                score,
                100,
            ),
        ),
        2,
    )


# ============================================================
# MAIN ENGINE
# ============================================================


def build_career_decision(
    career_fit_report: Any,
    ats_report: Any,
    tailoring_report: Any,
    opportunity_profile: Any = None,
) -> CareerDecision:
    """
    Executa a análise decisória completa.
    """

    career_fit_score = (
        extract_career_fit_score(
            career_fit_report
        )
    )

    ats_score = (
        extract_ats_score(
            ats_report
        )
    )

    tailoring_score = (
        extract_tailoring_score(
            tailoring_report
        )
    )

    mandatory_coverage = (
        extract_mandatory_coverage(
            ats_report
        )
    )

    seniority_score = (
        extract_seniority_score(
            ats_report
        )
    )

    mandatory_gaps = (
        extract_mandatory_gaps(
            ats_report
        )
    )

    detected_strengths = (
        extract_strengths(
            career_fit_report,
            ats_report,
        )
    )

    opportunity_quality = (
        calculate_opportunity_quality(
            opportunity_profile
        )
    )

    decision_score = (
        calculate_decision_score(
            career_fit_score=career_fit_score,
            ats_score=ats_score,
            tailoring_score=tailoring_score,
            mandatory_coverage=mandatory_coverage,
            seniority_score=seniority_score,
            mandatory_gaps=mandatory_gaps,
        )
    )

    decision = classify_decision(
        decision_score=decision_score,
        mandatory_coverage=mandatory_coverage,
        mandatory_gaps=mandatory_gaps,
        career_fit_score=career_fit_score,
        ats_score=ats_score,
    )

    (
        rationale,
        explanation_strengths,
        risks,
    ) = build_rationale(
        decision=decision,
        career_fit_score=career_fit_score,
        ats_score=ats_score,
        tailoring_score=tailoring_score,
        mandatory_coverage=mandatory_coverage,
        seniority_score=seniority_score,
        mandatory_gaps=mandatory_gaps,
        opportunity_quality=opportunity_quality,
    )

    strengths = []

    for item in (
        detected_strengths
        + explanation_strengths
    ):
        if item not in strengths:
            strengths.append(item)

    next_best_action = (
        build_next_best_action(
            decision,
            mandatory_gaps,
        )
    )

    confidence_score = (
        calculate_decision_confidence(
            opportunity_quality=opportunity_quality,
            career_fit_score=career_fit_score,
            ats_score=ats_score,
            mandatory_coverage=mandatory_coverage,
        )
    )

    return CareerDecision(
        decision=decision.value,
        decision_score=decision_score,
        confidence_score=confidence_score,
        career_fit_score=career_fit_score,
        ats_score=ats_score,
        tailoring_score=tailoring_score,
        mandatory_coverage=mandatory_coverage,
        seniority_score=seniority_score,
        strengths=strengths,
        risks=risks,
        mandatory_gaps=mandatory_gaps,
        rationale=rationale,
        next_best_action=next_best_action,
        opportunity_quality=opportunity_quality,
    )


# ============================================================
# SUMMARY
# ============================================================


def build_decision_summary(
    decision: CareerDecision,
) -> dict[str, Any]:
    """
    Versão resumida adequada para UI, persistência
    e relatórios.
    """

    return {
        "decision": decision.decision,
        "decision_score": (
            decision.decision_score
        ),
        "confidence_score": (
            decision.confidence_score
        ),
        "career_fit_score": (
            decision.career_fit_score
        ),
        "ats_score": decision.ats_score,
        "tailoring_score": (
            decision.tailoring_score
        ),
        "mandatory_coverage": (
            decision.mandatory_coverage
        ),
        "seniority_score": (
            decision.seniority_score
        ),
        "strengths": decision.strengths,
        "risks": decision.risks,
        "mandatory_gaps": (
            decision.mandatory_gaps
        ),
        "rationale": decision.rationale,
        "next_best_action": (
            decision.next_best_action
        ),
        "opportunity_quality": (
            decision.opportunity_quality
        ),
    }


# ============================================================
# SELF TEST
# ============================================================


def run_self_test() -> dict[str, Any]:
    """
    Executa cenário de teste independente.
    """

    career_fit_report = {
        "score": 76,
        "strengths": [
            "Gestão de Projetos",
            "Liderança",
            "Gestão de Stakeholders",
        ],
    }

    ats_report = {
        "score": 71,
        "mandatory_coverage": 78,
        "seniority_score": 100,
        "mandatory_gaps": [
            "Gestão de Riscos",
        ],
        "strengths": [
            "Power BI",
            "KPIs",
        ],
    }

    tailoring_report = {
        "tailoring_score": 82,
    }

    opportunity_profile = {
        "confidence_score": 87,
        "mandatory_requirements": [
            "Gestão de Projetos",
            "Liderança",
            "Gestão de Riscos",
        ],
        "responsibilities": [
            "Liderar projetos estratégicos",
            "Gerenciar stakeholders",
        ],
        "skills": [
            "Gestão de Projetos",
            "Liderança",
        ],
    }

    decision = build_career_decision(
        career_fit_report=career_fit_report,
        ats_report=ats_report,
        tailoring_report=tailoring_report,
        opportunity_profile=opportunity_profile,
    )

    return {
        "status": "ok",
        "decision": (
            build_decision_summary(
                decision
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
        "CareerCompass AI — Decision Engine"
    )
    print(
        "--------------------------------"
    )

    print(
        f"Status: {result['status']}"
    )

    decision = result["decision"]

    print()
    print(
        f"Decision: "
        f"{decision['decision']}"
    )

    print(
        f"Decision Score: "
        f"{decision['decision_score']}%"
    )

    print(
        f"Confidence: "
        f"{decision['confidence_score']}%"
    )

    print(
        f"Career Fit: "
        f"{decision['career_fit_score']}%"
    )

    print(
        f"ATS: "
        f"{decision['ats_score']}%"
    )

    print(
        f"Mandatory Coverage: "
        f"{decision['mandatory_coverage']}%"
    )

    print(
        f"Tailoring: "
        f"{decision['tailoring_score']}%"
    )

    print()
    print("Rationale:")

    for item in decision["rationale"]:
        print(
            f" - {item}"
        )

    print()
    print("Risks:")

    for item in decision["risks"]:
        print(
            f" - {item}"
        )

    print()
    print(
        "Next Best Action:"
    )

    print(
        decision[
            "next_best_action"
        ]
    )
