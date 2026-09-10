"""
CareerCompass AI
Decision Engine — Strategic Decision Intelligence
Sprint 5.4B
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

class DecisionType(str, Enum):
    APPLY_NOW = "APPLY NOW"
    APPLY_AFTER_TAILORING = "APPLY AFTER TAILORING"
    STRETCH_OPPORTUNITY = "STRETCH OPPORTUNITY"
    LOW_PRIORITY = "LOW PRIORITY"
    DO_NOT_PRIORITIZE = "DO NOT PRIORITIZE"

@dataclass
class CareerDecision:
    decision: str
    decision_score: float
    confidence_score: float
    career_fit_score: float
    ats_score: float
    tailoring_score: float
    mandatory_coverage: float
    seniority_score: float | None
    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    mandatory_gaps: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    next_best_action: str = ""
    opportunity_quality: float = 0.0
    strategic_fit_score: float | None = None
    strategic_fit_available: bool = False
    strategic_fit_classification: str | None = None
    strategic_fit_confidence: float | None = None
    strategic_warnings: list[str] = field(default_factory=list)
    decision_mode: str = "career_only"
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

STRATEGIC_WEIGHTS = {
    "career_fit": 0.30,
    "strategic_fit": 0.35,
    "ats": 0.15,
    "tailoring": 0.10,
    "opportunity_quality": 0.10,
}
FALLBACK_WEIGHTS = {
    "career_fit": 0.40,
    "ats": 0.25,
    "tailoring": 0.15,
    "opportunity_quality": 0.20,
}
DECISION_THRESHOLDS = {
    DecisionType.APPLY_NOW: 80,
    DecisionType.APPLY_AFTER_TAILORING: 68,
    DecisionType.STRETCH_OPPORTUNITY: 55,
    DecisionType.LOW_PRIORITY: 40,
}

def get_value(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)

def normalize_score(value: Any, default: float = 0.0) -> float:
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        score = float(value)
    elif isinstance(value, str):
        try:
            score = float(value.replace("%", "").replace(",", ".").strip())
        except ValueError:
            return default
    else:
        return default
    if 0 <= score <= 1:
        score *= 100
    return round(max(0.0, min(score, 100.0)), 2)

def normalize_string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values.strip()] if values.strip() else []
    try:
        iterable = list(values)
    except TypeError:
        return []
    out=[]
    for item in iterable:
        text=str(item).strip()
        if text and text not in out:
            out.append(text)
    return out

def _unique(values:list[str])->list[str]:
    out=[]
    for value in values:
        if value and value not in out:
            out.append(value)
    return out

def extract_career_fit_score(report:Any)->float:
    for key in ("score","career_fit_score","fit_score","overall_score"):
        value=get_value(report,key)
        if value is not None: return normalize_score(value)
    return 0.0

def extract_ats_score(report:Any)->float:
    for key in ("score","ats_score","overall_score"):
        value=get_value(report,key)
        if value is not None: return normalize_score(value)
    return 0.0

def extract_tailoring_score(report:Any)->float:
    for key in ("tailoring_score","score","readiness_score"):
        value=get_value(report,key)
        if value is not None: return normalize_score(value)
    return 0.0

def extract_mandatory_coverage(report:Any)->float:
    return normalize_score(get_value(report,"mandatory_coverage"))

def extract_seniority_score(report:Any)->float|None:
    value=get_value(report,"seniority_score")
    return None if value is None else normalize_score(value)

def extract_mandatory_gaps(report:Any)->list[str]:
    return normalize_string_list(get_value(report,"mandatory_gaps",[]))

def extract_strengths(career_fit_report:Any, ats_report:Any)->list[str]:
    return _unique(normalize_string_list(get_value(career_fit_report,"strengths",[]))+normalize_string_list(get_value(ats_report,"strengths",[])))

def extract_strategic_fit(result:Any)->dict[str,Any]:
    if result is None:
        return {"available":False,"score":None,"classification":None,"confidence":None,"warnings":[],"drivers":[],"tradeoffs":[]}
    available=bool(get_value(result,"available",False))
    raw=get_value(result,"score")
    score=normalize_score(raw) if available and raw is not None else None
    conf=get_value(result,"confidence_score")
    return {
        "available": available and score is not None,
        "score": score,
        "classification": get_value(result,"classification"),
        "confidence": normalize_score(conf) if conf is not None else None,
        "warnings": normalize_string_list(get_value(result,"warnings",[])),
        "drivers": normalize_string_list(get_value(result,"drivers",[])),
        "tradeoffs": normalize_string_list(get_value(result,"tradeoffs",[])),
    }

def calculate_opportunity_quality(opportunity_profile:Any)->float:
    if opportunity_profile is None: return 50.0
    confidence=normalize_score(get_value(opportunity_profile,"confidence_score",0))
    mandatory=normalize_string_list(get_value(opportunity_profile,"mandatory_requirements",[]))
    responsibilities=normalize_string_list(get_value(opportunity_profile,"responsibilities",[]))
    skills=normalize_string_list(get_value(opportunity_profile,"skills",[]))
    score=confidence*0.60 + (15 if mandatory else 0) + (15 if responsibilities else 0) + (10 if skills else 0)
    return round(min(score,100.0),2)

def calculate_decision_score(career_fit_score:float, ats_score:float, tailoring_score:float, mandatory_coverage:float, seniority_score:float|None, mandatory_gaps:list[str], opportunity_quality:float=50.0, strategic_fit_score:float|None=None, strategic_fit_available:bool=False)->float:
    if strategic_fit_available and strategic_fit_score is not None:
        score=(career_fit_score*STRATEGIC_WEIGHTS["career_fit"] + strategic_fit_score*STRATEGIC_WEIGHTS["strategic_fit"] + ats_score*STRATEGIC_WEIGHTS["ats"] + tailoring_score*STRATEGIC_WEIGHTS["tailoring"] + opportunity_quality*STRATEGIC_WEIGHTS["opportunity_quality"])
    else:
        score=(career_fit_score*FALLBACK_WEIGHTS["career_fit"] + ats_score*FALLBACK_WEIGHTS["ats"] + tailoring_score*FALLBACK_WEIGHTS["tailoring"] + opportunity_quality*FALLBACK_WEIGHTS["opportunity_quality"])
    score -= min(len(mandatory_gaps)*5.0,20.0)
    if mandatory_coverage < 30: score -= 12
    elif mandatory_coverage < 50: score -= 6
    if seniority_score is not None:
        if seniority_score < 35: score -= 10
        elif seniority_score < 55: score -= 5
    return round(max(0.0,min(score,100.0)),2)

def classify_decision(decision_score:float, mandatory_coverage:float, mandatory_gaps:list[str], career_fit_score:float, ats_score:float, strategic_fit_score:float|None=None, strategic_fit_available:bool=False, strategic_warnings:list[str]|None=None)->DecisionType:
    gaps=len(mandatory_gaps); warnings=strategic_warnings or []
    if mandatory_coverage < 30 and gaps >= 3: return DecisionType.DO_NOT_PRIORITIZE
    if career_fit_score < 35 and ats_score < 35: return DecisionType.DO_NOT_PRIORITIZE
    if strategic_fit_available and strategic_fit_score is not None and strategic_fit_score < 35:
        return DecisionType.LOW_PRIORITY if decision_score >= 40 else DecisionType.DO_NOT_PRIORITIZE
    if decision_score >= 80 and mandatory_coverage >= 80 and gaps <= 1 and not warnings and (not strategic_fit_available or strategic_fit_score is None or strategic_fit_score >= 70):
        return DecisionType.APPLY_NOW
    if decision_score >= 68 and mandatory_coverage >= 60 and gaps <= 3 and not warnings and (not strategic_fit_available or strategic_fit_score is None or strategic_fit_score >= 55):
        return DecisionType.APPLY_AFTER_TAILORING
    if strategic_fit_available and strategic_fit_score is not None and strategic_fit_score >= 70 and decision_score >= 50:
        return DecisionType.STRETCH_OPPORTUNITY
    if decision_score >= 55: return DecisionType.STRETCH_OPPORTUNITY
    if decision_score >= 40: return DecisionType.LOW_PRIORITY
    return DecisionType.DO_NOT_PRIORITIZE

def build_rationale(decision:DecisionType, career_fit_score:float, ats_score:float, tailoring_score:float, mandatory_coverage:float, seniority_score:float|None, mandatory_gaps:list[str], opportunity_quality:float, strategic_fit_score:float|None=None, strategic_fit_available:bool=False, strategic_fit_classification:str|None=None, strategic_warnings:list[str]|None=None, strategic_drivers:list[str]|None=None, strategic_tradeoffs:list[str]|None=None)->tuple[list[str],list[str],list[str]]:
    rationale=[]; strengths=[]; risks=[]
    if strategic_fit_available and strategic_fit_score is not None:
        if strategic_fit_score >= 85: strengths.append("A oportunidade possui alinhamento estratégico muito forte com a Career Direction definida.")
        elif strategic_fit_score >= 70: strengths.append("A oportunidade contribui de forma consistente para a trajetória profissional definida.")
        elif strategic_fit_score < 40: risks.append("A oportunidade apresenta baixo alinhamento com a trajetória profissional definida.")
        if strategic_fit_classification: rationale.append(f"Strategic Fit classificado como {strategic_fit_classification}.")
    strengths += strategic_drivers or []
    risks += strategic_tradeoffs or []
    risks += strategic_warnings or []
    if career_fit_score >= 80: strengths.append("O perfil apresenta forte aderência global à oportunidade.")
    elif career_fit_score < 45: risks.append("A aderência global do perfil à oportunidade é baixa.")
    if ats_score >= 75: strengths.append("O currículo possui boa cobertura para triagem ATS.")
    elif ats_score < 55: risks.append("A cobertura ATS ainda exige otimização antes da candidatura.")
    if mandatory_coverage >= 85: strengths.append("A maior parte dos requisitos obrigatórios possui evidência.")
    elif mandatory_coverage < 60: risks.append("A cobertura de requisitos obrigatórios é insuficiente.")
    if mandatory_gaps: risks.append(f"{len(mandatory_gaps)} requisito(s) obrigatório(s) não possui(em) evidência suficiente.")
    if seniority_score is not None:
        if seniority_score >= 85: strengths.append("A senioridade do perfil é compatível com a posição.")
        elif seniority_score < 55: risks.append("Existe risco de desalinhamento de senioridade.")
    if tailoring_score >= 80: strengths.append("O currículo pode ser customizado com boa base de evidências existentes.")
    elif tailoring_score < 50: risks.append("A customização do currículo possui limitações por falta de evidências.")
    if opportunity_quality < 50: risks.append("A descrição da vaga possui pouca informação estruturada, reduzindo a confiança da recomendação.")
    opening={
        DecisionType.APPLY_NOW:"A oportunidade combina aderência atual, viabilidade de candidatura e valor estratégico suficientes para priorização imediata.",
        DecisionType.APPLY_AFTER_TAILORING:"A oportunidade é relevante, mas o posicionamento da candidatura deve ser fortalecido antes de aplicar.",
        DecisionType.STRETCH_OPPORTUNITY:"A oportunidade representa um movimento de expansão: há gaps no fit atual, mas existe valor potencial para a trajetória.",
        DecisionType.LOW_PRIORITY:"O retorno esperado da candidatura é limitado frente aos gaps e/ou ao alinhamento estratégico.",
        DecisionType.DO_NOT_PRIORITIZE:"Os gaps e o baixo retorno estratégico tornam esta candidatura pouco eficiente neste momento.",
    }[decision]
    rationale=[opening]+rationale+strengths+risks
    return _unique(rationale),_unique(strengths),_unique(risks)

def build_next_best_action(decision:DecisionType, mandatory_gaps:list[str], strategic_fit_score:float|None=None, strategic_fit_available:bool=False)->str:
    if decision==DecisionType.APPLY_NOW: return "Finalizar a versão customizada do currículo e priorizar a candidatura."
    if decision==DecisionType.APPLY_AFTER_TAILORING: return "Customizar headline, resumo, competências e evidências do currículo antes de aplicar."
    if decision==DecisionType.STRETCH_OPPORTUNITY:
        if strategic_fit_available and strategic_fit_score is not None and strategic_fit_score >= 70:
            return "Tratar a vaga como movimento estratégico: fechar os principais gaps e preparar uma narrativa de transição antes de aplicar."
        if mandatory_gaps: return "Avaliar se os gaps obrigatórios podem ser sustentados por experiências ainda não evidenciadas no currículo antes de aplicar."
        return "Considerar a candidatura como movimento de expansão profissional e preparar uma narrativa forte para os gaps."
    if decision==DecisionType.LOW_PRIORITY: return "Priorizar oportunidades com melhor combinação entre Career Fit e Strategic Fit antes de investir tempo nesta candidatura."
    return "Não priorizar esta oportunidade neste momento. Direcionar esforço para vagas com maior aderência atual e estratégica."

def calculate_decision_confidence(opportunity_quality:float, career_fit_score:float, ats_score:float, mandatory_coverage:float, strategic_fit_confidence:float|None=None, strategic_fit_available:bool=False)->float:
    if strategic_fit_available and strategic_fit_confidence is not None:
        score=opportunity_quality*0.25+career_fit_score*0.15+ats_score*0.15+mandatory_coverage*0.20+strategic_fit_confidence*0.25
    else:
        score=opportunity_quality*0.35+career_fit_score*0.20+ats_score*0.20+mandatory_coverage*0.25
    return round(max(0.0,min(score,100.0)),2)

def build_career_decision(career_fit_report:Any, ats_report:Any, tailoring_report:Any, opportunity_profile:Any=None, strategic_fit_result:Any=None)->CareerDecision:
    career_fit_score=extract_career_fit_score(career_fit_report)
    ats_score=extract_ats_score(ats_report)
    tailoring_score=extract_tailoring_score(tailoring_report)
    mandatory_coverage=extract_mandatory_coverage(ats_report)
    seniority_score=extract_seniority_score(ats_report)
    mandatory_gaps=extract_mandatory_gaps(ats_report)
    opportunity_quality=calculate_opportunity_quality(opportunity_profile)
    strategic=extract_strategic_fit(strategic_fit_result)
    decision_score=calculate_decision_score(career_fit_score,ats_score,tailoring_score,mandatory_coverage,seniority_score,mandatory_gaps,opportunity_quality,strategic["score"],strategic["available"])
    decision=classify_decision(decision_score,mandatory_coverage,mandatory_gaps,career_fit_score,ats_score,strategic["score"],strategic["available"],strategic["warnings"])
    rationale, explanation_strengths, risks=build_rationale(decision,career_fit_score,ats_score,tailoring_score,mandatory_coverage,seniority_score,mandatory_gaps,opportunity_quality,strategic["score"],strategic["available"],strategic["classification"],strategic["warnings"],strategic["drivers"],strategic["tradeoffs"])
    strengths=_unique(extract_strengths(career_fit_report,ats_report)+explanation_strengths)
    next_best_action=build_next_best_action(decision,mandatory_gaps,strategic["score"],strategic["available"])
    confidence_score=calculate_decision_confidence(opportunity_quality,career_fit_score,ats_score,mandatory_coverage,strategic["confidence"],strategic["available"])
    return CareerDecision(decision=decision.value,decision_score=decision_score,confidence_score=confidence_score,career_fit_score=career_fit_score,ats_score=ats_score,tailoring_score=tailoring_score,mandatory_coverage=mandatory_coverage,seniority_score=seniority_score,strengths=strengths,risks=risks,mandatory_gaps=mandatory_gaps,rationale=rationale,next_best_action=next_best_action,opportunity_quality=opportunity_quality,strategic_fit_score=strategic["score"],strategic_fit_available=strategic["available"],strategic_fit_classification=strategic["classification"],strategic_fit_confidence=strategic["confidence"],strategic_warnings=strategic["warnings"],decision_mode="strategic" if strategic["available"] else "career_only")

def build_decision_summary(decision:CareerDecision)->dict[str,Any]:
    return decision.to_dict()

def run_self_test()->dict[str,Any]:
    decision=build_career_decision({"score":76,"strengths":["Liderança"]},{"score":71,"mandatory_coverage":78,"seniority_score":100,"mandatory_gaps":["Gestão de Riscos"]},{"tailoring_score":82},{"confidence_score":87,"mandatory_requirements":["Liderança"],"responsibilities":["Liderar projetos"],"skills":["Gestão"]},{"available":True,"score":74,"classification":"Strong Direction","confidence_score":70,"warnings":[],"drivers":["Valor estratégico"],"tradeoffs":[]})
    return {"status":"ok","decision":build_decision_summary(decision)}

if __name__=="__main__":
    print(run_self_test())
