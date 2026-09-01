from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# =========================================================
# IMPORT COMPATÍVEL
# =========================================================

try:
    from .ats_engine import ATSReport
except ImportError:
    from ats_engine import ATSReport


# =========================================================
# MODELOS
# =========================================================

@dataclass
class CareerRecommendation:
    title: str
    category: str
    priority: str
    action: str
    rationale: str


@dataclass
class RecommendationReport:
    recommendations: list[CareerRecommendation]
    priority_actions: list[str]
    positioning_guidance: list[str]
    interview_guidance: list[str]
    cv_guidance: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendations": [
                {
                    "title": item.title,
                    "category": item.category,
                    "priority": item.priority,
                    "action": item.action,
                    "rationale": item.rationale,
                }
                for item in self.recommendations
            ],
            "priority_actions": self.priority_actions,
            "positioning_guidance": self.positioning_guidance,
            "interview_guidance": self.interview_guidance,
            "cv_guidance": self.cv_guidance,
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
        normalized = item.strip()

        if not normalized:
            continue

        key = normalized.casefold()

        if key not in seen:
            seen.add(key)
            result.append(normalized)

    return result


def _add_recommendation(
    recommendations: list[CareerRecommendation],
    title: str,
    category: str,
    priority: str,
    action: str,
    rationale: str,
):
    recommendations.append(
        CareerRecommendation(
            title=title,
            category=category,
            priority=priority,
            action=action,
            rationale=rationale,
        )
    )


# =========================================================
# RECOMMENDATION ENGINE
# =========================================================

