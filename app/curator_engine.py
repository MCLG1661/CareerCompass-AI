from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


# =========================================================
# MODELOS
# =========================================================

@dataclass
class SkillMatch:
    skill: str
    status: str
    category: str = ""
    priority: str = "Geral"
    weight: float = 1.0


@dataclass
class Requirement:
    skill: str
    category: str
    aliases: list[str]
    priority: str
    weight: float


# =========================================================
# VOCABULÁRIO
# =========================================================

SKILL_CATALOG = {
    # -----------------------------------------------------
    # HARD SKILLS
    # -----------------------------------------------------
    "Python": {
        "category": "Hard Skills",
        "aliases": [
            "python",
        ],
    },
    "SQL": {
        "category": "Hard Skills",
        "aliases": [
            "sql",
        ],
    },
    "Pandas": {
        "category": "Hard Skills",
        "aliases": [
            "pandas",
        ],
    },
    "Scikit-Learn": {
        "category": "Hard Skills",
        "aliases": [
            "scikit-learn",
            "sklearn",
        ],
    },
    "Machine Learning": {
        "category": "Hard Skills",
        "aliases": [
            "machine learning",
            "aprendizado de máquina",
            "aprendizado de maquina",
        ],
    },
    "Data Analytics": {
        "category": "Hard Skills",
        "aliases": [
            "data analytics",
            "análise de dados",
            "analise de dados",
        ],
    },
    "Business Intelligence": {
        "category": "Hard Skills",
        "aliases": [
            "business intelligence",
            "bi",
        ],
    },
    "ETL": {
        "category": "Hard Skills",
        "aliases": [
            "etl",
            "extract transform load",
        ],
    },
    "Modelagem de Dados": {
        "category": "Hard Skills",
        "aliases": [
            "modelagem de dados",
            "data modeling",
            "modelo dimensional",
            "esquema estrela",
            "star schema",
        ],
    },
    "Dashboards": {
        "category": "Hard Skills",
        "aliases": [
            "dashboard",
            "dashboards",
            "painel",
            "painéis",
            "paineis",
        ],
    },
    "KPIs": {
        "category": "Hard Skills",
        "aliases": [
            "kpi",
            "kpis",
            "indicadores de desempenho",
            "indicadores de performance",
        ],
    },
    "Automação": {
        "category": "Hard Skills",
        "aliases": [
            "automação",
            "automacao",
            "automation",
        ],
    },
    "Inteligência Artificial": {
        "category": "Hard Skills",
        "aliases": [
            "inteligência artificial",
            "inteligencia artificial",
            "artificial intelligence",
            "generative ai",
            "genai",
            "ia aplicada",
        ],
    },

    # -----------------------------------------------------
    # FERRAMENTAS
    # -----------------------------------------------------
    "Power BI": {
        "category": "Ferramentas",
        "aliases": [
            "power bi",
            "powerbi",
        ],
    },
    "Excel": {
        "category": "Ferramentas",
        "aliases": [
            "excel",
            "microsoft excel",
        ],
    },
    "Salesforce": {
        "category": "Ferramentas",
        "aliases": [
            "salesforce",
        ],
    },
    "Jira": {
        "category": "Ferramentas",
        "aliases": [
            "jira",
        ],
    },
    "Trello": {
        "category": "Ferramentas",
        "aliases": [
            "trello",
        ],
    },
    "GitHub": {
        "category": "Ferramentas",
        "aliases": [
            "github",
        ],
    },
    "Git": {
        "category": "Ferramentas",
        "aliases": [
            "git",
        ],
    },
    "Streamlit": {
        "category": "Ferramentas",
        "aliases": [
            "streamlit",
        ],
    },
    "Neo4j": {
        "category": "Ferramentas",
        "aliases": [
            "neo4j",
        ],
    },

    # -----------------------------------------------------
    # GESTÃO
    # -----------------------------------------------------
    "Gestão de Projetos": {
        "category": "Gestão",
        "aliases": [
            "gestão de projetos",
            "gestao de projetos",
            "gerenciamento de projetos",
            "project management",
            "pmo",
        ],
    },
    "Gestão de Operações": {
        "category": "Gestão",
        "aliases": [
            "gestão de operações",
            "gestao de operacoes",
            "operations management",
            "gestão operacional",
            "gestao operacional",
        ],
    },
    "Gestão de Stakeholders": {
        "category": "Gestão",
        "aliases": [
            "gestão de stakeholders",
            "gestao de stakeholders",
            "stakeholder management",
            "stakeholders",
        ],
    },
    "Liderança": {
        "category": "Gestão",
        "aliases": [
            "liderança",
            "lideranca",
            "leadership",
        ],
    },
    "Gestão de Equipes": {
        "category": "Gestão",
        "aliases": [
            "gestão de equipes",
            "gestao de equipes",
            "gestão de equipe",
            "gestao de equipe",
            "team management",
        ],
    },
    "Planejamento Estratégico": {
        "category": "Gestão",
        "aliases": [
            "planejamento estratégico",
            "planejamento estrategico",
            "strategic planning",
        ],
    },
    "Gestão de Processos": {
        "category": "Gestão",
        "aliases": [
            "gestão de processos",
            "gestao de processos",
            "process management",
            "melhoria de processos",
            "process improvement",
        ],
    },
    "Gestão de Riscos": {
        "category": "Gestão",
        "aliases": [
            "gestão de riscos",
            "gestao de riscos",
            "risk management",
        ],
    },
    "Negociação": {
        "category": "Gestão",
        "aliases": [
            "negociação",
            "negociacao",
            "negotiation",
        ],
    },
    "Tomada de Decisão": {
        "category": "Gestão",
        "aliases": [
            "tomada de decisão",
            "tomada de decisao",
            "decision making",
        ],
    },

    # -----------------------------------------------------
    # NEGÓCIO / OPERAÇÕES
    # -----------------------------------------------------
    "Performance Operacional": {
        "category": "Negócio",
        "aliases": [
            "performance operacional",
            "desempenho operacional",
            "operational performance",
        ],
    },
    "Eficiência Operacional": {
        "category": "Negócio",
        "aliases": [
            "eficiência operacional",
            "eficiencia operacional",
            "operational efficiency",
        ],
    },
    "Marketing": {
        "category": "Negócio",
        "aliases": [
            "marketing",
            "marketing digital",
            "marketing analytics",
        ],
    },
    "CRM": {
        "category": "Negócio",
        "aliases": [
            "crm",
            "customer relationship management",
        ],
    },
    "Vendas": {
        "category": "Negócio",
        "aliases": [
            "vendas",
            "sales",
            "gestão comercial",
            "gestao comercial",
        ],
    },

    # -----------------------------------------------------
    # METODOLOGIAS
    # -----------------------------------------------------
    "Agile": {
        "category": "Metodologias",
        "aliases": [
            "agile",
            "ágil",
            "agil",
            "metodologias ágeis",
            "metodologias ageis",
        ],
    },
    "Scrum": {
        "category": "Metodologias",
        "aliases": [
            "scrum",
        ],
    },
    "Kanban": {
        "category": "Metodologias",
        "aliases": [
            "kanban",
        ],
    },
    "PMBOK": {
        "category": "Metodologias",
        "aliases": [
            "pmbok",
        ],
    },
    "Design Thinking": {
        "category": "Metodologias",
        "aliases": [
            "design thinking",
        ],
    },

    # -----------------------------------------------------
    # IDIOMAS
    # -----------------------------------------------------
    "Inglês": {
        "category": "Idiomas",
        "aliases": [
            "inglês",
            "ingles",
            "english",
        ],
    },
    "Espanhol": {
        "category": "Idiomas",
        "aliases": [
            "espanhol",
            "spanish",
        ],
    },
    "Português": {
        "category": "Idiomas",
        "aliases": [
            "português",
            "portugues",
            "portuguese",
        ],
    },
}



