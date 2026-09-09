"""
CareerCompass AI — Strategic Fit Engine
Sprint 5.3B

Deterministic, explainable strategic alignment between an active Career Direction
and an opportunity. Missing data is never treated as incompatibility.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any
import re
import unicodedata


@dataclass
class StrategicDimension:
    name: str
    weight: float
    score: float | None
    evaluated: bool
    explanation: str
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StrategicFitResult:
    available: bool
    score: float | None
    classification: str
    recommendation: str
    confidence_score: float
    evaluated_weight: float
    dimensions: dict[str, StrategicDimension]
    drivers: list[str] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


WEIGHTS = {
    "role_alignment": 25.0,
    "seniority_alignment": 20.0,
    "area_industry_alignment": 15.0,
    "work_location_alignment": 10.0,
    "compensation_alignment": 10.0,
    "strategic_priorities": 20.0,
}

SENIORITY = {
    "estagio": 1, "estagiario": 1,
    "junior": 2, "jr": 2,
    "pleno": 3, "mid level": 3,
    "senior": 4, "especialista": 4,
    "coordenador": 5, "coordenadora": 5, "coordenacao": 5,
    "gerente": 5, "gerencia": 5, "gerencial": 5, "manager": 5, "lideranca": 5,
    "executivo": 6, "executiva": 6, "diretor": 6, "diretora": 6,
    "diretoria": 6, "head": 6,
    "vp": 7, "vice president": 7, "c level": 7, "ceo": 7, "coo": 7,
    "cmo": 7, "cto": 7, "cdo": 7,
}

ROLE_FAMILIES = {
    "data_ai": {"data","dados","analytics","analise","ai","ia","artificial","inteligencia","machine","learning","bi"},
    "digital": {"transformacao","digital","technology","tecnologia","automation","automacao","inovacao","innovation"},
    "commercial": {"comercial","sales","vendas","business","negocios","account","revenue","receita"},
    "marketing": {"marketing","growth","brand","marca","media","performance","crm"},
    "operations": {"operacoes","operations","processos","process","logistica","logistics"},
    "projects": {"projetos","project","pmo","program","portfolio","agile","scrum"},
    "product": {"product","produto","produtos"},
    "customer": {"customer","cliente","clientes","success","experience","cx"},
}

GROWTH_TERMS = {"growth","crescimento","expansao","expansion","strategy","estrategia","transformacao","transformation","innovation","inovacao","revenue","receita"}
LEADERSHIP_TERMS = {"lideranca","leadership","gestao de pessoas","people management","team management","liderar","lead team","diretor","director","head","gerente","manager"}
LEARNING_TERMS = {"data","dados","analytics","ai","ia","artificial intelligence","machine learning","cloud","python","sql","automation","automacao","digital","transformacao","innovation","inovacao"}


def _plain(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+#./ -]+", " ", text)).strip()


def _tokens(value: Any) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9+#]+", _plain(value)) if len(t) > 1}


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(x).strip() for x in value if str(x).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _obj(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    keys = (
        "job_title","company","seniority","work_model","location","industry","sector",
        "mandatory_requirements","preferred_requirements","skills","tools",
        "methodologies","responsibilities","leadership_signals","business_signals",
        "keywords","raw_description","salary_min","salary_max","salary_currency",
        "compensation_min","compensation_max","compensation_currency",
    )
    return {k: getattr(value, k) for k in keys if hasattr(value, k)}


def _text(op: dict[str, Any]) -> str:
    parts = [str(op.get(k) or "") for k in ("job_title","company","seniority","work_model","location","industry","sector","raw_description")]
    for k in ("mandatory_requirements","preferred_requirements","skills","tools","methodologies","responsibilities","leadership_signals","business_signals","keywords"):
        parts.extend(_list(op.get(k)))
    return " ".join(parts)


def _families(value: Any) -> set[str]:
    tokens = _tokens(value)
    return {name for name, terms in ROLE_FAMILIES.items() if tokens.intersection({_plain(t) for t in terms})}


def _level(value: Any) -> int | None:
    text = _plain(value)
    if not text or text in {"nao identificada","nao identificado"}:
        return None
    found = [level for term, level in SENIORITY.items() if term in text]
    return max(found) if found else None


def _hits(text: str, terms: set[str]) -> list[str]:
    normalized = _plain(text)
    return sorted(t for t in terms if _plain(t) in normalized)


def _role(direction: dict, op: dict) -> StrategicDimension:
    weight = WEIGHTS["role_alignment"]
    targets = _list(direction.get("target_roles"))
    title = str(op.get("job_title") or "").strip()
    if not targets:
        return StrategicDimension("Role Alignment", weight, None, False, "Nenhum cargo-alvo foi definido.")
    if not title:
        return StrategicDimension("Role Alignment", weight, None, False, "A oportunidade não possui título identificável.")

    job_tokens, job_families = _tokens(title), _families(title)
    best, best_target = 0.0, ""
    for target in targets:
        target_tokens = _tokens(target)
        if not target_tokens:
            continue
        inter, union = job_tokens & target_tokens, job_tokens | target_tokens
        lexical = len(inter) / len(union) if union else 0.0
        tf = _families(target)
        family = len(job_families & tf) / len(tf) if tf else 0.0
        substring = 1.0 if _plain(target) in _plain(title) or _plain(title) in _plain(target) else 0.0
        score = max(substring, lexical, lexical * .55 + family * .45) * 100
        if score > best:
            best, best_target = score, target
    score = round(min(100.0, best), 2)
    explanation = (
        f'O cargo "{title}" está fortemente alinhado a "{best_target}".' if score >= 80
        else f'O cargo "{title}" possui alinhamento parcial com "{best_target}".' if score >= 55
        else f'O cargo "{title}" tem baixa proximidade com os cargos-alvo.'
    )
    return StrategicDimension("Role Alignment", weight, score, True, explanation, [f"Cargo: {title}", f"Melhor alvo: {best_target}"])


def _seniority(direction: dict, op: dict) -> tuple[StrategicDimension, bool]:
    weight = WEIGHTS["seniority_alignment"]
    target, current = direction.get("target_seniority"), op.get("seniority")
    a, b = _level(target), _level(current)
    if a is None:
        return StrategicDimension("Seniority Alignment", weight, None, False, "A direção não possui senioridade-alvo avaliável."), False
    if b is None:
        return StrategicDimension("Seniority Alignment", weight, None, False, "A senioridade da oportunidade não foi identificada."), False
    gap = b - a
    score = 100.0 if gap == 0 else 90.0 if gap == 1 else 72.0 if gap > 1 else 55.0 if gap == -1 else 20.0
    msg = (
        "A senioridade coincide com a senioridade-alvo." if gap == 0
        else "A oportunidade está acima da senioridade-alvo." if gap > 0
        else "A oportunidade está um nível abaixo da senioridade-alvo." if gap == -1
        else "A oportunidade está dois ou mais níveis abaixo da senioridade-alvo."
    )
    return StrategicDimension("Seniority Alignment", weight, score, True, msg, [f"Alvo: {target}", f"Vaga: {current}"]), gap < 0


def _area(direction: dict, op: dict) -> StrategicDimension:
    weight = WEIGHTS["area_industry_alignment"]
    areas, industries = _list(direction.get("target_areas")), _list(direction.get("target_industries"))
    if not areas and not industries:
        return StrategicDimension("Area & Industry Alignment", weight, None, False, "Nenhuma área ou setor-alvo foi definido.")
    text, subs, signals = _plain(_text(op)), [], []
    if areas:
        op_families = _families(text)
        matches = [a for a in areas if _plain(a) in text or bool(_families(a) & op_families)]
        subs.append(min(100.0, len(matches) / len(areas) * 100.0))
        if matches:
            signals.append("Áreas aderentes: " + ", ".join(matches))
    if industries:
        explicit = _plain(op.get("industry") or op.get("sector"))
        if explicit:
            matches = [i for i in industries if _plain(i) in explicit or explicit in _plain(i)]
            subs.append(min(100.0, len(matches) / len(industries) * 100.0))
            if matches:
                signals.append("Setores aderentes: " + ", ".join(matches))
        else:
            matches = [i for i in industries if _plain(i) in text]
            if matches:
                subs.append(min(80.0, len(matches) / len(industries) * 80.0))
                signals.append("Setores mencionados: " + ", ".join(matches))
    if not subs:
        return StrategicDimension("Area & Industry Alignment", weight, None, False, "Não há evidência suficiente para avaliar área/setor.")
    score = round(sum(subs) / len(subs), 2)
    return StrategicDimension("Area & Industry Alignment", weight, score, True, "A oportunidade apresenta sinais de alinhamento com áreas/setores." if score >= 55 else "Há baixa evidência de alinhamento com áreas/setores.", signals)


def _work(direction: dict, op: dict) -> StrategicDimension:
    weight = WEIGHTS["work_location_alignment"]
    modes, locations = _list(direction.get("work_modes")), _list(direction.get("target_locations"))
    relocation = bool(direction.get("relocation_available"))
    subs, signals = [], []
    mode = str(op.get("work_model") or "").strip()
    if modes and mode and _plain(mode) not in {"nao identificado","nao identificada"}:
        match = any(_plain(m) in _plain(mode) or _plain(mode) in _plain(m) for m in modes)
        subs.append(100.0 if match else 25.0)
        signals.append(f"Modelo: {mode}")
    location = str(op.get("location") or "").strip()
    if locations and location:
        match = any(_plain(l) in _plain(location) or _plain(location) in _plain(l) for l in locations)
        subs.append(100.0 if match else 70.0 if relocation else 20.0)
        signals.append(f"Localização: {location}")
    if not subs:
        return StrategicDimension("Work & Location Alignment", weight, None, False, "Modelo/localização não possuem evidência suficiente.")
    score = round(sum(subs) / len(subs), 2)
    return StrategicDimension("Work & Location Alignment", weight, score, True, "Modelo/localização são compatíveis." if score >= 70 else "Há trade-offs de modelo/localização.", signals)


def _comp(direction: dict, op: dict) -> StrategicDimension:
    weight = WEIGHTS["compensation_alignment"]
    try:
        target = float(direction.get("salary_min")) if direction.get("salary_min") is not None else None
    except (TypeError, ValueError):
        target = None
    if not target or target <= 0:
        return StrategicDimension("Compensation Alignment", weight, None, False, "Nenhuma remuneração mínima foi definida.")
    salary = None
    for key in ("salary_min","compensation_min","salary_max","compensation_max"):
        try:
            value = float(op.get(key))
            if value > 0:
                salary = value
                break
        except (TypeError, ValueError):
            pass
    if salary is None:
        return StrategicDimension("Compensation Alignment", weight, None, False, "A oportunidade não informa remuneração utilizável.")
    target_currency = str(direction.get("salary_currency") or "BRL").upper()
    currency = str(op.get("salary_currency") or op.get("compensation_currency") or target_currency).upper()
    if currency != target_currency:
        return StrategicDimension("Compensation Alignment", weight, None, False, "A remuneração está em moeda diferente e não será convertida automaticamente.", [f"Alvo: {target_currency}", f"Vaga: {currency}"])
    ratio = salary / target
    score = 100.0 if ratio >= 1 else 80.0 if ratio >= .9 else 60.0 if ratio >= .8 else 40.0 if ratio >= .7 else 20.0
    return StrategicDimension("Compensation Alignment", weight, score, True, "A remuneração atende ou supera a meta." if score == 100 else "A remuneração fica abaixo da meta.", [f"Meta: {target_currency} {target:,.0f}", f"Vaga: {target_currency} {salary:,.0f}"])


def _priorities(direction: dict, op: dict, comp: StrategicDimension) -> StrategicDimension:
    weight = WEIGHTS["strategic_priorities"]
    p = _dict(direction.get("priorities"))
    imp = {k: float(p.get(k, 0) or 0) for k in ("growth","leadership","learning","compensation")}
    if sum(v for v in imp.values() if v > 0) <= 0:
        return StrategicDimension("Strategic Priorities", weight, None, False, "Nenhuma prioridade estratégica foi configurada.")
    text = _text(op)
    leadership_text = " ".join(_list(op.get("leadership_signals")) + _list(op.get("responsibilities")) + [str(op.get("job_title") or "")])
    subs = {
        "growth": 100.0 if _hits(text, GROWTH_TERMS) else 45.0,
        "leadership": 100.0 if _hits(leadership_text, LEADERSHIP_TERMS) else 35.0,
        "learning": 100.0 if _hits(text, LEARNING_TERMS) else 50.0,
        "compensation": comp.score if comp.evaluated else None,
    }
    total = weighted = 0.0
    signals = []
    labels = {"growth":"Crescimento","leadership":"Liderança","learning":"Aprendizado","compensation":"Remuneração"}
    for k, importance in imp.items():
        if importance <= 0 or subs[k] is None:
            continue
        total += importance
        weighted += float(subs[k]) * importance
        signals.append(f"{labels[k]}: {float(subs[k]):.0f}/100")
    if total <= 0:
        return StrategicDimension("Strategic Priorities", weight, None, False, "As prioridades existem, mas não há sinais suficientes.")
    score = round(weighted / total, 2)
    return StrategicDimension("Strategic Priorities", weight, score, True, "A oportunidade atende bem às prioridades." if score >= 70 else "A oportunidade atende apenas parcialmente às prioridades.", signals)


def _classify(score: float) -> tuple[str, str]:
    if score >= 85: return "Strategic Priority", "Priorizar"
    if score >= 70: return "Strong Direction", "Considerar fortemente"
    if score >= 55: return "Conditional Fit", "Considerar com critérios"
    if score >= 40: return "Weak Direction", "Baixa prioridade"
    return "Strategic Detour", "Evitar ou justificar estrategicamente"


def analyze_strategic_fit(career_direction: dict[str, Any] | None, opportunity: Any) -> StrategicFitResult:
    direction, op = dict(career_direction or {}), _obj(opportunity)
    if not direction or not direction.get("is_active", True):
        return StrategicFitResult(False, None, "Direction Required", "Definir Career Direction", 0.0, 0.0, {}, unknowns=["Nenhuma Career Direction ativa disponível."], summary="Defina uma Career Direction antes de avaliar oportunidades.")

    role = _role(direction, op)
    seniority, below = _seniority(direction, op)
    area = _area(direction, op)
    work = _work(direction, op)
    comp = _comp(direction, op)
    priorities = _priorities(direction, op, comp)
    dimensions = {
        "role_alignment": role,
        "seniority_alignment": seniority,
        "area_industry_alignment": area,
        "work_location_alignment": work,
        "compensation_alignment": comp,
        "strategic_priorities": priorities,
    }
    evaluated = [d for d in dimensions.values() if d.evaluated and d.score is not None]
    evaluated_weight = sum(d.weight for d in evaluated)
    if evaluated_weight <= 0:
        return StrategicFitResult(False, None, "Insufficient Evidence", "Revisar dados da oportunidade", 0.0, 0.0, dimensions, unknowns=[f"{d.name}: {d.explanation}" for d in dimensions.values() if not d.evaluated], summary="Não há evidência suficiente para calcular Strategic Fit.")

    raw = sum(float(d.score) * d.weight for d in evaluated) / evaluated_weight
    warnings = []
    if below and bool(_dict(direction.get("constraints")).get("avoid_roles_below_seniority")):
        warnings.append("A oportunidade está abaixo da senioridade-alvo e viola uma restrição estratégica explícita.")
        raw = max(0.0, raw - 15.0)

    score = round(max(0.0, min(100.0, raw)), 2)
    classification, recommendation = _classify(score)
    if warnings and recommendation in {"Priorizar","Considerar fortemente"}:
        recommendation = "Revisar antes de priorizar"

    drivers, tradeoffs, unknowns = [], [], []
    for d in dimensions.values():
        if not d.evaluated:
            unknowns.append(f"{d.name}: {d.explanation}")
        elif d.score is not None and d.score >= 70:
            drivers.append(d.explanation)
        elif d.score is not None and d.score < 55:
            tradeoffs.append(d.explanation)

    confidence = round(evaluated_weight / sum(WEIGHTS.values()) * 100.0, 2)
    summary = (
        "A oportunidade está fortemente alinhada à direção profissional definida." if score >= 85
        else "A oportunidade contribui de forma consistente para a direção profissional." if score >= 70
        else "A oportunidade pode contribuir para a trajetória, mas exige análise de trade-offs." if score >= 55
        else "A oportunidade apresenta alinhamento estratégico limitado." if score >= 40
        else "A oportunidade tende a desviar da direção profissional definida."
    )

    return StrategicFitResult(
        True, score, classification, recommendation, confidence, round(evaluated_weight, 2),
        dimensions, drivers, tradeoffs, warnings, unknowns, summary
    )