def build_recommendations(
    ats_report: ATSReport,
) -> RecommendationReport:
    """
    Converte o diagnóstico ATS em recomendações acionáveis.

    O motor não inventa experiência nem competências.

    Ele trabalha apenas com:
    - forças identificadas;
    - gaps obrigatórios;
    - gaps diferenciais;
    - senioridade;
    - cobertura;
    - distribuição por categorias.
    """

    recommendations: list[CareerRecommendation] = []

    priority_actions: list[str] = []
    positioning_guidance: list[str] = []
    interview_guidance: list[str] = []
    cv_guidance: list[str] = []

    # =====================================================
    # GAPS OBRIGATÓRIOS
    # =====================================================

    if ats_report.mandatory_gaps:

        for skill in ats_report.mandatory_gaps:

            _add_recommendation(
                recommendations=recommendations,
                title=f"Reforçar evidência de {skill}",
                category="Gap obrigatório",
                priority="Alta",
                action=(
                    f"Verifique se existe experiência real relacionada a "
                    f"{skill} no histórico profissional. Caso exista, "
                    f"explicite essa experiência no currículo com contexto, "
                    f"responsabilidade e resultado. Caso não exista, não "
                    f"inclua a competência apenas para aumentar o score."
                ),
                rationale=(
                    f"{skill} foi identificado como requisito obrigatório "
                    f"da oportunidade, mas não há evidência suficiente no "
                    f"perfil analisado."
                ),
            )

            priority_actions.append(
                f"Revisar a evidência de {skill} antes da candidatura."
            )

            cv_guidance.append(
                f"Se houver experiência comprovável em {skill}, "
                f"dar maior visibilidade a essa competência no currículo."
            )

            interview_guidance.append(
                f"Prepare uma resposta objetiva sobre sua experiência "
                f"com {skill}, caso possua evidências reais."
            )

    # =====================================================
    # GAPS DIFERENCIAIS
    # =====================================================

    if ats_report.preferred_gaps:

        for skill in ats_report.preferred_gaps:

            _add_recommendation(
                recommendations=recommendations,
                title=f"Avaliar diferencial: {skill}",
                category="Diferencial",
                priority="Média",
                action=(
                    f"Avalie se {skill} já faz parte da sua experiência "
                    f"ou formação. Se sim, torne essa evidência mais explícita. "
                    f"Se não, trate como oportunidade de desenvolvimento, "
                    f"sem comprometer a veracidade do currículo."
                ),
                rationale=(
                    f"{skill} aparece como diferencial da vaga e pode "
                    f"aumentar a competitividade da candidatura."
                ),
            )

            cv_guidance.append(
                f"Destacar {skill} somente se houver evidência real."
            )

    # =====================================================
    # FORÇAS
    # =====================================================

    if ats_report.strengths:

        strongest = ats_report.strengths[:5]

        positioning_guidance.append(
            "Posicionar a candidatura principalmente sobre as competências "
            "já comprovadas: "
            + ", ".join(strongest)
            + "."
        )

        cv_guidance.append(
            "Manter as competências mais aderentes à vaga nas áreas de maior "
            "visibilidade do currículo."
        )

        interview_guidance.append(
            "Utilizar exemplos concretos relacionados às principais "
            "competências aderentes, conectando situação, ação e resultado."
        )

    # =====================================================
    # COBERTURA ATS
    # =====================================================

    if ats_report.keyword_coverage < 50:

        _add_recommendation(
            recommendations=recommendations,
            title="Aumentar cobertura de requisitos",
            category="ATS",
            priority="Alta",
            action=(
                "Revisar o currículo com foco nos requisitos efetivamente "
                "presentes na vaga. Priorize competências já existentes no "
                "histórico profissional e torne sua redação mais alinhada "
                "à linguagem da oportunidade."
            ),
            rationale=(
                f"A cobertura geral identificada foi de "
                f"{ats_report.keyword_coverage}%."
            ),
        )

        priority_actions.append(
            "Aumentar a cobertura de requisitos antes da candidatura."
        )

    elif ats_report.keyword_coverage < 70:

        _add_recommendation(
            recommendations=recommendations,
            title="Melhorar aderência textual",
            category="ATS",
            priority="Média",
            action=(
                "Ajustar a redação do currículo para refletir de forma mais "
                "direta competências e responsabilidades que já fazem parte "
                "da experiência profissional."
            ),
            rationale=(
                f"A cobertura geral de {ats_report.keyword_coverage}% "
                f"indica aderência relevante, mas ainda com espaço "
                f"para melhor alinhamento."
            ),
        )

    else:

        positioning_guidance.append(
            "A cobertura de requisitos está em nível competitivo. "
            "Priorize qualidade de evidência e resultados, em vez de "
            "simplesmente adicionar mais palavras-chave."
        )

    # =====================================================
    # REQUISITOS OBRIGATÓRIOS
    # =====================================================

    if ats_report.mandatory_coverage < 50:

        _add_recommendation(
            recommendations=recommendations,
            title="Reavaliar viabilidade da candidatura",
            category="Estratégia",
            priority="Alta",
            action=(
                "Avalie cuidadosamente se a oportunidade é prioritária. "
                "Uma cobertura baixa de requisitos obrigatórios pode indicar "
                "que outra vaga tenha maior aderência ao perfil atual."
            ),
            rationale=(
                f"A cobertura de requisitos obrigatórios foi de "
                f"{ats_report.mandatory_coverage}%."
            ),
        )

        priority_actions.append(
            "Reavaliar a candidatura diante dos gaps obrigatórios."
        )

    elif ats_report.mandatory_coverage < 80:

        positioning_guidance.append(
            "A candidatura possui base competitiva, mas os requisitos "
            "obrigatórios ainda devem ser revisados individualmente."
        )

    else:

        positioning_guidance.append(
            "A cobertura de requisitos obrigatórios é forte. "
            "A candidatura pode concentrar a narrativa em diferenciação "
            "e resultados."
        )

    # =====================================================
    # SENIORIDADE
    # =====================================================

    if ats_report.seniority_score is not None:

        if ats_report.seniority_score >= 85:

            positioning_guidance.append(
                "A senioridade identificada está bem alinhada à oportunidade."
            )

        elif ats_report.seniority_score >= 60:

            positioning_guidance.append(
                "A senioridade apresenta aderência parcial. "
                "É importante evidenciar escopo, autonomia, liderança "
                "e complexidade das responsabilidades exercidas."
            )

            cv_guidance.append(
                "Dar maior destaque ao nível de responsabilidade e "
                "complexidade das experiências mais relevantes."
            )

        else:

            _add_recommendation(
                recommendations=recommendations,
                title="Revisar aderência de senioridade",
                category="Senioridade",
                priority="Alta",
                action=(
                    "Avaliar se o nível da posição é compatível com a "
                    "experiência atual. Caso exista experiência equivalente, "
                    "torne explícitos escopo, autonomia, liderança e impacto."
                ),
                rationale=(
                    f"O score de senioridade foi de "
                    f"{ats_report.seniority_score}%."
                ),
            )

    # =====================================================
    # CATEGORIAS
    # =====================================================

    for category, summary in ats_report.category_summary.items():

        category_score = summary.get(
            "score",
            0,
        )

        total = summary.get(
            "total",
            0,
        )

        if not total:
            continue

        if category_score < 50:

            _add_recommendation(
                recommendations=recommendations,
                title=f"Reforçar dimensão: {category}",
                category="Dimensão profissional",
                priority="Média",
                action=(
                    f"Revisar as evidências relacionadas à dimensão "
                    f"{category}. Se houver experiência real, ela deve "
                    f"ser descrita de forma mais explícita no currículo."
                ),
                rationale=(
                    f"A aderência na categoria {category} foi de "
                    f"{category_score}%."
                ),
            )

    # =====================================================
    # SCORE GLOBAL
    # =====================================================

    if ats_report.score >= 85:

        positioning_guidance.append(
            "O perfil apresenta aderência muito forte à oportunidade. "
            "A estratégia deve concentrar-se em diferenciação, resultados "
            "e narrativa executiva."
        )

    elif ats_report.score >= 70:

        positioning_guidance.append(
            "O perfil apresenta boa competitividade. "
            "Recomenda-se uma candidatura customizada e focada nas "
            "competências mais aderentes."
        )

    elif ats_report.score >= 55:

        positioning_guidance.append(
            "O perfil é competitivo, mas exige customização do currículo "
            "e preparação específica para a oportunidade."
        )

    elif ats_report.score >= 40:

        positioning_guidance.append(
            "A aderência é parcial. A decisão de candidatura deve considerar "
            "a relevância dos gaps obrigatórios e o potencial de transferência "
            "de competências."
        )

    else:

        positioning_guidance.append(
            "A aderência atual é baixa. Pode ser mais eficiente priorizar "
            "oportunidades com maior compatibilidade."
        )

    # =====================================================
    # AÇÕES PADRÃO
    # =====================================================

    cv_guidance.append(
        "Evitar incluir competências ou resultados que não estejam "
        "comprovados pela experiência profissional."
    )

    cv_guidance.append(
        "Priorizar resultados, indicadores, escopo e impacto nas "
        "experiências mais aderentes à vaga."
    )

    interview_guidance.append(
        "Preparar exemplos reais para os principais requisitos da vaga, "
        "especialmente os obrigatórios."
    )

    interview_guidance.append(
        "Para gaps reais, preparar uma resposta transparente que demonstre "
        "capacidade de aprendizado e competências transferíveis."
    )

    priority_actions = _unique(
        priority_actions
    )

    positioning_guidance = _unique(
        positioning_guidance
    )

    interview_guidance = _unique(
        interview_guidance
    )

    cv_guidance = _unique(
        cv_guidance
    )

    return RecommendationReport(
        recommendations=recommendations,
        priority_actions=priority_actions,
        positioning_guidance=positioning_guidance,
        interview_guidance=interview_guidance,
        cv_guidance=cv_guidance,
    )
