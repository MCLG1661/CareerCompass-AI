"""
CareerCompass AI
Opportunity Intelligence Engine

Transforma descrições de vagas não estruturadas em um Opportunity Profile
padronizado para uso pelos demais engines da plataforma.

Responsabilidades:
- identificar senioridade;
- identificar modelo de trabalho;
- identificar localização;
- extrair requisitos obrigatórios e desejáveis;
- identificar competências e tecnologias;
- identificar responsabilidades;
- identificar indicadores de liderança;
- identificar idiomas;
- produzir sinais estruturados para Career Fit, ATS, Decision Engine
  e Career Analytics.

A implementação inicial é determinística e explicável.
Ela não depende de LLM e não inventa informações ausentes na vaga.
"""

from __future__ import annotations

import re

from dataclasses import asdict, dataclass, field
from typing import Any


# ============================================================
# DATA MODEL
# ============================================================


@dataclass
class OpportunityProfile:
    job_title: str
    company: str | None = None

    seniority: str = "Não identificada"
    work_model: str = "Não identificado"
    location: str | None = None

    mandatory_requirements: list[str] = field(default_factory=list)
    preferred_requirements: list[str] = field(default_factory=list)

    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    methodologies: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    responsibilities: list[str] = field(default_factory=list)

    leadership_signals: list[str] = field(default_factory=list)
    business_signals: list[str] = field(default_factory=list)

    keywords: list[str] = field(default_factory=list)

    confidence_score: float = 0.0

    raw_description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# TAXONOMIAS
# ============================================================


SENIORITY_PATTERNS = {
    "Executivo": [
        r"\bchief\b",
        r"\bc-level\b",
        r"\bceo\b",
        r"\bcoo\b",
        r"\bcmo\b",
        r"\bcto\b",
        r"\bcdo\b",
        r"\bvice president\b",
        r"\bvp\b",
        r"\bdiretor(?:a)?\b",
        r"\bdirector\b",
        r"\bsuperintendente\b",
        r"\bhead\b",
    ],
    "Gerencial": [
        r"\bgerente\b",
        r"\bmanager\b",
        r"\bmanagement\b",
        r"\bcoordenador(?:a)?\b",
        r"\bcoordinator\b",
    ],
    "Sênior": [
        r"\bs[êe]nior\b",
        r"\bsr\.?\b",
        r"\bsenior\b",
        r"\bespecialista\b",
        r"\bspecialist\b",
    ],
    "Pleno": [
        r"\bpleno\b",
        r"\bmid[- ]level\b",
    ],
    "Júnior": [
        r"\bj[uú]nior\b",
        r"\bjr\.?\b",
        r"\bjunior\b",
        r"\bentry[- ]level\b",
    ],
    "Estágio": [
        r"\best[aá]gio\b",
        r"\bestagi[aá]rio\b",
        r"\bintern\b",
        r"\binternship\b",
    ],
}


WORK_MODEL_PATTERNS = {
    "Remoto": [
        r"\bremoto\b",
        r"\bremote\b",
        r"\bhome office\b",
        r"\b100% remoto\b",
    ],
    "Híbrido": [
        r"\bh[ií]brido\b",
        r"\bhybrid\b",
    ],
    "Presencial": [
        r"\bpresencial\b",
        r"\bon[- ]site\b",
        r"\bonsite\b",
    ],
}


