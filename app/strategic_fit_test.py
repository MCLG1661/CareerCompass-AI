"""
CareerCompass AI
Sprint 5.3B — Strategic Fit Engine Isolated Test
"""

from strategic_fit_engine import analyze_strategic_fit


def direction():
    return {
        "id": "direction-test",
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


def test_strong_direction():
    op = {
        "job_title": "Head de Data & AI",
        "seniority": "Executivo",
        "work_model": "Híbrido",
        "location": "São Paulo",
        "industry": "Tecnologia",
        "salary_min": 26000,
        "salary_currency": "BRL",
        "skills": ["Data Analytics", "Inteligência Artificial", "Machine Learning"],
        "responsibilities": [
            "Liderar times de dados e IA",
            "Conduzir transformação digital e estratégia de crescimento",
        ],
        "leadership_signals": ["liderança", "gestão de pessoas"],
        "business_signals": ["crescimento", "estratégia", "receita"],
        "raw_description": "Liderança executiva de Data & AI em empresa de tecnologia.",
    }
    r = analyze_strategic_fit(direction(), op)
    assert r.available
    assert r.score is not None and r.score >= 85
    assert r.classification == "Strategic Priority"
    assert r.recommendation == "Priorizar"
    assert r.confidence_score == 100.0


def test_unknown_salary_not_zero():
    op = {
        "job_title": "Head de Data & AI",
        "seniority": "Executivo",
        "work_model": "Remoto",
        "location": "Portugal",
        "industry": "Tecnologia",
        "skills": ["Data Analytics", "Inteligência Artificial"],
        "leadership_signals": ["liderança"],
        "business_signals": ["crescimento", "estratégia"],
        "raw_description": "Posição executiva para liderar Data & AI.",
    }
    r = analyze_strategic_fit(direction(), op)
    d = r.dimensions["compensation_alignment"]
    assert d.evaluated is False
    assert d.score is None
    assert any("Compensation Alignment" in x for x in r.unknowns)
    assert r.score is not None and r.score > 70
    assert r.confidence_score < 100.0


def test_detour():
    op = {
        "job_title": "Assistente Administrativo",
        "seniority": "Júnior",
        "work_model": "Presencial",
        "location": "Curitiba",
        "industry": "Indústria",
        "salary_min": 5000,
        "salary_currency": "BRL",
        "responsibilities": ["Rotinas administrativas e suporte operacional"],
        "raw_description": "Atuação administrativa presencial.",
    }
    r = analyze_strategic_fit(direction(), op)
    assert r.available
    assert r.score is not None and r.score < 40
    assert r.classification == "Strategic Detour"
    assert r.warnings


def test_below_seniority_constraint():
    op = {
        "job_title": "Analista Sênior de Dados",
        "seniority": "Sênior",
        "work_model": "Híbrido",
        "location": "Rio de Janeiro",
        "industry": "Tecnologia",
        "skills": ["Data Analytics", "Python", "SQL"],
        "raw_description": "Análise de dados e automação.",
    }
    r = analyze_strategic_fit(direction(), op)
    assert r.warnings
    assert r.dimensions["seniority_alignment"].score == 20.0
    assert r.recommendation != "Priorizar"


def test_direction_required():
    r = analyze_strategic_fit(None, {"job_title": "Head de Data & AI"})
    assert not r.available
    assert r.score is None
    assert r.classification == "Direction Required"


def run():
    tests = [
        test_strong_direction,
        test_unknown_salary_not_zero,
        test_detour,
        test_below_seniority_constraint,
        test_direction_required,
    ]
    for fn in tests:
        fn()
        print(f"PASS: {fn.__name__}")
    print("SPRINT 5.3B VALIDADO: todos os cenários passaram.")


if __name__ == "__main__":
    run()
