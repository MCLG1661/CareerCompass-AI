from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


# =========================================================
# MODELO DO PERFIL PROFISSIONAL
# =========================================================

@dataclass
class ProfessionalProfile:
    raw_text: str

    candidate_name: str = "Candidato"

    areas: list[str] = field(default_factory=list)
    hard_skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    management_skills: list[str] = field(default_factory=list)
    methodologies: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    seniority: str = "Não identificada"

    evidence_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "candidate_name": self.candidate_name,
            "areas": self.areas,
            "hard_skills": self.hard_skills,
            "tools": self.tools,
            "management_skills": self.management_skills,
            "methodologies": self.methodologies,
            "languages": self.languages,
            "seniority": self.seniority,
            "evidence_terms": self.evidence_terms,
        }


# =========================================================
# VOCABULÁRIOS
# =========================================================

AREA_TERMS = {
    "Gestão de Projetos": [
        "gestão de projetos",
        "gestao de projetos",
        "gerenciamento de projetos",
        "project management",
        "pmo",
    ],
    "Operações": [
        "operações",
        "operacoes",
        "gestão de operações",
        "gestao de operacoes",
        "operations",
        "performance operacional",
        "eficiência operacional",
        "eficiencia operacional",
    ],
    "Marketing": [
        "marketing",
        "marketing digital",
        "marketing analytics",
        "growth",
    ],
    "Data Analytics": [
        "data analytics",
        "análise de dados",
        "analise de dados",
        "analytics",
    ],
    "Business Intelligence": [
        "business intelligence",
        "bi",
    ],
    "Inteligência Artificial": [
        "inteligência artificial",
        "inteligencia artificial",
        "artificial intelligence",
        "ia aplicada",
        "generative ai",
        "genai",
    ],
    "Vendas": [
        "vendas",
        "gestão comercial",
        "gestao comercial",
        "sales",
        "comercial",
    ],
    "CRM": [
        "crm",
        "customer relationship management",
    ],
}


HARD_SKILL_TERMS = {
    "Python": [
        "python",
    ],
    "SQL": [
        "sql",
    ],
    "Pandas": [
        "pandas",
    ],
    "Machine Learning": [
        "machine learning",
        "aprendizado de máquina",
        "aprendizado de maquina",
    ],
    "Data Analytics": [
        "data analytics",
        "análise de dados",
        "analise de dados",
    ],
    "Business Intelligence": [
        "business intelligence",
    ],
    "KPIs": [
        "kpi",
        "kpis",
        "indicadores de desempenho",
        "indicadores de performance",
    ],
    "Dashboards": [
        "dashboard",
        "dashboards",
    ],
    "Análise de Performance": [
        "análise de performance",
        "analise de performance",
        "performance analysis",
    ],
    "Automação": [
        "automação",
        "automacao",
        "automation",
    ],
    "Inteligência Artificial": [
        "inteligência artificial",
        "inteligencia artificial",
        "artificial intelligence",
        "generative ai",
        "genai",
    ],
}


TOOL_TERMS = {
    "Power BI": [
        "power bi",
        "powerbi",
    ],
    "Excel": [
        "excel",
        "microsoft excel",
    ],
    "Python": [
        "python",
    ],
    "Pandas": [
        "pandas",
    ],
    "SQL": [
        "sql",
    ],
    "Salesforce": [
        "salesforce",
    ],
    "Streamlit": [
        "streamlit",
    ],
    "Git": [
        "git",
    ],
    "GitHub": [
        "github",
    ],
    "Neo4j": [
        "neo4j",
    ],
    "Trello": [
        "trello",
    ],
    "Jira": [
        "jira",
    ],
}


