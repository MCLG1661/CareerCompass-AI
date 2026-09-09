"""
CareerCompass AI
Sprint 5.3C — Opportunity Intelligence + Strategic Fit Integration Test
"""

from opportunity_engine import analyze_opportunity
from strategic_fit_engine import analyze_strategic_fit


def career_direction() -> dict:
    return {
        "id": "direction-integration-test",
        "is_active": True,
        "target_roles": ["Head de Data & AI", "Gerente de Transformação Digital"],
        "target_seniority": "Executiva / Liderança",
        "target_areas": ["Dados", "Inteligência Artificial", "Transformação Digital"],
        "target_industries": ["Tecnologia", "Serviços"],
        "work_modes": ["Híbrido", "Remoto"],
        "target_locations": ["Rio de Janeiro", "São Paulo", "Portugal"],
        "relocation_available": True,
        "salary_min": 22000,
        "salary_currency": "BRL",
        "time_horizon_months": 30,
        "priorities": {"growth": 5, "leadership": 5, "learning": 4, "compensation": 4},
        "constraints": {"avoid_roles_below_seniority": True},
        "career_goal": "Consolidar liderança na interseção entre gestão, dados, IA e transformação digital.",
    }


def test_opportunity_profile_to_strategic_fit():
    description = """
Localização: São Paulo
Modelo híbrido.

Responsabilidades:
- Liderar a estratégia de Data & AI da companhia.
- Gerenciar times multidisciplinares de dados e inteligência artificial.
- Conduzir iniciativas de transformação digital.
- Apoiar crescimento, inovação e decisões de negócio orientadas por dados.

Requisitos obrigatórios:
- Experiência em liderança de equipes.
- Experiência com Data Analytics e Inteligência Artificial.
- Conhecimento de Python, SQL e cloud.

Diferenciais:
- Machine Learning.
- Transformação Digital.
"""
    opportunity = analyze_opportunity(
        job_title="Head de Data & AI",
        job_description=description,
        company="CareerCompass Test Company",
    )

    assert opportunity.job_title == "Head de Data & AI"
    assert opportunity.seniority == "Executivo"
    assert opportunity.work_model == "Híbrido"
    assert opportunity.location == "São Paulo"
    assert "Inteligência Artificial" in opportunity.skills
    assert opportunity.leadership_signals

    result = analyze_strategic_fit(career_direction(), opportunity)

    assert result.available is True
    assert result.score is not None
    assert result.score >= 80
    assert result.classification in {"Strategic Priority", "Strong Direction"}
    assert result.dimensions["role_alignment"].evaluated is True
    assert result.dimensions["seniority_alignment"].evaluated is True
    assert result.dimensions["work_location_alignment"].evaluated is True

    compensation = result.dimensions["compensation_alignment"]
    assert compensation.evaluated is False
    assert compensation.score is None
    assert any("Compensation Alignment" in item for item in result.unknowns)


def test_low_strategic_alignment_from_real_parser():
    description = """
Localização: Curitiba
Atuação presencial.

Responsabilidades:
- Executar rotinas administrativas.
- Organizar documentos e controles internos.
- Apoiar atividades operacionais.

Requisitos obrigatórios:
- Excel.
- Organização.
"""
    opportunity = analyze_opportunity(
        job_title="Assistente Administrativo Júnior",
        job_description=description,
        company="CareerCompass Test Company",
    )

    assert opportunity.seniority == "Júnior"
    assert opportunity.work_model == "Presencial"
    assert opportunity.location == "Curitiba"

    result = analyze_strategic_fit(career_direction(), opportunity)

    assert result.available is True
    assert result.score is not None
    assert result.score < 55
    assert result.classification in {"Weak Direction", "Strategic Detour"}
    assert result.warnings
    assert result.recommendation != "Priorizar"


def test_missing_direction_is_explicit():
    opportunity = analyze_opportunity(
        job_title="Gerente de Transformação Digital",
        job_description="""
Modelo remoto.

Responsabilidades:
- Liderar programas de transformação digital.
- Gerenciar stakeholders e iniciativas estratégicas.

Requisitos obrigatórios:
- Liderança.
- Gestão de projetos.
""",
    )

    result = analyze_strategic_fit(None, opportunity)

    assert result.available is False
    assert result.score is None
    assert result.classification == "Direction Required"


def run():
    tests = [
        test_opportunity_profile_to_strategic_fit,
        test_low_strategic_alignment_from_real_parser,
        test_missing_direction_is_explicit,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print()
    print("SPRINT 5.3C VALIDADO: Opportunity Intelligence -> Strategic Fit integrado com sucesso.")


if __name__ == "__main__":
    run()
