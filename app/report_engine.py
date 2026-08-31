from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# =========================================================
# MODELO DO RELATÓRIO
# =========================================================

@dataclass
class CareerReport:
    generated_at: str
    candidate_name: str
    source_name: str
    seniority: str

    executive_summary: str = ""

    areas: list[str] = field(default_factory=list)
    hard_skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    management_skills: list[str] = field(default_factory=list)
    methodologies: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    evidence_terms: list[str] = field(default_factory=list)

    strengths: list[str] = field(default_factory=list)
    attention_points: list[str] = field(default_factory=list)

    recommended_roles: list[dict[str, Any]] = field(
        default_factory=list
    )

    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "candidate_name": self.candidate_name,
            "source_name": self.source_name,
            "seniority": self.seniority,
            "executive_summary": self.executive_summary,
            "areas": self.areas,
            "hard_skills": self.hard_skills,
            "tools": self.tools,
            "management_skills": self.management_skills,
            "methodologies": self.methodologies,
            "languages": self.languages,
            "evidence_terms": self.evidence_terms,
            "strengths": self.strengths,
            "attention_points": self.attention_points,
            "recommended_roles": self.recommended_roles,
            "recommendations": self.recommendations,
        }


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def _safe_list(value: Any) -> list[str]:
    if not value:
        return []

    if isinstance(value, list):
        return [
            str(item)
            for item in value
            if item
        ]

    if isinstance(value, tuple):
        return [
            str(item)
            for item in value
            if item
        ]

    return [str(value)]


def _unique(items: list[str]) -> list[str]:
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


def _get_attribute(
    profile: Any,
    name: str,
    default: Any = None,
) -> Any:

    if isinstance(profile, dict):
        return profile.get(name, default)

    return getattr(
        profile,
        name,
        default,
    )


# =========================================================
# IDENTIFICAÇÃO DO CANDIDATO
# =========================================================

def _resolve_candidate_name(
    structured_profile: Any,
    candidate_name: str | None = None,
) -> str:
    """
    Prioridade:

    1. Nome explicitamente informado pelo consultor.
    2. Nome identificado pelo Profile Engine.
    3. Fallback seguro: Candidato.
    """

    if candidate_name:
        candidate_name = candidate_name.strip()

        if (
            candidate_name
            and candidate_name.casefold() != "candidato"
        ):
            return candidate_name

    detected_name = str(
        _get_attribute(
            structured_profile,
            "candidate_name",
            "",
        )
        or ""
    ).strip()

    if (
        detected_name
        and detected_name.casefold() != "candidato"
    ):
        return detected_name

    return "Candidato"


# =========================================================
# RESUMO EXECUTIVO
# =========================================================

