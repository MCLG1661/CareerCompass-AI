from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# =========================================================
# IMPORTS COMPATÍVEIS
# =========================================================

try:
    from .ats_engine import ATSReport
    from .recommendation_engine import RecommendationReport
except ImportError:
    from ats_engine import ATSReport
    from recommendation_engine import RecommendationReport


# =========================================================
# MODELOS
# =========================================================

@dataclass
class CVTailoringReport:
    headline: str
    professional_summary: str
    priority_skills: list[str]
    ats_keywords: list[str]
    evidence_to_highlight: list[str]
    gaps_to_respect: list[str]
    editing_recommendations: list[str]
    interview_bridge: list[str]
    tailoring_score: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline": self.headline,
            "professional_summary": self.professional_summary,
            "priority_skills": self.priority_skills,
            "ats_keywords": self.ats_keywords,
            "evidence_to_highlight": self.evidence_to_highlight,
            "gaps_to_respect": self.gaps_to_respect,
            "editing_recommendations": self.editing_recommendations,
            "interview_bridge": self.interview_bridge,
            "tailoring_score": self.tailoring_score,
        }


# =========================================================
# HELPERS
# =========================================================

def _unique(
    items: list[str],
) -> list[str]:

    seen = set()
    result = []

    for item in items:
        if not item:
            continue

        normalized = str(item).strip()

        if not normalized:
            continue

        key = normalized.casefold()

        if key not in seen:
            seen.add(key)
            result.append(normalized)

    return result


def _clean_text(
    text: str,
) -> str:

    if not text:
        return ""

    return " ".join(
        str(text)
        .replace("\n", " ")
        .replace("\r", " ")
        .split()
    )


def _contains_term(
    text: str,
    term: str,
) -> bool:

    if not text or not term:
        return False

    return term.casefold() in text.casefold()


def _safe_attribute(
    obj: Any,
    attribute: str,
    default: Any = None,
) -> Any:

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(
            attribute,
            default,
        )

    return getattr(
        obj,
        attribute,
        default,
    )


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default



# =========================================================
# DEDUPLICAÇÃO SEMÂNTICA DE HEADLINE
# =========================================================

HEADLINE_EQUIVALENCE_GROUPS = {
    "projetos": [
        "gerente de projetos",
        "gestão de projetos",
        "gestao de projetos",
        "project management",
        "pmo",
    ],
    "operacoes": [
        "gerente de operações",
        "gerente de operacoes",
        "gestão de operações",
        "gestao de operacoes",
        "operations management",
    ],
    "marketing": [
        "gerente de marketing",
        "gestão de marketing",
        "gestao de marketing",
        "marketing",
    ],
    "vendas": [
        "gerente comercial",
        "gerente de vendas",
        "gestão comercial",
        "gestao comercial",
        "vendas",
        "sales",
    ],
}


def _headline_semantic_key(
    value: str,
) -> str:
    """
    Retorna uma chave semântica simples para evitar
    repetições como:

    Gerente de Projetos | Gestão de Projetos
    """

    normalized = _clean_text(
        value
    ).casefold()

    for key, terms in HEADLINE_EQUIVALENCE_GROUPS.items():

        if any(
            term.casefold() in normalized
            for term in terms
        ):
            return key

    return normalized


def _deduplicate_headline_items(
    title: str,
    strengths: list[str],
    limit: int = 3,
) -> list[str]:

    used_keys = set()

    if title:
        used_keys.add(
            _headline_semantic_key(
                title
            )
        )

    selected: list[str] = []

    for strength in strengths:

        key = _headline_semantic_key(
            strength
        )

        if key in used_keys:
            continue

        used_keys.add(
            key
        )

        selected.append(
            strength
        )

        if len(selected) >= limit:
            break

    return selected


# =========================================================
# HEADLINE
# =========================================================

