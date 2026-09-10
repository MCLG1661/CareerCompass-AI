from decision_engine import build_career_decision

def base_inputs():
    return ({"score":82,"strengths":["Liderança","Gestão"]},{"score":80,"mandatory_coverage":90,"seniority_score":100,"mandatory_gaps":[],"strengths":["ATS competitivo"]},{"tailoring_score":85},{"confidence_score":90,"mandatory_requirements":["Liderança"],"responsibilities":["Liderar equipe"],"skills":["Gestão"]})

def strategic(score,warnings=None,confidence=85):
    return {"available":True,"score":score,"classification":"Strategic Priority" if score>=85 else "Strong Direction" if score>=70 else "Conditional Fit" if score>=55 else "Weak Direction" if score>=40 else "Strategic Detour","confidence_score":confidence,"warnings":warnings or [],"drivers":["Alinhamento estratégico detectado"] if score>=70 else [],"tradeoffs":["Baixo alinhamento com a trajetória"] if score<55 else []}

def test_high_fit_high_strategy_apply_now():
    cf,ats,t,o=base_inputs(); r=build_career_decision(cf,ats,t,o,strategic(90)); assert r.decision=="APPLY NOW"; assert r.strategic_fit_score==90; assert r.decision_mode=="strategic"

def test_high_career_fit_low_strategy_is_downgraded():
    cf,ats,t,o=base_inputs(); r=build_career_decision(cf,ats,t,o,strategic(25)); assert r.decision in {"LOW PRIORITY","DO NOT PRIORITIZE"}; assert r.decision!="APPLY NOW"

def test_moderate_career_fit_strong_strategy_can_be_stretch():
    cf,ats,t,o=base_inputs(); cf["score"]=57; ats["score"]=60; ats["mandatory_coverage"]=57; t["tailoring_score"]=63; r=build_career_decision(cf,ats,t,o,strategic(71.15,confidence=65)); assert r.strategic_fit_score==71.15; assert r.decision in {"STRETCH OPPORTUNITY","APPLY AFTER TAILORING"}; assert r.decision!="DO NOT PRIORITIZE"

def test_strategic_warning_blocks_apply_now():
    cf,ats,t,o=base_inputs(); r=build_career_decision(cf,ats,t,o,strategic(88,["A oportunidade viola uma restrição estratégica explícita."])); assert r.decision!="APPLY NOW"; assert r.strategic_warnings

def test_without_strategic_fit_keeps_backward_compatibility():
    cf,ats,t,o=base_inputs(); r=build_career_decision(cf,ats,t,o); assert r.strategic_fit_available is False; assert r.strategic_fit_score is None; assert r.decision_mode=="career_only"

def test_mandatory_hard_stop_still_wins():
    cf,ats,t,o=base_inputs(); ats["mandatory_coverage"]=20; ats["mandatory_gaps"]=["A","B","C","D"]; r=build_career_decision(cf,ats,t,o,strategic(95)); assert r.decision=="DO NOT PRIORITIZE"

def run():
    tests=[test_high_fit_high_strategy_apply_now,test_high_career_fit_low_strategy_is_downgraded,test_moderate_career_fit_strong_strategy_can_be_stretch,test_strategic_warning_blocks_apply_now,test_without_strategic_fit_keeps_backward_compatibility,test_mandatory_hard_stop_still_wins]
    for test in tests:
        test(); print(f"PASS: {test.__name__}")
    print("SPRINT 5.4B VALIDADO: Strategic Fit integrado ao Decision Engine.")

if __name__=="__main__": run()