MANAGEMENT_TERMS = {
    "Gestão de Projetos": [
        "gestão de projetos",
        "gestao de projetos",
        "project management",
        "gerenciamento de projetos",
    ],
    "Gestão de Operações": [
        "gestão de operações",
        "gestao de operacoes",
        "operations management",
    ],
    "Gestão de Stakeholders": [
        "stakeholder",
        "stakeholders",
        "gestão de stakeholders",
        "gestao de stakeholders",
    ],
    "Liderança": [
        "liderança",
        "lideranca",
        "leadership",
    ],
    "Gestão de Equipes": [
        "gestão de equipes",
        "gestao de equipes",
        "gestão de equipe",
        "gestao de equipe",
    ],
    "Planejamento Estratégico": [
        "planejamento estratégico",
        "planejamento estrategico",
        "strategic planning",
    ],
    "Gestão de Processos": [
        "gestão de processos",
        "gestao de processos",
        "process management",
        "melhoria de processos",
    ],
    "Negociação": [
        "negociação",
        "negociacao",
        "negotiation",
    ],
    "Gestão de Indicadores": [
        "indicadores",
        "kpi",
        "kpis",
        "gestão de indicadores",
        "gestao de indicadores",
    ],
    "Gestão de Riscos": [
        "gestão de riscos",
        "gestao de riscos",
        "risk management",
    ],
}


METHODOLOGY_TERMS = {
    "Agile": [
        "agile",
        "ágil",
        "agil",
        "metodologias ágeis",
        "metodologias ageis",
    ],
    "Scrum": [
        "scrum",
    ],
    "Kanban": [
        "kanban",
    ],
    "PMBOK": [
        "pmbok",
    ],
    "Design Thinking": [
        "design thinking",
    ],
}


LANGUAGE_TERMS = {
    "Inglês": [
        "inglês",
        "ingles",
        "english",
    ],
    "Português": [
        "português",
        "portugues",
        "portuguese",
    ],
    "Espanhol": [
        "espanhol",
        "spanish",
    ],
}


EVIDENCE_TERMS = {
    "Resultados": [
        "resultado",
        "resultados",
    ],
    "Metas": [
        "meta",
        "metas",
    ],
    "Indicadores": [
        "indicador",
        "indicadores",
        "kpi",
        "kpis",
    ],
    "Performance": [
        "performance",
        "desempenho",
    ],
    "Eficiência": [
        "eficiência",
        "eficiencia",
    ],
    "Melhoria": [
        "melhoria",
        "melhorias",
    ],
    "Receita": [
        "receita",
        "faturamento",
    ],
    "Redução de Custos": [
        "redução de custos",
        "reducao de custos",
        "redução de custo",
        "reducao de custo",
    ],
}


# =========================================================
# DETECÇÃO DO NOME DO CANDIDATO
# =========================================================

INVALID_NAME_TERMS = {
    "curriculo",
    "currículo",
    "curriculum",
    "vitae",
    "perfil profissional",
    "resumo profissional",
    "professional profile",
    "career summary",
    "experiência profissional",
    "experiencia profissional",
    "professional experience",
    "formação",
    "formacao",
    "education",
    "competências",
    "competencias",
    "skills",
    "contato",
    "contact",
    "telefone",
    "phone",
    "email",
    "e-mail",
    "linkedin",
    "github",
}


JOB_TITLE_TERMS = {
    "analista",
    "gerente",
    "diretor",
    "diretora",
    "coordenador",
    "coordenadora",
    "consultor",
    "consultora",
    "especialista",
    "supervisor",
    "supervisora",
    "assistente",
    "executivo",
    "executiva",
    "manager",
    "director",
    "analyst",
    "specialist",
    "consultant",
    "coordinator",
    "head",
    "ceo",
    "founder",
}


def _clean_candidate_line(line: str) -> str:
    line = line.strip()

    line = re.sub(
        r"\s+",
        " ",
        line,
    )

    line = line.strip(
        "•|-–—_:;,."
    )

    return line.strip()


def _looks_like_email(text: str) -> bool:
    return bool(
        re.search(
            r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
            text,
        )
    )


def _looks_like_phone(text: str) -> bool:
    digits = re.sub(
        r"\D",
        "",
        text,
    )

    return len(digits) >= 8


def _looks_like_url(text: str) -> bool:
    lowered = text.lower()

    return any(
        marker in lowered
        for marker in [
            "http://",
            "https://",
            "www.",
            "linkedin.com",
            "github.com",
        ]
    )


def _contains_invalid_heading(text: str) -> bool:
    normalized = normalize_text(text)

    return any(
        normalize_text(term) in normalized
        for term in INVALID_NAME_TERMS
    )


def _looks_like_job_title(text: str) -> bool:
    normalized = normalize_text(text)

    words = set(
        re.findall(
            r"\b[\w\-]+\b",
            normalized,
        )
    )

    return bool(
        words.intersection(
            {
                normalize_text(term)
                for term in JOB_TITLE_TERMS
            }
        )
    )