def _build_executive_summary(
    structured_profile: Any,
) -> str:

    seniority = str(
        _get_attribute(
            structured_profile,
            "seniority",
            "Não identificada",
        )
    )

    areas = _safe_list(
        _get_attribute(
            structured_profile,
            "areas",
            [],
        )
    )

    hard_skills = _safe_list(
        _get_attribute(
            structured_profile,
            "hard_skills",
            [],
        )
    )

    management_skills = _safe_list(
        _get_attribute(
            structured_profile,
            "management_skills",
            [],
        )
    )

    evidence_terms = _safe_list(
        _get_attribute(
            structured_profile,
            "evidence_terms",
            [],
        )
    )

    paragraphs = []

    # -----------------------------------------------------
    # Perfil principal
    # -----------------------------------------------------

    if areas:
        primary_areas = ", ".join(
            areas[:4]
        )

        if seniority != "Não identificada":
            paragraphs.append(
                f"O perfil analisado apresenta senioridade "
                f"{seniority.lower()}, com experiência identificada "
                f"principalmente em {primary_areas}."
            )

        else:
            paragraphs.append(
                f"O perfil analisado demonstra experiência "
                f"principalmente em {primary_areas}."
            )

    elif seniority != "Não identificada":
        paragraphs.append(
            f"O perfil apresenta senioridade "
            f"{seniority.lower()} com trajetória profissional "
            f"compatível com posições de maior responsabilidade."
        )

    else:
        paragraphs.append(
            "O perfil profissional foi analisado a partir das "
            "informações disponíveis no currículo."
        )

    # -----------------------------------------------------
    # Combinação gestão + técnica
    # -----------------------------------------------------

    if management_skills and hard_skills:
        technical = ", ".join(
            hard_skills[:4]
        )

        paragraphs.append(
            "Um dos principais elementos do perfil é a combinação "
            "entre competências de gestão e capacidades analíticas "
            f"e técnicas, com evidências em {technical}."
        )

    elif hard_skills:
        technical = ", ".join(
            hard_skills[:5]
        )

        paragraphs.append(
            f"A base técnica identificada inclui {technical}, "
            "ampliando o repertório profissional para funções "
            "orientadas por dados e tecnologia."
        )

    elif management_skills:
        management = ", ".join(
            management_skills[:4]
        )

        paragraphs.append(
            f"As competências de gestão identificadas incluem "
            f"{management}."
        )

    # -----------------------------------------------------
    # Evidências
    # -----------------------------------------------------

    if evidence_terms:
        paragraphs.append(
            "O currículo também apresenta evidências relacionadas "
            "a resultados, indicadores e performance, elemento "
            "relevante para fortalecer a narrativa profissional "
            "em processos seletivos."
        )

    return " ".join(paragraphs)


# =========================================================
# FORÇAS
# =========================================================

def _build_strengths(
    structured_profile: Any,
) -> list[str]:

    strengths = []

    areas = _safe_list(
        _get_attribute(
            structured_profile,
            "areas",
            [],
        )
    )

    hard_skills = _safe_list(
        _get_attribute(
            structured_profile,
            "hard_skills",
            [],
        )
    )

    tools = _safe_list(
        _get_attribute(
            structured_profile,
            "tools",
            [],
        )
    )

    management_skills = _safe_list(
        _get_attribute(
            structured_profile,
            "management_skills",
            [],
        )
    )

    evidence_terms = _safe_list(
        _get_attribute(
            structured_profile,
            "evidence_terms",
            [],
        )
    )

    if areas:
        strengths.append(
            "Experiência multidisciplinar identificada em "
            + ", ".join(areas[:5])
            + "."
        )

    if management_skills:
        strengths.append(
            "Competências de gestão e liderança identificadas em "
            + ", ".join(management_skills[:5])
            + "."
        )

    if hard_skills:
        strengths.append(
            "Base analítica e técnica identificada em "
            + ", ".join(hard_skills[:6])
            + "."
        )

    if tools:
        strengths.append(
            "Familiaridade com ferramentas e tecnologias como "
            + ", ".join(tools[:6])
            + "."
        )

    if management_skills and hard_skills:
        strengths.append(
            "Combinação entre visão de gestão e competências "
            "analíticas, característica relevante para funções "
            "que conectam negócio, dados e tecnologia."
        )

    if evidence_terms:
        strengths.append(
            "O currículo apresenta evidências associadas a "
            "resultados, indicadores, performance e impacto "
            "profissional."
        )

    return _unique(strengths)


# =========================================================
# PONTOS DE ATENÇÃO
# =========================================================

