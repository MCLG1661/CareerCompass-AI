from __future__ import annotations

from dataclasses import dataclass


SKILLS = {
    "Python": ["python"],
    "SQL": ["sql"],
    "Power BI": ["power bi", "powerbi"],
    "Excel": ["excel"],
    "Pandas": ["pandas"],
    "Scikit-Learn": ["scikit-learn", "sklearn"],
    "Machine Learning": ["machine learning"],
    "Data Analytics": ["data analytics", "análise de dados", "analise de dados"],
    "Business Intelligence": [
        "business intelligence",
        "bi",
    ],
    "ETL": ["etl"],
    "Modelagem de Dados": [
        "modelagem de dados",
        "data modeling",
        "modelo dimensional",
        "esquema estrela",
    ],
    "Dashboards": [
        "dashboard",
        "dashboards",
        "painel",
        "painéis",
    ],
}


@dataclass
class SkillMatch:
    skill: str
    status: str


def contains_any(text: str, terms: list[str]) -> bool:
    text = text.lower()
    return any(term.lower() in text for term in terms)


def analyze_compatibility(profile: str, job_description: str) -> dict:
    profile_lower = profile.lower()
    job_lower = job_description.lower()

    required_skills = []

    for skill, aliases in SKILLS.items():
        if contains_any(job_lower, aliases):
            required_skills.append(skill)

    matches: list[SkillMatch] = []

    for skill in required_skills:
        aliases = SKILLS[skill]

        if contains_any(profile_lower, aliases):
            matches.append(
                SkillMatch(
                    skill=skill,
                    status="Atende",
                )
            )
        else:
            matches.append(
                SkillMatch(
                    skill=skill,
                    status="Não identificado no perfil",
                )
            )

    if required_skills:
        attended = sum(
            1 for item in matches if item.status == "Atende"
        )
        score = round((attended / len(required_skills)) * 100)
    else:
        score = 0

    if score >= 75:
        compatibility = "Alta"
    elif score >= 50:
        compatibility = "Média"
    else:
        compatibility = "Baixa"

    strengths = [
        item.skill
        for item in matches
        if item.status == "Atende"
    ]

    gaps = [
        item.skill
        for item in matches
        if item.status != "Atende"
    ]

    return {
        "score": score,
        "compatibility": compatibility,
        "matches": matches,
        "strengths": strengths,
        "gaps": gaps,
    }
