from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# =========================================================
# MODELOS
# =========================================================

@dataclass
class InterviewStep:
    number: int
    title: str
    question: str
    objective: str = ""
    target_skills: list[str] | None = None
    question_type: str = "general"


# =========================================================
# ETAPAS BASE
# =========================================================

BASE_STEPS = {
    1: InterviewStep(
        number=1,
        title="Apresentação profissional",
        question=(
            "Faça uma breve apresentação sobre sua trajetória profissional "
            "e explique quais experiências considera mais relevantes "
            "para esta oportunidade."
        ),
        objective=(
            "Avaliar clareza, síntese, posicionamento e conexão "
            "entre trajetória e oportunidade."
        ),
        target_skills=[],
        question_type="presentation",
    ),
    2: InterviewStep(
        number=2,
        title="Experiência e trajetória",
        question=(
            "Conte sobre uma experiência profissional relevante em que "
            "você teve responsabilidade direta sobre uma entrega, projeto, "
            "operação ou resultado importante."
        ),
        objective=(
            "Identificar escopo de responsabilidade, autonomia, "
            "complexidade e impacto."
        ),
        target_skills=[],
        question_type="experience",
    ),
    3: InterviewStep(
        number=3,
        title="Competências relacionadas à função",
        question=(
            "Quais competências da sua experiência profissional você "
            "considera mais aderentes a esta oportunidade? "
            "Dê exemplos concretos."
        ),
        objective=(
            "Avaliar evidências relacionadas aos principais "
            "requisitos da oportunidade."
        ),
        target_skills=[],
        question_type="competency",
    ),
    4: InterviewStep(
        number=4,
        title="Situação profissional desafiadora",
        question=(
            "Descreva uma situação profissional desafiadora. "
            "Explique o contexto, sua responsabilidade, as ações tomadas "
            "e o resultado alcançado."
        ),
        objective=(
            "Avaliar capacidade de estruturar respostas com contexto, "
            "ação, decisão e resultado."
        ),
        target_skills=[],
        question_type="behavioral",
    ),
    5: InterviewStep(
        number=5,
        title="Motivação e aderência",
        question=(
            "Por que esta oportunidade faz sentido para o seu momento "
            "profissional e de que forma sua experiência pode gerar "
            "valor para a organização?"
        ),
        objective=(
            "Avaliar motivação, coerência de carreira e proposta de valor."
        ),
        target_skills=[],
        question_type="motivation",
    ),
    6: InterviewStep(
        number=6,
        title="Encerramento",
        question=(
            "Existe algum aspecto da sua trajetória, experiência ou "
            "qualificação que ainda não abordamos e que você considera "
            "importante destacar para esta oportunidade?"
        ),
        objective=(
            "Permitir complementação estratégica da narrativa profissional."
        ),
        target_skills=[],
        question_type="closing",
    ),
}


# =========================================================
# HELPERS
# =========================================================

def _unique(items: list[str]) -> list[str]:
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