# =========================================================
# EQUIVALÊNCIAS PROFISSIONAIS CONTROLADAS
# =========================================================
#
# Não são aliases. São relações de evidência profissional
# controladas para evitar falsos negativos entre competências
# conceitualmente relacionadas.
# =========================================================

SKILL_EQUIVALENCES = {
    "Agile": [
        "Scrum",
        "Kanban",
    ],
    "Liderança": [
        "Gestão de Equipes",
    ],
    "Gestão de Projetos": [
        "PMBOK",
    ],
}


# =========================================================
# PESOS
# =========================================================

CATEGORY_WEIGHTS = {
    "Hard Skills": 1.20,
    "Ferramentas": 0.90,
    "Gestão": 1.25,
    "Negócio": 1.05,
    "Metodologias": 0.75,
    "Idiomas": 0.65,
    "Senioridade": 1.15,
}


PRIORITY_MULTIPLIERS = {
    "Obrigatório": 1.25,
    "Geral": 1.00,
    "Diferencial": 0.65,
}


# =========================================================
# SEÇÕES DA VAGA
# =========================================================

MANDATORY_SECTION_TERMS = [
    "requisitos",
    "requisitos obrigatórios",
    "requisitos obrigatorios",
    "qualificações",
    "qualificacoes",
    "requirements",
    "must have",
    "required",
]


