from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# =========================================================
# IMPORTS COMPATÍVEIS
# =========================================================

try:
    from .curator_engine import (
        analyze_compatibility,
        detect_required_skills,
    )
    from .profile_engine import build_professional_profile

except ImportError:
    from curator_engine import (
        analyze_compatibility,
        detect_required_skills,
    )
    from profile_engine import build_professional_profile


# =========================================================
# MODELOS
# =========================================================

@dataclass
class ATSRequirementResult:
    skill: str
    category: str
    priority: str
    status: str
    weight: float


@dataclass
class ATSReport:
    score: int
    classification: str
    keyword_coverage: int
    mandatory_coverage: int
    preferred_coverage: int
    seniority_score: int | None
    requirements_found: int
    requirements_total: int
    mandatory_gaps: list[str]
    preferred_gaps: list[str]
    strengths: list[str]
    requirements: list[ATSRequirementResult]
    category_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "classification": self.classification,
            "keyword_coverage": self.keyword_coverage,
            "mandatory_coverage": self.mandatory_coverage,
            "preferred_coverage": self.preferred_coverage,
            "seniority_score": self.seniority_score,
            "requirements_found": self.requirements_found,
            "requirements_total": self.requirements_total,
            "mandatory_gaps": self.mandatory_gaps,
            "preferred_gaps": self.preferred_gaps,
            "strengths": self.strengths,
            "requirements": [
                {
                    "skill": item.skill,
                    "category": item.category,
                    "priority": item.priority,
                    "status": item.status,
                    "weight": item.weight,
                }
                for item in self.requirements
            ],
            "category_summary": self.category_summary,
        }


# =========================================================
# EQUIVALÊNCIAS PROFISSIONAIS
# =========================================================
#
# Estas equivalências não inventam competências.
# Apenas reconhecem termos equivalentes já identificados
# pelo Profile Engine.
# =========================================================

PROFILE_EQUIVALENCES = {
    "Gestão de Operações": {
        "areas": [
            "Operações",
            "Gestão de Operações",
        ],
        "management_skills": [
            "Gestão de Operações",
            "Gestão Operacional",
        ],
    },

    "Gestão de Projetos": {
        "areas": [
            "Gestão de Projetos",
            "Projetos",
        ],
        "management_skills": [
            "Gestão de Projetos",
        ],
    },

    "Gestão de Stakeholders": {
        "management_skills": [
            "Gestão de Stakeholders",
        ],
    },

    "Gestão de Processos": {
        "management_skills": [
            "Gestão de Processos",
        ],
        "evidence_terms": [
            "Melhoria",
            "Processos",
        ],
    },

    "Agile": {
        "methodologies": [
            "Agile",
            "Scrum",
            "Kanban",
        ],
    },

    "Scrum": {
        "methodologies": [
            "Scrum",
        ],
    },

    "Kanban": {
        "methodologies": [
            "Kanban",
        ],
    },

    "Inglês": {
        "languages": [
            "Inglês",
            "English",
        ],
    },

    "Espanhol": {
        "languages": [
            "Espanhol",
            "Spanish",
        ],
    },

    "Python": {
        "hard_skills": [
            "Python",
        ],
        "tools": [
            "Python",
        ],
    },

    "SQL": {
        "hard_skills": [
            "SQL",
        ],
        "tools": [
            "SQL",
        ],
    },

    "Power BI": {
        "tools": [
            "Power BI",
        ],
    },

    "Excel": {
        "tools": [
            "Excel",
        ],
    },

    "Pandas": {
        "hard_skills": [
            "Pandas",
        ],
        "tools": [
            "Pandas",
        ],
    },

    "Business Intelligence": {
        "areas": [
            "Business Intelligence",
        ],
        "hard_skills": [
            "Business Intelligence",
        ],
    },

    "Data Analytics": {
        "areas": [
            "Data Analytics",
        ],
        "hard_skills": [
            "Data Analytics",
        ],
    },

    "Machine Learning": {
        "hard_skills": [
            "Machine Learning",
        ],
    },

    "Dashboards": {
        "hard_skills": [
            "Dashboards",
        ],
    },

    "KPIs": {
        "hard_skills": [
            "KPIs",
        ],
        "management_skills": [
            "Gestão de Indicadores",
        ],
        "evidence_terms": [
            "Indicadores",
            "Performance",
        ],
    },

    "Automação": {
        "hard_skills": [
            "Automação",
        ],
    },

    "Inteligência Artificial": {
        "areas": [
            "Inteligência Artificial",
        ],
        "hard_skills": [
            "Inteligência Artificial",
        ],
    },

    "Marketing": {
        "areas": [
            "Marketing",
        ],
    },

    "CRM": {
        "areas": [
            "CRM",
        ],
    },

    "Vendas": {
        "areas": [
            "Vendas",
        ],
    },

    "Liderança": {
        "management_skills": [
            "Liderança",
            "Gestão de Equipes",
        ],
    },

    "Gestão de Equipes": {
        "management_skills": [
            "Gestão de Equipes",
            "Liderança",
        ],
    },
}