def _build_headline(
    job_title: str,
    ats_report: ATSReport,
) -> str:
    """
    Cria headline orientada à vaga usando apenas
    competências efetivamente identificadas como forças.
    """

    title = _clean_text(
        job_title
    )

    strengths = _unique(
        list(
            _safe_attribute(
                ats_report,
                "strengths",
                [],
            )
            or []
        )
    )

    selected_strengths = _deduplicate_headline_items(
        title=title,
        strengths=strengths,
        limit=3,
    )

    if title and selected_strengths:
        return (
            f"{title} | "
            + " | ".join(
                selected_strengths
            )
        )

    if title:
        return title

    if selected_strengths:
        return " | ".join(
            selected_strengths
        )

    return "Perfil Profissional"


# =========================================================
# RESUMO PROFISSIONAL
# =========================================================

def _build_professional_summary(
    profile_text: str,
    job_title: str,
    ats_report: ATSReport,
) -> str:
    """
    Gera um resumo de posicionamento sem criar fatos novos.
    """

    profile = _clean_text(
        profile_text
    )

    title = _clean_text(
        job_title
    )

    strengths = _unique(
        list(
            _safe_attribute(
                ats_report,
                "strengths",
                [],
            )
            or []
        )
    )

    strongest = strengths[:5]

    seniority_score = _safe_int(
        _safe_attribute(
            ats_report,
            "seniority_score",
            0,
        ),
        0,
    )

    if strongest:
        skills_text = ", ".join(
            strongest
        )

        summary = (
            f"Profissional com experiência e competências identificadas "
            f"em {skills_text}, com perfil orientado à geração de valor, "
            f"execução e resultados."
        )

    else:
        summary = (
            "Profissional com experiência multidisciplinar e atuação "
            "orientada a resultados, melhoria de processos e objetivos "
            "de negócio."
        )

    if title:
        summary += (
            f" Para a oportunidade de {title}, o posicionamento deve "
            f"priorizar as experiências e evidências diretamente "
            f"relacionadas aos requisitos da função."
        )

    if seniority_score >= 80:
        summary += (
            " A senioridade identificada apresenta forte aderência "
            "ao nível da oportunidade."
        )

    elif seniority_score >= 60:
        summary += (
            " A apresentação profissional deve tornar mais explícitos "
            "o escopo, a autonomia e a complexidade das responsabilidades "
            "já exercidas."
        )

    elif seniority_score > 0:
        summary += (
            " A senioridade identificada apresenta aderência parcial, "
            "por isso o currículo deve evidenciar com clareza o escopo "
            "e o nível de responsabilidade das experiências mais relevantes."
        )

    if profile:
        summary += (
            " A customização deve preservar integralmente a veracidade "
            "do histórico profissional original."
        )

    return summary


# =========================================================
# COMPETÊNCIAS PRIORITÁRIAS
# =========================================================

def _build_priority_skills(
    ats_report: ATSReport,
) -> list[str]:
    """
    Retorna somente competências atendidas pelo candidato.
    """

    strengths = list(
        _safe_attribute(
            ats_report,
            "strengths",
            [],
        )
        or []
    )

    return _unique(
        strengths
    )


# =========================================================
# KEYWORDS ATS
# =========================================================

def _build_ats_keywords(
    ats_report: ATSReport,
) -> list[str]:
    """
    Keywords seguras para utilização no CV.

    Apenas requisitos marcados como atendidos podem ser
    tratados como keywords recomendadas para inclusão.
    """

    keywords: list[str] = []

    requirements = list(
        _safe_attribute(
            ats_report,
            "requirements",
            [],
        )
        or []
    )

    for requirement in requirements:

        status = _safe_attribute(
            requirement,
            "status",
            "",
        )

        skill = _safe_attribute(
            requirement,
            "skill",
            "",
        )

        if (
            status == "Atende"
            and skill
        ):
            keywords.append(
                str(skill)
            )

    if not keywords:
        keywords.extend(
            list(
                _safe_attribute(
                    ats_report,
                    "strengths",
                    [],
                )
                or []
            )
        )

    return _unique(
        keywords
    )