PREFERRED_SECTION_TERMS = [
    "diferenciais",
    "diferencial",
    "desejável",
    "desejavel",
    "desejáveis",
    "desejaveis",
    "nice to have",
    "preferred",
    "differentials",
]


GENERAL_SECTION_TERMS = [
    "responsabilidades",
    "principais responsabilidades",
    "atividades",
    "sobre a posição",
    "sobre a posicao",
    "sobre a vaga",
    "responsibilities",
    "about the role",
]


# =========================================================
# NORMALIZAÇÃO
# =========================================================

def normalize_text(text: str) -> str:
    text = text.lower()

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def contains_term(
    text: str,
    term: str,
) -> bool:

    normalized_text = normalize_text(text)
    normalized_term = normalize_text(term)

    pattern = (
        r"(?<!\w)"
        + re.escape(normalized_term)
        + r"(?!\w)"
    )

    return bool(
        re.search(
            pattern,
            normalized_text,
        )
    )


def contains_any(
    text: str,
    terms: list[str],
) -> bool:

    return any(
        contains_term(
            text,
            term,
        )
        for term in terms
    )



# =========================================================
# MATCHING SEMÂNTICO CONTROLADO
# =========================================================

def profile_supports_equivalent_skill(
    profile: str,
    skill: str,
) -> bool:
    """
    Verifica equivalências profissionais controladas.

    Exemplo:
    - vaga exige Agile;
    - currículo comprova Scrum ou Kanban;
    - o requisito Agile pode ser considerado atendido.

    A função não cria competências nem trata qualquer termo
    relacionado como sinônimo.
    """

    equivalent_skills = SKILL_EQUIVALENCES.get(
        skill,
        [],
    )

    for equivalent_skill in equivalent_skills:

        config = SKILL_CATALOG.get(
            equivalent_skill,
            {},
        )

        aliases = config.get(
            "aliases",
            [],
        )

        if aliases and contains_any(
            profile,
            aliases,
        ):
            return True

    return False


def profile_supports_requirement(
    profile: str,
    requirement: Requirement,
) -> bool:
    """
    Matching do Curator 2.1 em duas camadas:

    1. evidência textual direta pelos aliases do requisito;
    2. equivalência profissional controlada.
    """

    if contains_any(
        profile,
        requirement.aliases,
    ):
        return True

    return profile_supports_equivalent_skill(
        profile=profile,
        skill=requirement.skill,
    )


# =========================================================
# PRIORIDADE DA SEÇÃO
# =========================================================

def detect_section_priority(
    line: str,
) -> str | None:

    normalized = normalize_text(line)

    if any(
        normalize_text(term) in normalized
        for term in MANDATORY_SECTION_TERMS
    ):
        return "Obrigatório"

    if any(
        normalize_text(term) in normalized
        for term in PREFERRED_SECTION_TERMS
    ):
        return "Diferencial"

    if any(
        normalize_text(term) in normalized
        for term in GENERAL_SECTION_TERMS
    ):
        return "Geral"

    return None