# =========================================================
# HELPERS
# =========================================================

def _normalize(
    value: str,
) -> str:
    return (
        str(value)
        .strip()
        .casefold()
    )


def _contains_equivalent(
    source_items: list[str],
    expected_items: list[str],
) -> bool:

    source = {
        _normalize(item)
        for item in source_items
        if item
    }

    expected = {
        _normalize(item)
        for item in expected_items
        if item
    }

    return bool(
        source.intersection(
            expected
        )
    )


def _profile_supports_skill(
    skill: str,
    structured_profile: Any,
) -> bool:
    """
    Verifica se o Profile Engine já identificou
    evidência equivalente ao requisito.
    """

    mapping = PROFILE_EQUIVALENCES.get(
        skill
    )

    if not mapping:
        return False

    for (
        profile_field,
        accepted_values,
    ) in mapping.items():

        source_values = getattr(
            structured_profile,
            profile_field,
            [],
        ) or []

        if _contains_equivalent(
            source_values,
            accepted_values,
        ):
            return True

    return False


def _coverage(
    items: list[ATSRequirementResult],
) -> int:

    if not items:
        return 0

    attended = sum(
        1
        for item in items
        if item.status == "Atende"
    )

    return round(
        attended
        / len(items)
        * 100
    )


def _classify_ats(
    score: int,
) -> str:

    if score >= 85:
        return "Muito forte"

    if score >= 70:
        return "Forte"

    if score >= 55:
        return "Competitivo"

    if score >= 40:
        return "Parcial"

    return "Baixo"


def _build_category_summary(
    requirements: list[ATSRequirementResult],
) -> dict[str, Any]:

    result: dict[str, Any] = {}

    categories = sorted(
        {
            item.category
            for item in requirements
        }
    )

    for category in categories:

        category_items = [
            item
            for item in requirements
            if item.category == category
        ]

        total = len(
            category_items
        )

        attended = sum(
            1
            for item in category_items
            if item.status == "Atende"
        )

        score = (
            round(
                attended
                / total
                * 100
            )
            if total
            else 0
        )

        result[category] = {
            "attended": attended,
            "total": total,
            "score": score,
        }

    return result


# =========================================================
# SENIORIDADE
# =========================================================

def _get_seniority_score(
    curator_result: dict[str, Any],
    structured_profile: Any,
) -> int | None:
    """
    Prioriza o score já calculado pelo Curator 2.0.

    Caso ele não esteja disponível, utiliza
    a senioridade detectada pelo Profile Engine
    apenas como fallback defensivo.
    """

    score_details = curator_result.get(
        "score_details",
        {},
    )

    seniority_score = score_details.get(
        "seniority_score"
    )

    if seniority_score is not None:

        try:
            return int(
                seniority_score
            )

        except (
            TypeError,
            ValueError,
        ):
            pass

    profile_seniority = getattr(
        structured_profile,
        "seniority",
        None,
    )

    if profile_seniority:

        normalized = _normalize(
            profile_seniority
        )

        if normalized in {
            "gerencial",
            "executiva / direção",
            "executiva / direcao",
            "coordenação",
            "coordenacao",
            "sênior / especialista",
            "senior / especialista",
        }:
            return 100

    return None


# =========================================================
# ATS ANALYSIS
# =========================================================