SKILL_CATALOG = {
    "Gestão de Projetos": [
        "gestão de projetos",
        "project management",
        "gerenciamento de projetos",
    ],
    "Gestão de Operações": [
        "gestão de operações",
        "operations management",
        "operações",
        "operations",
    ],
    "Liderança": [
        "liderança",
        "leadership",
        "liderar",
        "lead teams",
    ],
    "Gestão de Equipes": [
        "gestão de equipes",
        "team management",
        "people management",
        "gestão de pessoas",
    ],
    "Gestão de Stakeholders": [
        "stakeholder management",
        "gestão de stakeholders",
        "stakeholders",
    ],
    "Planejamento Estratégico": [
        "planejamento estratégico",
        "strategic planning",
    ],
    "Gestão de Riscos": [
        "gestão de riscos",
        "risk management",
    ],
    "Negociação": [
        "negociação",
        "negotiation",
    ],
    "Data Analytics": [
        "data analytics",
        "analytics",
        "análise de dados",
    ],
    "Business Intelligence": [
        "business intelligence",
        "bi",
    ],
    "Power BI": [
        "power bi",
        "powerbi",
    ],
    "Python": [
        "python",
    ],
    "SQL": [
        "sql",
    ],
    "Machine Learning": [
        "machine learning",
        "ml",
    ],
    "Inteligência Artificial": [
        "inteligência artificial",
        "artificial intelligence",
        "generative ai",
        "genai",
        "ia generativa",
    ],
    "Marketing": [
        "marketing",
    ],
    "Marketing Digital": [
        "marketing digital",
        "digital marketing",
    ],
    "Growth": [
        "growth",
        "growth marketing",
    ],
    "CRM": [
        "crm",
        "customer relationship management",
    ],
    "SEO": [
        "seo",
        "search engine optimization",
    ],
    "Mídia Paga": [
        "mídia paga",
        "paid media",
        "performance media",
    ],
    "Vendas": [
        "vendas",
        "sales",
    ],
    "Gestão Comercial": [
        "gestão comercial",
        "sales management",
    ],
    "Desenvolvimento de Negócios": [
        "business development",
        "desenvolvimento de negócios",
    ],
    "Gestão de Contas": [
        "account management",
        "gestão de contas",
        "key account",
    ],
    "Transformação Digital": [
        "transformação digital",
        "digital transformation",
    ],
    "Automação": [
        "automação",
        "automation",
    ],
    "Processos": [
        "processos",
        "process management",
        "process improvement",
    ],
    "KPIs": [
        "kpi",
        "kpis",
        "indicadores de performance",
        "indicadores de desempenho",
    ],
    "Dashboards": [
        "dashboard",
        "dashboards",
    ],
}