def split_job_by_priority(
    job_description: str,
) -> dict[str, str]:

    sections = {
        "Obrigatório": "",
        "Geral": "",
        "Diferencial": "",
    }

    current_priority = "Geral"

    for raw_line in job_description.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        detected_priority = detect_section_priority(
            line
        )

        if detected_priority:
            current_priority = detected_priority

        sections[current_priority] += (
            " " + line
        )

    return sections


# =========================================================
# EXTRAÇÃO DE REQUISITOS
# =========================================================

def detect_required_skills(
    job_description: str,
) -> list[Requirement]:

    sections = split_job_by_priority(
        job_description
    )

    detected: dict[str, Requirement] = {}

    priority_order = {
        "Obrigatório": 3,
        "Geral": 2,
        "Diferencial": 1,
    }

    for priority, section_text in sections.items():

        for skill, config in SKILL_CATALOG.items():

            aliases = config["aliases"]

            if not contains_any(
                section_text,
                aliases,
            ):
                continue

            category = config["category"]

            weight = (
                CATEGORY_WEIGHTS.get(
                    category,
                    1.0,
                )
                * PRIORITY_MULTIPLIERS.get(
                    priority,
                    1.0,
                )
            )

            requirement = Requirement(
                skill=skill,
                category=category,
                aliases=aliases,
                priority=priority,
                weight=weight,
            )

            previous = detected.get(skill)

            if (
                previous is None
                or priority_order[priority]
                > priority_order[previous.priority]
            ):
                detected[skill] = requirement

    return list(
        detected.values()
    )


# =========================================================
# SENIORIDADE
# =========================================================

def detect_job_seniority(
    job_description: str,
) -> str | None:

    text = normalize_text(
        job_description
    )

    executive_terms = [
        "diretor",
        "diretora",
        "director",
        "head",
        "chief",
        "ceo",
    ]

    manager_terms = [
        "gerente",
        "manager",
        "gestor",
        "gestora",
    ]

    coordinator_terms = [
        "coordenador",
        "coordenadora",
        "coordinator",
    ]

    senior_terms = [
        "senior",
        "especialista",
        "specialist",
    ]

    if any(
        contains_term(
            text,
            term,
        )
        for term in executive_terms
    ):
        return "Executiva / Direção"

    if any(
        contains_term(
            text,
            term,
        )
        for term in manager_terms
    ):
        return "Gerencial"

    if any(
        contains_term(
            text,
            term,
        )
        for term in coordinator_terms
    ):
        return "Coordenação"

    if any(
        contains_term(
            text,
            term,
        )
        for term in senior_terms
    ):
        return "Sênior / Especialista"

    return None


def detect_profile_seniority(
    profile: str,
) -> str | None:

    return detect_job_seniority(
        profile
    )


def seniority_match_score(
    profile_seniority: str | None,
    job_seniority: str | None,
) -> float:

    if not job_seniority:
        return 1.0

    if not profile_seniority:
        return 0.45

    levels = {
        "Não identificada": 0,
        "Sênior / Especialista": 1,
        "Coordenação": 2,
        "Gerencial": 3,
        "Executiva / Direção": 4,
    }

    profile_level = levels.get(
        profile_seniority,
        0,
    )

    job_level = levels.get(
        job_seniority,
        0,
    )

    difference = (
        profile_level
        - job_level
    )

    if difference == 0:
        return 1.0

    if difference == 1:
        return 0.90

    if difference > 1:
        return 0.78

    if difference == -1:
        return 0.65

    return 0.35


# =========================================================
# SCORE
# =========================================================