def _build_attention_points(
    structured_profile: Any,
) -> list[str]:

    points = []

    areas = _safe_list(
        _get_attribute(
            structured_profile,
            "areas",
            [],
        )
    )

    hard_skills = _safe_list(
        _get_attribute(
            structured_profile,
            "hard_skills",
            [],
        )
    )

    methodologies = _safe_list(
        _get_attribute(
            structured_profile,
            "methodologies",
            [],
        )
    )

    languages = _safe_list(
        _get_attribute(
            structured_profile,
            "languages",
            [],
        )
    )

    evidence_terms = _safe_list(
        _get_attribute(
            structured_profile,
            "evidence_terms",
            [],
        )
    )

    if len(hard_skills) < 3:
        points.append(
            "O currículo apresenta poucas hard skills "
            "explicitamente identificáveis. Vale revisar a "
            "descrição das competências técnicas."
        )

    if not methodologies:
        points.append(
            "Não foram identificadas metodologias profissionais "
            "de forma explícita no currículo."
        )

    if not languages:
        points.append(
            "Não foram identificados idiomas de forma estruturada."
        )

    if not evidence_terms:
        points.append(
            "Há pouca evidência textual de resultados mensuráveis. "
            "Considere reforçar indicadores, volumes, percentuais "
            "e impactos."
        )

    if len(areas) >= 6:
        points.append(
            "O perfil apresenta amplitude relevante de áreas de "
            "atuação. Em candidaturas específicas, recomenda-se "
            "priorizar as experiências diretamente relacionadas "
            "à posição-alvo para preservar clareza de posicionamento."
        )

    if not points:
        points.append(
            "O perfil apresenta boa cobertura das dimensões "
            "analisadas. A próxima etapa é avaliar a aderência "
            "às oportunidades-alvo."
        )

    return _unique(points)


# =========================================================
# RECOMENDAÇÕES
# =========================================================

def _build_recommendations(
    structured_profile: Any,
) -> list[str]:

    recommendations = []

    seniority = str(
        _get_attribute(
            structured_profile,
            "seniority",
            "Não identificada",
        )
    )

    areas = _safe_list(
        _get_attribute(
            structured_profile,
            "areas",
            [],
        )
    )

    management_skills = _safe_list(
        _get_attribute(
            structured_profile,
            "management_skills",
            [],
        )
    )

    evidence_terms = _safe_list(
        _get_attribute(
            structured_profile,
            "evidence_terms",
            [],
        )
    )

    if (
        seniority
        and seniority != "Não identificada"
    ):
        recommendations.append(
            f"Priorizar oportunidades compatíveis com a "
            f"senioridade identificada: {seniority}."
        )

    if areas:
        recommendations.append(
            "Direcionar a estratégia de candidatura para funções "
            "relacionadas às áreas com maior evidência no perfil, "
            "evitando posicionamento excessivamente genérico."
        )

    if len(areas) >= 6:
        recommendations.append(
            "Criar versões direcionadas do currículo para os "
            "principais eixos profissionais, destacando somente "
            "as experiências e competências mais aderentes a "
            "cada oportunidade."
        )

    if management_skills:
        recommendations.append(
            "Explorar no currículo e nas entrevistas exemplos "
            "concretos de liderança, gestão de stakeholders, "
            "tomada de decisão e condução de projetos."
        )

    if evidence_terms:
        recommendations.append(
            "Manter resultados, indicadores e impactos em destaque "
            "para aumentar a força da narrativa profissional."
        )

    else:
        recommendations.append(
            "Adicionar resultados mensuráveis às principais "
            "experiências profissionais sempre que possível."
        )

    recommendations.append(
        "Customizar o currículo para cada oportunidade relevante, "
        "priorizando competências e experiências aderentes à "
        "descrição da vaga."
    )

    recommendations.append(
        "Utilizar a Análise de Fit antes da candidatura para "
        "identificar aderências, lacunas e elementos que precisam "
        "ser reforçados."
    )

    recommendations.append(
        "Utilizar o Simulador de Entrevistas para transformar "
        "experiências profissionais em respostas estruturadas "
        "com contexto, ação e resultado."
    )

    return _unique(recommendations)


# =========================================================
# RESULTADOS DO SCOUT
# =========================================================

def _parse_scout_results(
    scout_results: Any,
) -> list[dict[str, Any]]:

    if not scout_results:
        return []

    parsed = []

    for result in scout_results[:5]:

        if isinstance(result, dict):
            title = result.get(
                "title",
                "",
            )

            score = result.get(
                "score",
                0,
            )

            level = result.get(
                "level",
                "",
            )

            reason = result.get(
                "reason",
                "",
            )

        else:
            title = getattr(
                result,
                "title",
                "",
            )

            score = getattr(
                result,
                "score",
                0,
            )

            level = getattr(
                result,
                "level",
                "",
            )

            reason = getattr(
                result,
                "reason",
                "",
            )

        if title:
            parsed.append(
                {
                    "title": title,
                    "score": score,
                    "level": level,
                    "reason": reason,
                }
            )

    return parsed