def _is_plausible_person_name(text: str) -> bool:
    candidate = _clean_candidate_line(text)

    if not candidate:
        return False

    if len(candidate) < 5 or len(candidate) > 70:
        return False

    if _looks_like_email(candidate):
        return False

    if _looks_like_phone(candidate):
        return False

    if _looks_like_url(candidate):
        return False

    if _contains_invalid_heading(candidate):
        return False

    if _looks_like_job_title(candidate):
        return False

    if any(
        char.isdigit()
        for char in candidate
    ):
        return False

    words = candidate.split()

    if len(words) < 2 or len(words) > 6:
        return False

    valid_words = 0

    for word in words:
        cleaned = re.sub(
            r"[^A-Za-zÀ-ÖØ-öø-ÿ'-]",
            "",
            word,
        )

        if len(cleaned) >= 2:
            valid_words += 1

    if valid_words < 2:
        return False

    return True


def detect_candidate_name(text: str) -> str:
    """
    Procura um nome plausível nas primeiras linhas do currículo.

    A função é deliberadamente conservadora:
    quando não há evidência suficiente, retorna "Candidato".
    """

    if not text or not text.strip():
        return "Candidato"

    raw_lines = text.splitlines()

    lines = [
        _clean_candidate_line(line)
        for line in raw_lines[:20]
        if _clean_candidate_line(line)
    ]

    if not lines:
        return "Candidato"

    # Prioridade máxima para as primeiras linhas do documento.
    for line in lines[:8]:
        if _is_plausible_person_name(line):
            return line

    # Segunda tentativa: linhas seguintes, ainda no cabeçalho inicial.
    for line in lines[8:20]:
        if _is_plausible_person_name(line):
            return line

    return "Candidato"


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


# =========================================================
# MATCHING DE TERMOS
# =========================================================

def contains_term(
    normalized_text: str,
    term: str,
) -> bool:

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


def detect_from_dictionary(
    text: str,
    vocabulary: dict[str, list[str]],
) -> list[str]:

    normalized_text = normalize_text(text)

    detected = []

    for label, terms in vocabulary.items():

        if any(
            contains_term(
                normalized_text,
                term,
            )
            for term in terms
        ):
            detected.append(label)

    return detected


# =========================================================
# SENIORIDADE
# =========================================================

def detect_seniority(text: str) -> str:

    normalized_text = normalize_text(text)

    executive_terms = [
        "diretor",
        "diretora",
        "director",
        "head",
        "ceo",
        "chief",
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
        "sênior",
        "especialista",
        "specialist",
    ]

    if any(
        contains_term(normalized_text, term)
        for term in executive_terms
    ):
        return "Executiva / Direção"

    if any(
        contains_term(normalized_text, term)
        for term in manager_terms
    ):
        return "Gerencial"

    if any(
        contains_term(normalized_text, term)
        for term in coordinator_terms
    ):
        return "Coordenação"

    if any(
        contains_term(normalized_text, term)
        for term in senior_terms
    ):
        return "Sênior / Especialista"

    return "Não identificada"


# =========================================================
# CONSTRUÇÃO DO PERFIL
# =========================================================

def build_professional_profile(
    text: str,
) -> ProfessionalProfile:

    if not text or not text.strip():
        return ProfessionalProfile(
            raw_text="",
            candidate_name="Candidato",
        )

    profile = ProfessionalProfile(
        raw_text=text,
    )

    profile.candidate_name = detect_candidate_name(
        text
    )

    profile.areas = detect_from_dictionary(
        text,
        AREA_TERMS,
    )

    profile.hard_skills = detect_from_dictionary(
        text,
        HARD_SKILL_TERMS,
    )

    profile.tools = detect_from_dictionary(
        text,
        TOOL_TERMS,
    )

    profile.management_skills = detect_from_dictionary(
        text,
        MANAGEMENT_TERMS,
    )

    profile.methodologies = detect_from_dictionary(
        text,
        METHODOLOGY_TERMS,
    )

    profile.languages = detect_from_dictionary(
        text,
        LANGUAGE_TERMS,
    )

    profile.seniority = detect_seniority(
        text,
    )

    profile.evidence_terms = detect_from_dictionary(
        text,
        EVIDENCE_TERMS,
    )

    return profile