def analyze_ats(
    profile: str,
    job_description: str,
) -> ATSReport:
    """
    Avalia a aderência do currículo à oportunidade
    sob perspectiva ATS.

    Combina:

    - matching textual do Curator 2.0;
    - perfil estruturado do Profile Engine;
    - equivalências profissionais controladas;
    - requisitos obrigatórios;
    - diferenciais;
    - senioridade;
    - cobertura por categoria.
    """

    # =====================================================
    # PROFILE ENGINE
    # =====================================================

    structured_profile = (
        build_professional_profile(
            profile
        )
    )

    # =====================================================
    # CURATOR
    # =====================================================

    curator_result = (
        analyze_compatibility(
            profile=profile,
            job_description=job_description,
        )
    )

    # =====================================================
    # REQUISITOS DA VAGA
    # =====================================================

    detected_requirements = (
        detect_required_skills(
            job_description
        )
    )

    match_map = {
        item.skill: item
        for item
        in curator_result["matches"]
    }

    requirement_results: list[
        ATSRequirementResult
    ] = []

    for requirement in detected_requirements:

        match = match_map.get(
            requirement.skill
        )

        textual_match = (
            match is not None
            and match.status == "Atende"
        )

        semantic_profile_match = (
            _profile_supports_skill(
                requirement.skill,
                structured_profile,
            )
        )

        if (
            textual_match
            or semantic_profile_match
        ):
            status = "Atende"

        else:
            status = (
                "Não identificado no perfil"
            )

        requirement_results.append(
            ATSRequirementResult(
                skill=requirement.skill,
                category=requirement.category,
                priority=requirement.priority,
                status=status,
                weight=requirement.weight,
            )
        )

    # =====================================================
    # GRUPOS DE REQUISITOS
    # =====================================================

    mandatory_items = [
        item
        for item in requirement_results
        if item.priority == "Obrigatório"
    ]

    preferred_items = [
        item
        for item in requirement_results
        if item.priority == "Diferencial"
    ]

    # =====================================================
    # COBERTURA
    # =====================================================

    keyword_coverage = _coverage(
        requirement_results
    )

    mandatory_coverage = _coverage(
        mandatory_items
    )

    preferred_coverage = _coverage(
        preferred_items
    )

    # =====================================================
    # SENIORIDADE
    # =====================================================

    seniority_score = (
        _get_seniority_score(
            curator_result=curator_result,
            structured_profile=structured_profile,
        )
    )

    # =====================================================
    # SCORE ATS
    # =====================================================

    components: list[float] = []
    weights: list[float] = []

    if requirement_results:

        components.append(
            keyword_coverage
        )

        weights.append(
            0.35
        )

    if mandatory_items:

        components.append(
            mandatory_coverage
        )

        weights.append(
            0.45
        )

    if preferred_items:

        components.append(
            preferred_coverage
        )

        weights.append(
            0.10
        )

    if seniority_score is not None:

        components.append(
            seniority_score
        )

        weights.append(
            0.10
        )

    if not components:

        final_score = 0

    else:

        weighted_total = sum(
            component * weight
            for component, weight
            in zip(
                components,
                weights,
            )
        )

        total_weight = sum(
            weights
        )

        final_score = round(
            weighted_total
            / total_weight
        )

    # Evita falsa certeza absoluta.
    final_score = min(
        final_score,
        98,
    )

    classification = (
        _classify_ats(
            final_score
        )
    )

    # =====================================================
    # FORÇAS
    # =====================================================

    strengths = [
        item.skill
        for item
        in requirement_results
        if item.status == "Atende"
    ]

    # =====================================================
    # GAPS OBRIGATÓRIOS
    # =====================================================

    mandatory_gaps = [
        item.skill
        for item
        in mandatory_items
        if item.status != "Atende"
    ]

    # =====================================================
    # GAPS DIFERENCIAIS
    # =====================================================

    preferred_gaps = [
        item.skill
        for item
        in preferred_items
        if item.status != "Atende"
    ]

    # =====================================================
    # CONTAGEM
    # =====================================================

    requirements_found = len(
        strengths
    )

    requirements_total = len(
        requirement_results
    )

    # =====================================================
    # CATEGORIAS
    # =====================================================

    category_summary = (
        _build_category_summary(
            requirement_results
        )
    )

    # =====================================================
    # RESULTADO
    # =====================================================

    return ATSReport(
        score=final_score,
        classification=classification,
        keyword_coverage=keyword_coverage,
        mandatory_coverage=mandatory_coverage,
        preferred_coverage=preferred_coverage,
        seniority_score=seniority_score,
        requirements_found=requirements_found,
        requirements_total=requirements_total,
        mandatory_gaps=mandatory_gaps,
        preferred_gaps=preferred_gaps,
        strengths=strengths,
        requirements=requirement_results,
        category_summary=category_summary,
    )