def calculate_weighted_score(
    matches: list[SkillMatch],
    profile: str,
    job_description: str,
) -> tuple[int, dict]:

    if not matches:
        return 0, {
            "requirements_score": 0,
            "seniority_score": None,
            "coverage": 0,
        }

    total_weight = sum(
        item.weight
        for item in matches
    )

    attended_weight = sum(
        item.weight
        for item in matches
        if item.status == "Atende"
    )

    if total_weight == 0:
        requirements_ratio = 0.0
    else:
        requirements_ratio = (
            attended_weight
            / total_weight
        )

    attended_count = sum(
        1
        for item in matches
        if item.status == "Atende"
    )

    coverage = (
        attended_count
        / len(matches)
    )

    job_seniority = detect_job_seniority(
        job_description
    )

    profile_seniority = (
        detect_profile_seniority(
            profile
        )
    )

    if job_seniority:

        seniority_ratio = (
            seniority_match_score(
                profile_seniority,
                job_seniority,
            )
        )

        raw_score = (
            requirements_ratio * 0.85
            + seniority_ratio * 0.15
        )

    else:

        seniority_ratio = None

        raw_score = (
            requirements_ratio
        )

    # -----------------------------------------------------
    # CALIBRAÇÃO
    #
    # Evita transformar matching textual simples
    # em uma falsa certeza de 100%.
    # -----------------------------------------------------

    category_count = len(
        {
            item.category
            for item in matches
        }
    )

    if len(matches) <= 2:
        confidence_factor = 0.88

    elif len(matches) <= 4:
        confidence_factor = 0.93

    else:
        confidence_factor = 0.97

    if category_count >= 3:
        confidence_factor += 0.01

    confidence_factor = min(
        confidence_factor,
        0.98,
    )

    calibrated_score = (
        raw_score
        * confidence_factor
        * 100
    )

    score = round(
        min(
            calibrated_score,
            98,
        )
    )

    details = {
        "requirements_score": round(
            requirements_ratio * 100
        ),
        "seniority_score": (
            round(
                seniority_ratio * 100
            )
            if seniority_ratio is not None
            else None
        ),
        "coverage": round(
            coverage * 100
        ),
        "job_seniority": job_seniority,
        "profile_seniority": profile_seniority,
        "categories_detected": category_count,
    }

    return score, details


# =========================================================
# COMPATIBILIDADE
# =========================================================

def classify_compatibility(
    score: int,
) -> str:

    if score >= 80:
        return "Alta"

    if score >= 60:
        return "Média-Alta"

    if score >= 45:
        return "Média"

    return "Baixa"


# =========================================================
# ANÁLISE PRINCIPAL
# =========================================================

def analyze_compatibility(
    profile: str,
    job_description: str,
) -> dict:

    requirements = detect_required_skills(
        job_description
    )

    matches: list[SkillMatch] = []

    for requirement in requirements:

        attended = profile_supports_requirement(
            profile=profile,
            requirement=requirement,
        )

        status = (
            "Atende"
            if attended
            else "Não identificado no perfil"
        )

        matches.append(
            SkillMatch(
                skill=requirement.skill,
                status=status,
                category=requirement.category,
                priority=requirement.priority,
                weight=requirement.weight,
            )
        )

    score, score_details = (
        calculate_weighted_score(
            matches=matches,
            profile=profile,
            job_description=job_description,
        )
    )

    compatibility = (
        classify_compatibility(
            score
        )
    )

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

    mandatory_matches = [
        item
        for item in matches
        if item.priority == "Obrigatório"
    ]

    mandatory_gaps = [
        item.skill
        for item in mandatory_matches
        if item.status != "Atende"
    ]

    preferred_gaps = [
        item.skill
        for item in matches
        if (
            item.priority == "Diferencial"
            and item.status != "Atende"
        )
    ]

    category_summary = {}

    categories = sorted(
        {
            item.category
            for item in matches
        }
    )

    for category in categories:

        category_items = [
            item
            for item in matches
            if item.category == category
        ]

        attended = sum(
            1
            for item in category_items
            if item.status == "Atende"
        )

        total = len(
            category_items
        )

        category_summary[category] = {
            "attended": attended,
            "total": total,
            "score": (
                round(
                    attended
                    / total
                    * 100
                )
                if total
                else 0
            ),
        }

    return {
        # -------------------------------------------------
        # Compatibilidade com main.py atual
        # -------------------------------------------------
        "score": score,
        "compatibility": compatibility,
        "matches": matches,
        "strengths": strengths,
        "gaps": gaps,

        # -------------------------------------------------
        # Curator 2.1
        # -------------------------------------------------
        "score_details": score_details,
        "mandatory_gaps": mandatory_gaps,
        "preferred_gaps": preferred_gaps,
        "category_summary": category_summary,
        "requirements_count": len(matches),
    }