# =========================================================
# EVIDÊNCIAS PARA DESTACAR
# =========================================================

def _build_evidence_to_highlight(
    profile_text: str,
    ats_report: ATSReport,
) -> list[str]:
    """
    Identifica competências já comprovadas que devem ganhar
    maior visibilidade no currículo.
    """

    profile = _clean_text(
        profile_text
    )

    strengths = list(
        _safe_attribute(
            ats_report,
            "strengths",
            [],
        )
        or []
    )

    evidence: list[str] = []

    for skill in strengths:

        if _contains_term(
            profile,
            str(skill),
        ):
            evidence.append(
                f"Dar maior visibilidade à experiência comprovada "
                f"em {skill}."
            )

        else:
            evidence.append(
                f"Manter {skill} em destaque somente nas seções em que "
                f"já exista evidência profissional correspondente."
            )

    return _unique(
        evidence
    )


# =========================================================
# GAPS QUE DEVEM SER RESPEITADOS
# =========================================================

def _build_gaps_to_respect(
    ats_report: ATSReport,
) -> list[str]:
    """
    Impede que o tailoring transforme gaps em competências
    fictícias.
    """

    gaps: list[str] = []

    mandatory_gaps = list(
        _safe_attribute(
            ats_report,
            "mandatory_gaps",
            [],
        )
        or []
    )

    preferred_gaps = list(
        _safe_attribute(
            ats_report,
            "preferred_gaps",
            [],
        )
        or []
    )

    for skill in mandatory_gaps:

        gaps.append(
            f"{skill}: requisito obrigatório sem evidência suficiente. "
            f"Não incluir como competência dominada sem comprovação."
        )

    for skill in preferred_gaps:

        gaps.append(
            f"{skill}: diferencial sem evidência suficiente. "
            f"Não acrescentar artificialmente ao currículo."
        )

    return _unique(
        gaps
    )


# =========================================================
# RECOMENDAÇÕES DE EDIÇÃO
# =========================================================

def _build_editing_recommendations(
    ats_report: ATSReport,
    recommendation_report: RecommendationReport,
) -> list[str]:

    recommendations: list[str] = []

    recommendations.extend(
        list(
            _safe_attribute(
                recommendation_report,
                "cv_guidance",
                [],
            )
            or []
        )
    )

    score = _safe_int(
        _safe_attribute(
            ats_report,
            "score",
            0,
        ),
        0,
    )

    keyword_coverage = _safe_int(
        _safe_attribute(
            ats_report,
            "keyword_coverage",
            0,
        ),
        0,
    )

    mandatory_coverage = _safe_int(
        _safe_attribute(
            ats_report,
            "mandatory_coverage",
            0,
        ),
        0,
    )

    if score >= 70:

        recommendations.append(
            "Preservar a estrutura central do currículo e concentrar "
            "a customização em headline, resumo, competências e experiências "
            "mais aderentes à oportunidade."
        )

    else:

        recommendations.append(
            "Reorganizar a ordem de destaque das experiências e competências "
            "para aproximar o currículo dos requisitos efetivamente "
            "comprovados da oportunidade."
        )

    if keyword_coverage < 70:

        recommendations.append(
            "Revisar a terminologia utilizada no currículo e aproximá-la "
            "da linguagem da vaga somente quando os termos representarem "
            "experiências ou competências reais."
        )

    if mandatory_coverage < 80:

        recommendations.append(
            "Não mascarar gaps obrigatórios. Quando houver experiência "
            "transferível, descrevê-la de forma objetiva sem afirmar "
            "domínio inexistente."
        )

    recommendations.append(
        "Priorizar realizações, indicadores, resultados e impacto "
        "nas experiências mais relevantes para a oportunidade."
    )

    recommendations.append(
        "Evitar excesso de palavras-chave sem contexto. Sempre que possível, "
        "associar competências a responsabilidades, projetos ou resultados."
    )

    recommendations.append(
        "Não alterar cargos, empresas, datas, formação, certificações "
        "ou resultados para aumentar artificialmente a aderência."
    )

    return _unique(
        recommendations
    )