TOOL_CATALOG = {
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Excel": ["excel"],
    "Python": ["python"],
    "SQL": ["sql"],
    "Salesforce": ["salesforce"],
    "HubSpot": ["hubspot"],
    "SAP": ["sap"],
    "Oracle": ["oracle"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "Google Cloud": ["google cloud", "gcp"],
    "Jira": ["jira"],
    "Trello": ["trello"],
    "GitHub": ["github"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes"],
}


METHODOLOGY_CATALOG = {
    "Agile": [
        "agile",
        "ágil",
        "metodologias ágeis",
    ],
    "Scrum": [
        "scrum",
    ],
    "Kanban": [
        "kanban",
    ],
    "Lean": [
        "lean",
    ],
    "Design Thinking": [
        "design thinking",
    ],
    "PMBOK": [
        "pmbok",
    ],
}


LANGUAGE_CATALOG = {
    "Inglês": [
        "inglês",
        "english",
    ],
    "Espanhol": [
        "espanhol",
        "spanish",
    ],
    "Português": [
        "português",
        "portuguese",
    ],
}


LEADERSHIP_TERMS = [
    "liderança",
    "liderar",
    "gestão de equipe",
    "gestão de pessoas",
    "people management",
    "team management",
    "team leadership",
    "desenvolvimento de equipe",
    "formação de equipe",
    "gestão de talentos",
]


BUSINESS_TERMS = [
    "estratégia",
    "strategy",
    "resultado",
    "results",
    "receita",
    "revenue",
    "budget",
    "orçamento",
    "p&l",
    "profit",
    "rentabilidade",
    "crescimento",
    "growth",
    "negócio",
    "business",
    "performance",
]


MANDATORY_MARKERS = [
    "obrigatório",
    "obrigatória",
    "obrigatórios",
    "obrigatórias",
    "requisito",
    "requisitos",
    "necessário",
    "necessária",
    "necessários",
    "necessárias",
    "must have",
    "required",
    "requirements",
    "essencial",
    "essenciais",
]


PREFERRED_MARKERS = [
    "desejável",
    "desejáveis",
    "diferencial",
    "diferenciais",
    "preferencial",
    "preferencialmente",
    "nice to have",
    "preferred",
    "plus",
]


RESPONSIBILITY_MARKERS = [
    "responsabilidades",
    "responsibility",
    "responsibilities",
    "principais atividades",
    "atividades",
    "atribuições",
    "desafios",
    "o que você fará",
    "o que você vai fazer",
]


# ============================================================
# TEXT HELPERS
# ============================================================


def normalize_text(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        (text or "").strip().lower(),
    )


def clean_line(line: str) -> str:
    line = re.sub(
        r"^[\s•●▪■◆◇✓✔☑\-–—*]+",
        "",
        line,
    )

    line = re.sub(
        r"\s+",
        " ",
        line,
    )

    return line.strip()


def split_lines(text: str) -> list[str]:
    lines = []

    for raw_line in (text or "").splitlines():
        line = clean_line(raw_line)

        if line:
            lines.append(line)

    return lines


def unique_preserve_order(
    values: list[str],
) -> list[str]:
    seen = set()
    result = []

    for value in values:
        key = normalize_text(value)

        if not key or key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


def contains_term(
    text: str,
    term: str,
) -> bool:
    normalized = normalize_text(text)
    normalized_term = normalize_text(term)

    if len(normalized_term) <= 3:
        return bool(
            re.search(
                rf"(?<!\w){re.escape(normalized_term)}(?!\w)",
                normalized,
            )
        )

    return normalized_term in normalized


# ============================================================
# EXTRACTION
# ============================================================


def detect_seniority(
    job_title: str,
    description: str,
) -> str:
    """
    Prioriza o título porque ele normalmente representa melhor
    a senioridade da posição do que menções incidentais no texto.
    """

    title = normalize_text(job_title)

    for seniority, patterns in SENIORITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, title, flags=re.IGNORECASE):
                return seniority

    body = normalize_text(description)

    for seniority, patterns in SENIORITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, body, flags=re.IGNORECASE):
                return seniority

    return "Não identificada"


def detect_work_model(
    description: str,
) -> str:
    text = normalize_text(description)

    for model, patterns in WORK_MODEL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return model

    return "Não identificado"


def detect_location(
    description: str,
) -> str | None:
    """
    Extração conservadora.

    Procura somente linhas explicitamente associadas a localização.
    Não tenta inferir cidade/estado sem evidência textual.
    """

    patterns = [
        r"^(?:localiza[cç][aã]o|local|location)\s*[:\-]\s*(.+)$",
        r"^(?:cidade|city)\s*[:\-]\s*(.+)$",
    ]

    for line in split_lines(description):
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                flags=re.IGNORECASE,
            )

            if match:
                location = match.group(1).strip()

                if location:
                    return location[:120]

    return None


def extract_catalog_matches(
    text: str,
    catalog: dict[str, list[str]],
) -> list[str]:
    matches = []

    for canonical_name, aliases in catalog.items():
        if any(
            contains_term(text, alias)
            for alias in aliases
        ):
            matches.append(canonical_name)

    return matches


def classify_requirement_lines(
    description: str,
) -> tuple[list[str], list[str]]:
    """
    Classifica linhas explicitamente sinalizadas como obrigatórias
    ou desejáveis.

    Não converte qualquer frase da vaga em requisito.
    """

    mandatory = []
    preferred = []

    current_section: str | None = None

    for line in split_lines(description):
        normalized = normalize_text(line)

        if any(
            marker in normalized
            for marker in PREFERRED_MARKERS
        ):
            current_section = "preferred"

            if ":" in line:
                after_colon = line.split(":", 1)[1].strip()

                if after_colon:
                    preferred.append(after_colon)

            continue

        if any(
            marker in normalized
            for marker in MANDATORY_MARKERS
        ):
            current_section = "mandatory"

            if ":" in line:
                after_colon = line.split(":", 1)[1].strip()

                if after_colon:
                    mandatory.append(after_colon)

            continue

        if is_section_heading(line):
            current_section = None
            continue

        if current_section == "mandatory":
            mandatory.append(line)

        elif current_section == "preferred":
            preferred.append(line)

    return (
        unique_preserve_order(mandatory),
        unique_preserve_order(preferred),
    )


