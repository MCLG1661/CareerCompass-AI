import re
from dataclasses import dataclass


@dataclass
class JobMatch:
    title: str
    score: int
    level: str
    reason: str


TARGET_ROLES = {
    "Analista de BI": [
        "power bi",
        "sql",
        "excel",
        "python",
        "pandas",
        "business intelligence",
        "dashboard",
        "dados",
    ],
    "Analista de Dados": [
        "python",
        "sql",
        "pandas",
        "excel",
        "power bi",
        "análise de dados",
        "data analytics",
        "dashboard",
    ],
    "Analista de Marketing": [
        "marketing",
        "analytics",
        "crm",
        "power bi",
        "dados",
        "campanhas",
        "kpi",
        "growth",
    ],
    "Gerente de Projetos": [
        "gestão de projetos",
        "project management",
        "stakeholders",
        "kpi",
        "operações",
        "cronograma",
        "gestão",
        "projetos",
    ],
    "Gerente de Operações": [
        "operações",
        "gestão",
        "kpi",
        "processos",
        "performance",
        "equipe",
        "indicadores",
        "projetos",
    ],
}


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def discover_roles(profile: str) -> list[JobMatch]:
    profile_normalized = normalize(profile)

    results = []

    for role, keywords in TARGET_ROLES.items():
        matches = [
            keyword
            for keyword in keywords
            if keyword in profile_normalized
        ]

        score = round(
            (len(matches) / len(keywords)) * 100
        )

        if score >= 75:
            level = "Forte aderência"
        elif score >= 50:
            level = "Boa aderência"
        elif score >= 25:
            level = "Aderência parcial"
        else:
            level = "Baixa aderência"

        if matches:
            reason = (
                "Competências encontradas: "
                + ", ".join(matches)
            )
        else:
            reason = (
                "Poucas evidências foram encontradas "
                "no perfil atual."
            )

        results.append(
            JobMatch(
                title=role,
                score=score,
                level=level,
                reason=reason,
            )
        )

    results.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    return results
