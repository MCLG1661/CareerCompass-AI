from dataclasses import dataclass


@dataclass
class InterviewStep:
    number: int
    title: str
    question: str


INTERVIEW_STEPS = [
    InterviewStep(
        1,
        "Apresentação profissional",
        (
            "Como você apresentaria brevemente seu perfil profissional, "
            "sua trajetória e as principais competências que o qualificam "
            "para esta oportunidade?"
        ),
    ),
    InterviewStep(
        2,
        "Experiência e trajetória",
        (
            "Conte sobre uma experiência profissional relevante em que "
            "você utilizou dados, indicadores ou análise para apoiar uma "
            "decisão ou resolver um problema."
        ),
    ),
    InterviewStep(
        3,
        "Competências relacionadas à função",
        (
            "Como você utiliza suas competências técnicas para transformar "
            "dados em informações úteis para as áreas de negócio?"
        ),
    ),
    InterviewStep(
        4,
        "Situação ou problema profissional",
        (
            "Conte sobre uma situação profissional em que você identificou "
            "um problema, tomou uma ação e conseguiu gerar algum resultado "
            "ou melhoria."
        ),
    ),
    InterviewStep(
        5,
        "Motivação e aderência",
        (
            "O que motiva você a buscar esta oportunidade e como acredita "
            "que sua experiência pode gerar valor para a empresa?"
        ),
    ),
    InterviewStep(
        6,
        "Encerramento",
        (
            "Antes de encerrarmos, há alguma informação sobre sua trajetória, "
            "competências ou potencial de contribuição que você gostaria "
            "de acrescentar?"
        ),
    ),
]


def get_step(step_number: int) -> InterviewStep:
    if step_number < 1:
        step_number = 1

    if step_number > len(INTERVIEW_STEPS):
        step_number = len(INTERVIEW_STEPS)

    return INTERVIEW_STEPS[step_number - 1]


def evaluate_answer(answer: str) -> dict:
    text = answer.strip()

    word_count = len(text.split())

    if word_count < 20:
        clarity = "Resposta muito curta"
        recommendation = (
            "Desenvolva um pouco mais a resposta, incluindo contexto, "
            "ação realizada e resultado."
        )

    elif word_count < 60:
        clarity = "Resposta objetiva"
        recommendation = (
            "A estrutura está adequada. Tente incluir uma evidência "
            "concreta ou resultado verificável."
        )

    else:
        clarity = "Resposta bem desenvolvida"
        recommendation = (
            "A resposta apresenta bom nível de detalhe. Mantenha o foco "
            "nos pontos mais relevantes para evitar excesso de informação."
        )

    evidence_terms = [
        "resultado",
        "meta",
        "indicador",
        "kpi",
        "dados",
        "melhoria",
        "redução",
        "aumento",
        "dashboard",
        "sql",
        "python",
        "power bi",
        "excel",
    ]

    found_evidence = [
        term
        for term in evidence_terms
        if term in text.lower()
    ]

    if found_evidence:
        evidence = (
            "Foram identificadas evidências ou termos concretos: "
            + ", ".join(found_evidence)
        )
    else:
        evidence = (
            "A resposta ainda pode ganhar força com exemplos, "
            "ferramentas ou resultados concretos."
        )

    return {
        "word_count": word_count,
        "clarity": clarity,
        "evidence": evidence,
        "recommendation": recommendation,
    }