# =========================================================
# PONTE PARA ENTREVISTA
# =========================================================

def _build_interview_bridge(
    recommendation_report: RecommendationReport,
) -> list[str]:

    guidance = list(
        _safe_attribute(
            recommendation_report,
            "interview_guidance",
            [],
        )
        or []
    )

    guidance.append(
        "Utilizar na entrevista os mesmos pilares de posicionamento "
        "destacados no currículo customizado."
    )

    guidance.append(
        "Preparar exemplos concretos que comprovem as competências "
        "priorizadas no currículo."
    )

    guidance.append(
        "Quando questionado sobre um gap real, responder com transparência "
        "e demonstrar competências transferíveis ou plano de desenvolvimento."
    )

    return _unique(
        guidance
    )


# =========================================================
# SCORE DE TAILORING
# =========================================================

def _calculate_tailoring_score(
    ats_report: ATSReport,
) -> int:
    """
    Score indicativo de prontidão para customização.

    Não substitui o score ATS.
    """

    ats_score = _safe_int(
        _safe_attribute(
            ats_report,
            "score",
            0,
        ),
        0,
    )

    keyword_coverage = _safe_int(
        _safe_attribute(
            ats_report,
            "keyword_coverage",
            0,
        ),
        0,
    )

    mandatory_coverage = _safe_int(
        _safe_attribute(
            ats_report,
            "mandatory_coverage",
            0,
        ),
        0,
    )

    seniority_score = _safe_int(
        _safe_attribute(
            ats_report,
            "seniority_score",
            0,
        ),
        0,
    )

    tailoring_score = round(
        (
            ats_score * 0.40
            + keyword_coverage * 0.20
            + mandatory_coverage * 0.25
            + seniority_score * 0.15
        )
    )

    return max(
        0,
        min(
            100,
            tailoring_score,
        ),
    )


# =========================================================
# ENGINE PRINCIPAL
# =========================================================

def tailor_cv(
    profile_text: str,
    job_description: str,
    job_title: str,
    ats_report: ATSReport,
    recommendation_report: RecommendationReport,
) -> CVTailoringReport:
    """
    Gera estratégia de customização do currículo.

    Regras:
    - não inventar experiências;
    - não inventar competências;
    - não inventar resultados;
    - não alterar cargos ou formação;
    - utilizar apenas evidências existentes;
    - respeitar gaps identificados pelo ATS.
    """

    profile_text = _clean_text(
        profile_text
    )

    job_description = _clean_text(
        job_description
    )

    job_title = _clean_text(
        job_title
    )

    headline = _build_headline(
        job_title=job_title,
        ats_report=ats_report,
    )

    professional_summary = _build_professional_summary(
        profile_text=profile_text,
        job_title=job_title,
        ats_report=ats_report,
    )

    priority_skills = _build_priority_skills(
        ats_report=ats_report,
    )

    ats_keywords = _build_ats_keywords(
        ats_report=ats_report,
    )

    evidence_to_highlight = _build_evidence_to_highlight(
        profile_text=profile_text,
        ats_report=ats_report,
    )

    gaps_to_respect = _build_gaps_to_respect(
        ats_report=ats_report,
    )

    editing_recommendations = _build_editing_recommendations(
        ats_report=ats_report,
        recommendation_report=recommendation_report,
    )

    interview_bridge = _build_interview_bridge(
        recommendation_report=recommendation_report,
    )

    tailoring_score = _calculate_tailoring_score(
        ats_report=ats_report,
    )

    return CVTailoringReport(
        headline=headline,
        professional_summary=professional_summary,
        priority_skills=priority_skills,
        ats_keywords=ats_keywords,
        evidence_to_highlight=evidence_to_highlight,
        gaps_to_respect=gaps_to_respect,
        editing_recommendations=editing_recommendations,
        interview_bridge=interview_bridge,
        tailoring_score=tailoring_score,
    )