def is_section_heading(
    line: str,
) -> bool:
    normalized = normalize_text(line)

    known_headings = [
        "responsabilidades",
        "responsibility",
        "responsibilities",
        "principais atividades",
        "atividades",
        "atribuições",
        "desafios",
        "benefícios",
        "benefits",
        "sobre a empresa",
        "about us",
        "quem somos",
    ]

    if normalized.rstrip(":") in known_headings:
        return True

    if line.endswith(":") and len(line.split()) <= 6:
        return True

    return False


def extract_responsibilities(
    description: str,
) -> list[str]:
    responsibilities = []
    current_section = False

    for line in split_lines(description):
        normalized = normalize_text(line)

        if any(
            marker == normalized.rstrip(":")
            for marker in RESPONSIBILITY_MARKERS
        ):
            current_section = True
            continue

        if current_section and is_section_heading(line):
            current_section = False
            continue

        if current_section:
            responsibilities.append(line)

    return unique_preserve_order(
        responsibilities
    )[:20]


def extract_signal_terms(
    description: str,
    terms: list[str],
) -> list[str]:
    return [
        term
        for term in terms
        if contains_term(description, term)
    ]


def extract_keywords(
    description: str,
    skills: list[str],
    tools: list[str],
    methodologies: list[str],
    languages: list[str],
) -> list[str]:
    """
    Keywords são deliberadamente baseadas na taxonomia controlada,
    evitando retornar palavras genéricas sem valor profissional.
    """

    values = (
        skills
        + tools
        + methodologies
        + languages
    )

    return unique_preserve_order(values)


# ============================================================
# CONFIDENCE
# ============================================================


def calculate_confidence(
    profile: OpportunityProfile,
) -> float:
    """
    Mede quanta estrutura útil foi identificada na vaga.

    Não representa qualidade da vaga nem compatibilidade do candidato.
    """

    signals = 0
    possible = 8

    if profile.job_title:
        signals += 1

    if profile.seniority != "Não identificada":
        signals += 1

    if profile.work_model != "Não identificado":
        signals += 1

    if profile.mandatory_requirements:
        signals += 1

    if profile.preferred_requirements:
        signals += 1

    if profile.skills:
        signals += 1

    if profile.responsibilities:
        signals += 1

    if (
        profile.tools
        or profile.methodologies
        or profile.languages
    ):
        signals += 1

    return round(
        (signals / possible) * 100,
        2,
    )


# ============================================================
# MAIN ENGINE
# ============================================================


def analyze_opportunity(
    job_title: str,
    job_description: str,
    company: str | None = None,
) -> OpportunityProfile:
    """
    Constrói o Opportunity Intelligence Profile.
    """

    if not job_title.strip():
        raise ValueError(
            "job_title é obrigatório."
        )

    if not job_description.strip():
        raise ValueError(
            "job_description é obrigatório."
        )

    mandatory, preferred = (
        classify_requirement_lines(
            job_description
        )
    )

    skills = extract_catalog_matches(
        job_description,
        SKILL_CATALOG,
    )

    tools = extract_catalog_matches(
        job_description,
        TOOL_CATALOG,
    )

    methodologies = extract_catalog_matches(
        job_description,
        METHODOLOGY_CATALOG,
    )

    languages = extract_catalog_matches(
        job_description,
        LANGUAGE_CATALOG,
    )

    responsibilities = extract_responsibilities(
        job_description
    )

    leadership_signals = extract_signal_terms(
        job_description,
        LEADERSHIP_TERMS,
    )

    business_signals = extract_signal_terms(
        job_description,
        BUSINESS_TERMS,
    )

    keywords = extract_keywords(
        job_description,
        skills,
        tools,
        methodologies,
        languages,
    )

    profile = OpportunityProfile(
        job_title=job_title.strip(),
        company=company.strip() if company else None,
        seniority=detect_seniority(
            job_title,
            job_description,
        ),
        work_model=detect_work_model(
            job_description
        ),
        location=detect_location(
            job_description
        ),
        mandatory_requirements=mandatory,
        preferred_requirements=preferred,
        skills=skills,
        tools=tools,
        methodologies=methodologies,
        languages=languages,
        responsibilities=responsibilities,
        leadership_signals=leadership_signals,
        business_signals=business_signals,
        keywords=keywords,
        raw_description=job_description.strip(),
    )

    profile.confidence_score = (
        calculate_confidence(profile)
    )

    return profile