def _safe_attribute(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _clean_text(text: str) -> str:
    if not text:
        return ""

    return " ".join(
        text.replace("\n", " ").replace("\r", " ").split()
    )


def _contains_number(text: str) -> bool:
    return bool(re.search(r"\d", text))


def _detect_evidence_terms(answer: str) -> list[str]:
    text = answer.casefold()

    vocabulary = {
        "resultado": [
            "resultado", "resultados", "atingi", "atingimos",
            "alcancei", "alcançamos", "alcancamos", "entreguei",
            "entregamos",
        ],
        "indicador": [
            "indicador", "indicadores", "kpi", "kpis",
        ],
        "meta": [
            "meta", "metas",
        ],
        "dados": [
            "dados", "data analytics", "analytics",
        ],
        "melhoria": [
            "melhoria", "melhoramos", "melhorei",
            "otimização", "otimizacao",
        ],
        "redução": [
            "redução", "reducao", "reduzi",
        ],
        "crescimento": [
            "crescimento", "cresceu", "aumento", "aumentei",
        ],
        "liderança": [
            "liderança", "lideranca", "liderei", "equipe",
            "equipes",
        ],
        "stakeholders": [
            "stakeholder", "stakeholders",
        ],
        "projeto": [
            "projeto", "projetos",
        ],
        "operação": [
            "operação", "operacao", "operações", "operacoes",
        ],
        "decisão": [
            "decisão", "decisao", "decisões", "decisoes",
        ],
    }

    detected = []

    for label, terms in vocabulary.items():
        if any(term in text for term in terms):
            detected.append(label)

    return _unique(detected)


def _detect_star_structure(answer: str) -> dict[str, bool]:
    """
    Heurística ampliada para identificar componentes STAR.

    A versão anterior era muito restritiva para Contexto.
    Aqui incluímos expressões naturais como:
    - "em uma operação..."
    - "o desafio era..."
    - "havia a necessidade..."
    - "naquele cenário..."
    """

    text = answer.casefold()

    situation_terms = [
        "contexto",
        "situação",
        "situacao",
        "cenário",
        "cenario",
        "quando",
        "na época",
        "na epoca",
        "em uma operação",
        "em uma operacao",
        "em um projeto",
        "em uma empresa",
        "o desafio era",
        "o desafio foi",
        "havia a necessidade",
        "havia necessidade",
        "naquele momento",
        "naquele cenário",
        "naquele cenario",
        "durante uma operação",
        "durante uma operacao",
        "durante um projeto",
    ]

    task_terms = [
        "responsável",
        "responsavel",
        "minha responsabilidade",
        "meu objetivo",
        "minha missão",
        "minha missao",
        "precisávamos",
        "precisavamos",
        "eu precisava",
        "cabia a mim",
        "fiquei responsável",
        "fiquei responsavel",
    ]

    action_terms = [
        "implementei",
        "estruturei",
        "conduzi",
        "liderei",
        "analisei",
        "negociei",
        "desenvolvi",
        "criei",
        "organizei",
        "coordenei",
        "decidi",
        "realizei",
        "acompanhei",
        "defini",
        "reorganizei",
        "automatizei",
        "priorizei",
        "como ação",
        "como acao",
    ]

    result_terms = [
        "resultado",
        "resultados",
        "como resultado",
        "atingimos",
        "atingi",
        "alcançamos",
        "alcancamos",
        "alcancei",
        "aumentou",
        "reduziu",
        "melhorou",
        "entregamos",
        "entreguei",
        "gerou",
        "permitiu",
    ]

    return {
        "situation": any(term in text for term in situation_terms),
        "task": any(term in text for term in task_terms),
        "action": any(term in text for term in action_terms),
        "result": (
            any(term in text for term in result_terms)
            or _contains_number(answer)
        ),
    }


def _detect_motivation_signals(answer: str) -> dict[str, bool]:
    text = answer.casefold()

    return {
        "motivation": any(
            term in text
            for term in [
                "faz sentido",
                "momento profissional",
                "interesse",
                "oportunidade",
                "motivação",
                "motivacao",
                "busco",
                "quero",
            ]
        ),
        "career_coherence": any(
            term in text
            for term in [
                "trajetória",
                "trajetoria",
                "experiência",
                "experiencia",
                "ao longo",
                "carreira",
                "histórico",
                "historico",
            ]
        ),
        "value_proposition": any(
            term in text
            for term in [
                "gerar valor",
                "contribuir",
                "posso contribuir",
                "posso gerar",
                "resultados",
                "eficiência",
                "eficiencia",
                "melhoria",
                "decisões",
                "decisoes",
            ]
        ),
        "role_connection": any(
            term in text
            for term in [
                "gestão de projetos",
                "gestao de projetos",
                "operações",
                "operacoes",
                "performance",
                "dados",
                "business intelligence",
                "power bi",
                "python",
                "stakeholders",
            ]
        ),
    }


def _detect_presentation_signals(answer: str) -> dict[str, bool]:
    text = answer.casefold()

    return {
        "trajectory": any(
            term in text
            for term in [
                "trajetória",
                "trajetoria",
                "experiência",
                "experiencia",
                "ao longo",
                "atuo",
                "atuei",
                "carreira",
            ]
        ),
        "positioning": any(
            term in text
            for term in [
                "gestão de projetos",
                "gestao de projetos",
                "operações",
                "operacoes",
                "marketing",
                "performance",
                "dados",
                "analytics",
                "business intelligence",
                "inteligência artificial",
                "inteligencia artificial",
            ]
        ),
        "value": any(
            term in text
            for term in [
                "gerar valor",
                "resultado",
                "resultados",
                "eficiência",
                "eficiencia",
                "melhoria",
                "decisão",
                "decisao",
                "decisões",
                "decisoes",
            ]
        ),
    }


def _detect_closing_signals(answer: str) -> dict[str, bool]:
    text = answer.casefold()

    return {
        "relevance": any(
            term in text
            for term in [
                "importante destacar",
                "considero importante",
                "trajetória",
                "trajetoria",
                "experiência",
                "experiencia",
                "qualificação",
                "qualificacao",
            ]
        ),
        "differentiation": any(
            term in text
            for term in [
                "diferencial",
                "combinação",
                "combinacao",
                "conectar",
                "integra",
                "multidisciplinar",
                "atualização",
                "atualizacao",
                "tecnologia",
                "dados",
                "inteligência artificial",
                "inteligencia artificial",
            ]
        ),
        "value": any(
            term in text
            for term in [
                "gerar valor",
                "contribuir",
                "melhorar processos",
                "eficiência",
                "eficiencia",
                "decisões",
                "decisoes",
                "resultados",
            ]
        ),
        "concise_close": 40 <= len(answer.split()) <= 160,
    }


def _word_count_score(word_count: int) -> int:
    if 40 <= word_count <= 180:
        return 100

    if 25 <= word_count < 40:
        return 70

    if 180 < word_count <= 230:
        return 75

    if 15 <= word_count < 25:
        return 45

    if 230 < word_count <= 300:
        return 45

    return 25


def _evidence_score(
    evidence_terms: list[str],
    has_number: bool,
) -> int:
    score = min(len(evidence_terms) * 12, 72)

    if has_number:
        score += 28

    return min(score, 100)


def _target_skill_score(
    target_skills: list[str],
    skills_mentioned: list[str],
) -> int | None:
    if not target_skills:
        return None

    return round(
        len(skills_mentioned)
        / len(target_skills)
        * 100
    )


def _classify_performance(score: int) -> str:
    if score >= 85:
        return "Muito forte"

    if score >= 70:
        return "Forte"

    if score >= 55:
        return "Boa"

    if score >= 40:
        return "Parcial"

    return "Precisa de desenvolvimento"


def _infer_question_type(
    step_number: int | None,
    question_type: str | None = None,
) -> str:
    if question_type:
        return question_type

    mapping = {
        1: "presentation",
        2: "experience",
        3: "competency",
        4: "behavioral",
        5: "motivation",
        6: "closing",
    }

    return mapping.get(
        step_number,
        "general",
    )


# =========================================================
# GERAÇÃO CONTEXTUAL DE PERGUNTAS
# =========================================================

def get_step(
    step_number: int,
    job_title: str = "",
    ats_report: Any = None,
    tailoring_report: Any = None,
) -> InterviewStep:
    base = BASE_STEPS.get(
        step_number,
        BASE_STEPS[1],
    )

    question = base.question
    objective = base.objective
    question_type = base.question_type
    target_skills: list[str] = []

    job_title = _clean_text(job_title)

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

    mandatory_gaps = _unique(
        list(
            _safe_attribute(
                ats_report,
                "mandatory_gaps",
                [],
            )
            or []
        )
    )

    priority_skills = _unique(
        list(
            _safe_attribute(
                tailoring_report,
                "priority_skills",
                [],
            )
            or []
        )
    )

    if not priority_skills:
        priority_skills = strengths

    if step_number == 1:
        if job_title:
            question = (
                f"Considerando a oportunidade de {job_title}, "
                f"faça uma apresentação breve da sua trajetória "
                f"profissional e destaque as experiências que mais "
                f"se conectam a esta função."
            )

        target_skills = priority_skills[:4]

    elif step_number == 2:
        if priority_skills:
            skills_text = ", ".join(
                priority_skills[:3]
            )

            question = (
                f"Conte sobre uma experiência profissional em que "
                f"você aplicou competências relacionadas a "
                f"{skills_text}. "
                f"Explique o contexto, sua responsabilidade, "
                f"as decisões tomadas e o resultado."
            )

            target_skills = priority_skills[:3]

    elif step_number == 3:
        if priority_skills:
            skills_text = ", ".join(
                priority_skills[:4]
            )

            question = (
                f"A oportunidade apresenta aderência com competências "
                f"como {skills_text}. "
                f"Escolha duas delas e apresente exemplos concretos "
                f"de como você as utilizou profissionalmente."
            )

            target_skills = priority_skills[:4]

    elif step_number == 4:
        question = (
            "Descreva uma situação profissional desafiadora "
            "utilizando a estrutura Contexto → Responsabilidade → "
            "Ação → Resultado. Priorize um exemplo relevante para "
            "esta oportunidade."
        )

        target_skills = priority_skills[:3]

    elif step_number == 5:
        if mandatory_gaps:
            gap_text = ", ".join(
                mandatory_gaps[:2]
            )

            question = (
                f"Esta oportunidade apresenta alguns requisitos "
                f"para os quais não encontramos evidência suficiente "
                f"no currículo, como {gap_text}. "
                f"Como você responderia a um recrutador sobre esses "
                f"pontos sem exagerar sua experiência e demonstrando "
                f"competências transferíveis ou capacidade de aprendizado?"
            )

            target_skills = mandatory_gaps[:2]

        elif job_title:
            question = (
                f"Por que a oportunidade de {job_title} faz sentido "
                f"para sua trajetória e quais aspectos da sua experiência "
                f"podem gerar maior valor para a organização?"
            )

    elif step_number == 6:
        if job_title:
            question = (
                f"Antes de encerrarmos a entrevista para "
                f"{job_title}, qual mensagem principal você gostaria "
                f"que o recrutador lembrasse sobre seu perfil profissional?"
            )

    return InterviewStep(
        number=base.number,
        title=base.title,
        question=question,
        objective=objective,
        target_skills=target_skills,
        question_type=question_type,
    )


# =========================================================
# AVALIAÇÃO DA RESPOSTA
# =========================================================

def evaluate_answer(
    answer: str,
    target_skills: list[str] | None = None,
    step_number: int | None = None,
    question_type: str | None = None,
) -> dict:
    """
    Coach 2.1

    A régua muda de acordo com o tipo da pergunta.

    Compatibilidade preservada:
        evaluate_answer(answer)

    Uso contextual:
        evaluate_answer(
            answer,
            target_skills=[...],
            step_number=4,
            question_type="behavioral",
        )
    """

    answer = answer.strip()
    word_count = len(answer.split())

    target_skills = _unique(
        target_skills or []
    )

    effective_question_type = _infer_question_type(
        step_number=step_number,
        question_type=question_type,
    )

    evidence_terms = _detect_evidence_terms(
        answer
    )

    has_number = _contains_number(
        answer
    )

    star = _detect_star_structure(
        answer
    )

    star_points = sum(
        1
        for value in star.values()
        if value
    )

    star_score_raw = round(
        star_points / 4 * 100
    )

    # STAR só é obrigatório no behavioral.
    if effective_question_type == "behavioral":
        star_score: int | None = star_score_raw
    elif effective_question_type in {
        "experience",
        "competency",
    }:
        star_score = star_score_raw
    else:
        star_score = None

    if word_count < 25:
        clarity = "Resposta muito curta"
    elif word_count < 60:
        clarity = "Resposta objetiva"
    elif word_count <= 180:
        clarity = "Resposta bem desenvolvida"
    elif word_count <= 250:
        clarity = "Resposta detalhada"
    else:
        clarity = "Resposta extensa — considere maior síntese"

    evidence_parts = []

    if evidence_terms:
        evidence_parts.append(
            "Foram identificadas evidências ou termos concretos: "
            + ", ".join(evidence_terms)
        )

    if has_number:
        evidence_parts.append(
            "A resposta utiliza dado ou indicador quantitativo."
        )

    if not evidence_parts:
        if effective_question_type == "behavioral":
            evidence = (
                "Poucas evidências concretas foram identificadas. "
                "Considere explicitar contexto, ação e resultado."
            )
        else:
            evidence = (
                "Poucas evidências concretas foram identificadas. "
                "Considere tornar a resposta mais específica e conectada "
                "à oportunidade."
            )
    else:
        evidence = " ".join(evidence_parts)

    skills_mentioned = []

    if target_skills:
        answer_lower = answer.casefold()

        for skill in target_skills:
            if skill.casefold() in answer_lower:
                skills_mentioned.append(skill)

    length_score = _word_count_score(
        word_count
    )

    evidence_score = _evidence_score(
        evidence_terms,
        has_number,
    )

    target_score = _target_skill_score(
        target_skills,
        skills_mentioned,
    )

    recommendations: list[str] = []
    rubric_scores: dict[str, int] = {}

    # =====================================================
    # PRESENTATION
    # =====================================================

    if effective_question_type == "presentation":
        signals = _detect_presentation_signals(
            answer
        )

        positioning_score = round(
            sum(signals.values())
            / len(signals)
            * 100
        )

        fit_score = (
            target_score
            if target_score is not None
            else positioning_score
        )

        score = round(
            length_score * 0.20
            + positioning_score * 0.30
            + fit_score * 0.30
            + evidence_score * 0.20
        )

        rubric_scores = {
            "clareza": length_score,
            "posicionamento": positioning_score,
            "aderencia": fit_score,
            "evidencias": evidence_score,
        }

        if positioning_score < 70:
            recommendations.append(
                "Deixe mais claro seu posicionamento profissional, "
                "conectando trajetória, competências e proposta de valor."
            )

        if target_score is not None and target_score < 50:
            recommendations.append(
                "Conecte a apresentação de forma mais explícita "
                "às competências prioritárias da oportunidade."
            )

    # =====================================================
    # EXPERIENCE
    # =====================================================

    elif effective_question_type == "experience":
        responsibility_score = 100 if star["task"] else 55
        impact_score = 100 if star["result"] else evidence_score
        structure_score = star_score_raw

        score = round(
            length_score * 0.15
            + responsibility_score * 0.25
            + evidence_score * 0.20
            + impact_score * 0.20
            + structure_score * 0.20
        )

        rubric_scores = {
            "clareza": length_score,
            "responsabilidade": responsibility_score,
            "evidencias": evidence_score,
            "impacto": impact_score,
            "estrutura": structure_score,
        }

        if not star["task"]:
            recommendations.append(
                "Explicite melhor qual era sua responsabilidade direta."
            )

        if not star["result"]:
            recommendations.append(
                "Inclua o resultado ou impacto da experiência, "
                "sempre com evidências reais."
            )

    # =====================================================
    # COMPETENCY
    # =====================================================

    elif effective_question_type == "competency":
        competence_score = (
            target_score
            if target_score is not None
            else min(
                100,
                50 + len(evidence_terms) * 10,
            )
        )

        example_score = round(
            star_score_raw * 0.60
            + evidence_score * 0.40
        )

        score = round(
            length_score * 0.15
            + competence_score * 0.35
            + example_score * 0.30
            + evidence_score * 0.20
        )

        rubric_scores = {
            "clareza": length_score,
            "competencias": competence_score,
            "exemplos": example_score,
            "evidencias": evidence_score,
        }

        if target_score is not None and target_score < 50:
            recommendations.append(
                "Mencione de forma mais explícita as competências "
                "prioritárias da oportunidade e associe cada uma a um exemplo."
            )

        if example_score < 65:
            recommendations.append(
                "Use exemplos mais concretos para demonstrar como "
                "as competências foram aplicadas."
            )

    # =====================================================
    # BEHAVIORAL
    # =====================================================

    elif effective_question_type == "behavioral":
        score = round(
            length_score * 0.15
            + star_score_raw * 0.45
            + evidence_score * 0.25
            + (
                target_score
                if target_score is not None
                else 70
            ) * 0.15
        )

        rubric_scores = {
            "clareza": length_score,
            "star": star_score_raw,
            "evidencias": evidence_score,
            "competencias": (
                target_score
                if target_score is not None
                else 70
            ),
        }

        if star_score_raw < 100:
            missing_star = []

            if not star["situation"]:
                missing_star.append("contexto")

            if not star["task"]:
                missing_star.append("responsabilidade")

            if not star["action"]:
                missing_star.append("ação")

            if not star["result"]:
                missing_star.append("resultado")

            if missing_star:
                recommendations.append(
                    "Fortaleça a estrutura STAR incluindo: "
                    + ", ".join(missing_star)
                    + "."
                )

        if not has_number:
            recommendations.append(
                "Sempre que houver evidência real, inclua indicadores, "
                "volumes, percentuais ou resultados mensuráveis."
            )

    # =====================================================
    # MOTIVATION
    # =====================================================

    elif effective_question_type == "motivation":
        signals = _detect_motivation_signals(
            answer
        )

        motivation_score = 100 if signals["motivation"] else 55
        coherence_score = 100 if signals["career_coherence"] else 55
        value_score = 100 if signals["value_proposition"] else 50
        fit_score = 100 if signals["role_connection"] else 55

        score = round(
            length_score * 0.15
            + motivation_score * 0.25
            + coherence_score * 0.20
            + value_score * 0.25
            + fit_score * 0.15
        )

        rubric_scores = {
            "clareza": length_score,
            "motivacao": motivation_score,
            "coerencia": coherence_score,
            "proposta_de_valor": value_score,
            "aderencia": fit_score,
        }

        if motivation_score < 70:
            recommendations.append(
                "Explique com mais clareza por que a oportunidade "
                "faz sentido para seu momento profissional."
            )

        if value_score < 70:
            recommendations.append(
                "Torne mais explícita sua proposta de valor: "
                "como sua experiência pode contribuir para a organização."
            )

        if fit_score < 70:
            recommendations.append(
                "Conecte sua trajetória aos principais desafios "
                "e responsabilidades da função."
            )

    # =====================================================
    # CLOSING
    # =====================================================

    elif effective_question_type == "closing":
        signals = _detect_closing_signals(
            answer
        )

        relevance_score = 100 if signals["relevance"] else 60
        differentiation_score = (
            100 if signals["differentiation"] else 55
        )
        value_score = 100 if signals["value"] else 60
        synthesis_score = (
            100 if signals["concise_close"] else length_score
        )

        score = round(
            relevance_score * 0.30
            + differentiation_score * 0.30
            + value_score * 0.20
            + synthesis_score * 0.20
        )

        rubric_scores = {
            "relevancia": relevance_score,
            "diferenciacao": differentiation_score,
            "valor": value_score,
            "sintese": synthesis_score,
        }

        if differentiation_score < 70:
            recommendations.append(
                "Use o encerramento para reforçar um diferencial "
                "que ainda não tenha ficado claro durante a entrevista."
            )

        if value_score < 70:
            recommendations.append(
                "Feche conectando esse diferencial ao valor "
                "que você pode gerar na função."
            )

    # =====================================================
    # GENERAL / FALLBACK
    # =====================================================

    else:
        score = round(
            length_score * 0.30
            + evidence_score * 0.35
            + (
                target_score
                if target_score is not None
                else 70
            ) * 0.35
        )

        rubric_scores = {
            "clareza": length_score,
            "evidencias": evidence_score,
            "aderencia": (
                target_score
                if target_score is not None
                else 70
            ),
        }

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    performance = _classify_performance(
        score
    )

    if word_count < 25:
        recommendations.append(
            "Desenvolva um pouco mais a resposta."
        )

    if word_count > 230:
        recommendations.append(
            "Reduza detalhes secundários e concentre a resposta "
            "nos elementos diretamente relacionados à pergunta."
        )

    if (
        effective_question_type
        in {"experience", "competency", "behavioral"}
        and not has_number
    ):
        recommendations.append(
            "Sempre que houver evidência real, inclua indicadores, "
            "volumes, percentuais ou outros resultados mensuráveis."
        )

    if not recommendations:
        recommendations.append(
            "A resposta está bem estruturada para este tipo de pergunta. "
            "Mantenha o foco em clareza, evidências e conexão "
            "com a oportunidade."
        )

    recommendation = " ".join(
        _unique(recommendations)
    )

    return {
        # Compatibilidade com UI atual
        "clarity": clarity,
        "evidence": evidence,
        "recommendation": recommendation,
        "word_count": word_count,

        # Coach 2.1
        "score": score,
        "performance": performance,
        "question_type": effective_question_type,
        "rubric_scores": rubric_scores,
        "star_score": star_score,
        "star": star,
        "target_skills": target_skills,
        "skills_mentioned": skills_mentioned,
        "evidence_terms": evidence_terms,
        "has_quantitative_evidence": has_number,
        "step_number": step_number,
    }