# =========================================================
# CONSTRUÇÃO DO RELATÓRIO
# =========================================================

def build_career_report(
    structured_profile: Any,
    candidate_name: str | None = None,
    source_name: str = "Perfil profissional",
    scout_results: Any = None,
) -> CareerReport:

    seniority = str(
        _get_attribute(
            structured_profile,
            "seniority",
            "Não identificada",
        )
    )

    resolved_candidate_name = _resolve_candidate_name(
        structured_profile,
        candidate_name,
    )

    return CareerReport(
        generated_at=datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        ),
        candidate_name=resolved_candidate_name,
        source_name=source_name,
        seniority=seniority,
        executive_summary=_build_executive_summary(
            structured_profile
        ),
        areas=_unique(
            _safe_list(
                _get_attribute(
                    structured_profile,
                    "areas",
                    [],
                )
            )
        ),
        hard_skills=_unique(
            _safe_list(
                _get_attribute(
                    structured_profile,
                    "hard_skills",
                    [],
                )
            )
        ),
        tools=_unique(
            _safe_list(
                _get_attribute(
                    structured_profile,
                    "tools",
                    [],
                )
            )
        ),
        management_skills=_unique(
            _safe_list(
                _get_attribute(
                    structured_profile,
                    "management_skills",
                    [],
                )
            )
        ),
        methodologies=_unique(
            _safe_list(
                _get_attribute(
                    structured_profile,
                    "methodologies",
                    [],
                )
            )
        ),
        languages=_unique(
            _safe_list(
                _get_attribute(
                    structured_profile,
                    "languages",
                    [],
                )
            )
        ),
        evidence_terms=_unique(
            _safe_list(
                _get_attribute(
                    structured_profile,
                    "evidence_terms",
                    [],
                )
            )
        ),
        strengths=_build_strengths(
            structured_profile
        ),
        attention_points=_build_attention_points(
            structured_profile
        ),
        recommended_roles=_parse_scout_results(
            scout_results
        ),
        recommendations=_build_recommendations(
            structured_profile
        ),
    )


# =========================================================
# EXPORTAÇÃO MARKDOWN
# =========================================================

def report_to_markdown(
    report: CareerReport,
) -> str:

    def bullet_list(
        items: list[str],
    ) -> str:

        if not items:
            return "- Não identificado"

        return "\n".join(
            f"- {item}"
            for item in items
        )

    roles = []

    for role in report.recommended_roles:
        roles.append(
            f"- **{role['title']}** — "
            f"{role['score']}% de aderência "
            f"({role['level']})"
        )

    roles_text = (
        "\n".join(roles)
        if roles
        else (
            "- Execute o Radar de Oportunidades "
            "para gerar recomendações."
        )
    )

    return f"""# Career Assessment Report

## CareerCompass AI

**Candidato:** {report.candidate_name}

**Fonte analisada:** {report.source_name}

**Data da análise:** {report.generated_at}

**Senioridade identificada:** {report.seniority}

---

## 1. Resumo Executivo

{report.executive_summary}

## 2. Áreas de Atuação

{bullet_list(report.areas)}

## 3. Hard Skills

{bullet_list(report.hard_skills)}

## 4. Ferramentas e Tecnologias

{bullet_list(report.tools)}

## 5. Competências de Gestão

{bullet_list(report.management_skills)}

## 6. Metodologias

{bullet_list(report.methodologies)}

## 7. Idiomas

{bullet_list(report.languages)}

## 8. Evidências Profissionais

{bullet_list(report.evidence_terms)}

## 9. Principais Forças

{bullet_list(report.strengths)}

## 10. Pontos de Atenção

{bullet_list(report.attention_points)}

## 11. Caminhos Profissionais

{roles_text}

## 12. Recomendações

{bullet_list(report.recommendations)}

---

*Relatório gerado pelo CareerCompass AI — Career Intelligence Platform.*
"""