# ============================================================
# SUMMARY
# ============================================================


def build_opportunity_summary(
    profile: OpportunityProfile,
) -> dict[str, Any]:
    """
    Cria versão resumida adequada para UI, persistência,
    analytics e futuros agentes.
    """

    return {
        "job_title": profile.job_title,
        "company": profile.company,
        "seniority": profile.seniority,
        "work_model": profile.work_model,
        "location": profile.location,
        "mandatory_requirements": (
            profile.mandatory_requirements
        ),
        "preferred_requirements": (
            profile.preferred_requirements
        ),
        "skills": profile.skills,
        "tools": profile.tools,
        "methodologies": profile.methodologies,
        "languages": profile.languages,
        "responsibilities": profile.responsibilities,
        "leadership_signals": (
            profile.leadership_signals
        ),
        "business_signals": (
            profile.business_signals
        ),
        "keywords": profile.keywords,
        "confidence_score": (
            profile.confidence_score
        ),
    }


# ============================================================
# SELF TEST
# ============================================================


def run_self_test() -> dict[str, Any]:
    sample_description = """
Localização: São Paulo - SP
Modelo híbrido.

Responsabilidades:
- Liderar projetos estratégicos de transformação digital.
- Gerenciar stakeholders e equipes multidisciplinares.
- Acompanhar KPIs e dashboards executivos.
- Apoiar decisões de negócio orientadas por dados.

Requisitos obrigatórios:
- Experiência com gestão de projetos.
- Liderança e gestão de equipes.
- Conhecimento de Power BI e análise de dados.
- Inglês avançado.

Diferenciais:
- Scrum ou outras metodologias ágeis.
- Python e SQL.
"""

    profile = analyze_opportunity(
        job_title="Gerente Sênior de Projetos",
        company="CareerCompass Test Company",
        job_description=sample_description,
    )

    return {
        "status": "ok",
        "profile": build_opportunity_summary(
            profile
        ),
    }


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================


if __name__ == "__main__":
    result = run_self_test()

    print()
    print(
        "CareerCompass AI — "
        "Opportunity Intelligence Engine"
    )
    print(
        "--------------------------------------------"
    )
    print(
        f"Status: {result['status']}"
    )

    profile = result["profile"]

    print(
        f"Cargo: {profile['job_title']}"
    )
    print(
        f"Empresa: {profile['company']}"
    )
    print(
        f"Senioridade: {profile['seniority']}"
    )
    print(
        f"Modelo: {profile['work_model']}"
    )
    print(
        f"Localização: {profile['location']}"
    )
    print(
        "Confiança da extração: "
        f"{profile['confidence_score']}%"
    )

    print()
    print("Competências:")
    for item in profile["skills"]:
        print(f" - {item}")

    print()
    print("Ferramentas:")
    for item in profile["tools"]:
        print(f" - {item}")

    print()
    print("Metodologias:")
    for item in profile["methodologies"]:
        print(f" - {item}")

    print()
    print("Requisitos obrigatórios:")
    for item in profile[
        "mandatory_requirements"
    ]:
        print(f" - {item}")

    print()
    print("Diferenciais:")
    for item in profile[
        "preferred_requirements"
    ]:
        print(f" - {item}")
