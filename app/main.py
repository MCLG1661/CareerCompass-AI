from pathlib import Path
import hashlib

import streamlit as st
from PIL import Image

from ats_engine import analyze_ats
from coach_engine import evaluate_answer, get_step
from curator_engine import analyze_compatibility
from cv_tailoring_engine import tailor_cv
from decision_engine import build_career_decision
from gap_intelligence_engine import analyze_career_gaps
from career_analytics_engine import analyze_career_history
from application_intelligence_engine import analyze_application_history
from executive_intelligence_engine import build_executive_intelligence
from opportunity_engine import analyze_opportunity
from pdf_engine import build_career_report_pdf
from profile_engine import build_professional_profile
from recommendation_engine import build_recommendations
from report_engine import build_career_report, report_to_markdown
from resume_parser import ResumeParserError, extract_resume_text
from scout_engine import discover_roles
from auth_engine import (
    send_password_recovery,
    sign_in_with_password,
    sign_out,
    sign_up,
)
from persistence_service import (
    build_career_snapshot,
    change_application_status,
    activate_profile,
    ensure_user,
    get_analysis_history,
    get_application_pipeline,
    get_career_dashboard_metrics,
    get_opportunity_history,
    get_profile_repository,
    get_user_active_profile,
    initialize_persistence,
    persist_application,
    persist_career_analysis,
    persist_opportunity,
    persist_profile,
)


# =========================================================
# CONFIGURAÇÃO
# =========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT_DIR / "data" / "user-profile.md"
ICON_PATH = ROOT_DIR / "careercompass-icon.png"

PAGE_ICON = (
    Image.open(ICON_PATH)
    if ICON_PATH.exists()
    else "🧭"
)


def load_default_profile() -> str:
    if not PROFILE_PATH.exists():
        return "Perfil profissional não encontrado."

    return PROFILE_PATH.read_text(
        encoding="utf-8"
    )


def reset_coach():
    st.session_state.coach_step = 1
    st.session_state.coach_answers = {}
    st.session_state.coach_feedback = {}

    for i in range(1, 7):
        key = f"coach_answer_{i}"

        if key in st.session_state:
            del st.session_state[key]


def reset_opportunity_analysis():
    st.session_state.curator_result = None
    st.session_state.ats_report = None
    st.session_state.recommendation_report = None
    st.session_state.tailoring_report = None
    st.session_state.opportunity_profile = None
    st.session_state.career_decision = None
    st.session_state.analyzed_job_title = ""
    st.session_state.analyzed_job_description = ""
    st.session_state.career_opportunity_id = None
    st.session_state.career_analysis_id = None
    st.session_state.career_application_id = None


def clear_opportunity_workspace():
    reset_opportunity_analysis()
    st.session_state.job_title_input = ""
    st.session_state.job_description_input = ""
    st.session_state.career_report = None
    st.session_state.career_report_pdf = None
    reset_coach()


def format_items(
    items: list[str],
) -> str:

    if not items:
        return "Não identificado"

    return " • ".join(items)


def safe_filename(
    name: str,
) -> str:

    cleaned = "".join(
        char
        for char in name
        if char.isalnum()
        or char in ("-", "_")
    )

    return cleaned or "candidato"


st.set_page_config(
    page_title="CareerCompass AI",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# SPRINT 4.3 — SUPABASE AUTH
# =========================================================

AUTH_SESSION_KEY = "careercompass_auth_session"


def _auth_user_name(auth_user) -> str:
    metadata = getattr(auth_user, "user_metadata", None) or {}
    return (
        str(metadata.get("full_name") or "").strip()
        or str(metadata.get("name") or "").strip()
        or str(metadata.get("display_name") or "").strip()
        or str(getattr(auth_user, "email", "") or "").split("@")[0]
        or "CareerCompass User"
    )


def _clear_app_session_after_logout() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def render_auth_screen() -> None:
    st.markdown(
        """
        <style>
        .stApp{
            background:
                radial-gradient(circle at 85% 0%,rgba(46,166,255,.13),transparent 28%),
                radial-gradient(circle at 65% 8%,rgba(120,102,255,.10),transparent 22%),
                linear-gradient(180deg,#06101d 0%,#07111f 55%,#081423 100%);
            color:#f4f8ff;
        }
        .block-container{max-width:760px;padding-top:5rem;}
        h1,h2,h3,p,label{color:#f4f8ff!important;}
        [data-testid="stCaptionContainer"] p{color:#91a0b5!important;}
        .stTextInput input{
            background:#0b1829!important;color:#eef5ff!important;
            border:1px solid rgba(255,255,255,.10)!important;
            border-radius:11px!important;
        }
        .stButton button{min-height:44px;border-radius:10px;font-weight:700;}
        div[data-baseweb="tab-list"]{border-bottom:1px solid rgba(255,255,255,.10);}
        button[data-baseweb="tab"]{color:#91a0b5!important;font-weight:750!important;}
        button[data-baseweb="tab"][aria-selected="true"]{color:#5fc3ff!important;}
        #MainMenu,footer{visibility:hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    brand_col, title_col = st.columns([0.14, 0.86], vertical_alignment="center")
    with brand_col:
        if ICON_PATH.exists():
            st.image(str(ICON_PATH), width=54)
        else:
            st.markdown("### C")
    with title_col:
        st.markdown("# CareerCompass AI")
        st.markdown("### Career Intelligence Platform")
    st.caption("Entre para acessar seu perfil, histórico e inteligência de carreira.")

    login_tab, signup_tab, recovery_tab = st.tabs(
        ["Entrar", "Criar conta", "Recuperar senha"]
    )

    with login_tab:
        with st.form("careercompass_login_form"):
            email = st.text_input("E-mail", key="auth_login_email")
            password = st.text_input("Senha", type="password", key="auth_login_password")
            submitted = st.form_submit_button(
                "Entrar no CareerCompass",
                type="primary",
                use_container_width=True,
            )
        if submitted:
            try:
                session = sign_in_with_password(email.strip(), password)
                st.session_state[AUTH_SESSION_KEY] = session
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível entrar: {exc}")

    with signup_tab:
        with st.form("careercompass_signup_form"):
            full_name = st.text_input("Nome", key="auth_signup_name")
            signup_email = st.text_input("E-mail", key="auth_signup_email")
            signup_password = st.text_input(
                "Senha", type="password", key="auth_signup_password"
            )
            signup_submitted = st.form_submit_button(
                "Criar conta",
                type="primary",
                use_container_width=True,
            )
        if signup_submitted:
            try:
                result = sign_up(
                    signup_email.strip(),
                    signup_password,
                    full_name=full_name.strip() or None,
                )
                result_session = getattr(result, "session", None)
                if result_session is not None:
                    st.session_state[AUTH_SESSION_KEY] = result_session
                    st.rerun()
                else:
                    st.success(
                        "Conta criada. Verifique seu e-mail para confirmar o cadastro "
                        "e depois volte para entrar."
                    )
            except Exception as exc:
                st.error(f"Não foi possível criar a conta: {exc}")

    with recovery_tab:
        with st.form("careercompass_recovery_form"):
            recovery_email = st.text_input("E-mail", key="auth_recovery_email")
            recovery_submitted = st.form_submit_button(
                "Enviar recuperação",
                use_container_width=True,
            )
        if recovery_submitted:
            try:
                send_password_recovery(recovery_email.strip())
                st.success(
                    "Se o e-mail estiver cadastrado, você receberá as instruções "
                    "de recuperação."
                )
            except Exception as exc:
                st.error(f"Não foi possível iniciar a recuperação: {exc}")


auth_session = st.session_state.get(AUTH_SESSION_KEY)

if auth_session is None:
    render_auth_screen()
    st.stop()

auth_user = auth_session.user
auth_user_id = str(auth_user.id)
auth_email = str(auth_user.email or "").strip()
auth_name = _auth_user_name(auth_user)


# =========================================================
# ESTADO
# =========================================================

if "selected_flow" not in st.session_state:
    st.session_state.selected_flow = "home"

if "coach_step" not in st.session_state:
    st.session_state.coach_step = 1

if "coach_answers" not in st.session_state:
    st.session_state.coach_answers = {}

if "coach_feedback" not in st.session_state:
    st.session_state.coach_feedback = {}

if "resume_text" not in st.session_state:
    st.session_state.resume_text = None

if "resume_name" not in st.session_state:
    st.session_state.resume_name = None

if "resume_source_name" not in st.session_state:
    st.session_state.resume_source_name = None

if "profile_repository_initialized" not in st.session_state:
    st.session_state.profile_repository_initialized = False

if "scout_results" not in st.session_state:
    st.session_state.scout_results = None

if "career_report" not in st.session_state:
    st.session_state.career_report = None

if "career_report_pdf" not in st.session_state:
    st.session_state.career_report_pdf = None

if "candidate_name_input" not in st.session_state:
    st.session_state.candidate_name_input = ""

if "job_title_input" not in st.session_state:
    st.session_state.job_title_input = ""

if "job_description_input" not in st.session_state:
    st.session_state.job_description_input = ""

if "curator_result" not in st.session_state:
    st.session_state.curator_result = None

if "ats_report" not in st.session_state:
    st.session_state.ats_report = None

if "recommendation_report" not in st.session_state:
    st.session_state.recommendation_report = None

if "tailoring_report" not in st.session_state:
    st.session_state.tailoring_report = None

if "opportunity_profile" not in st.session_state:
    st.session_state.opportunity_profile = None

if "career_decision" not in st.session_state:
    st.session_state.career_decision = None

if "analyzed_job_title" not in st.session_state:
    st.session_state.analyzed_job_title = ""

if "analyzed_job_description" not in st.session_state:
    st.session_state.analyzed_job_description = ""

if "career_user_id" not in st.session_state:
    st.session_state.career_user_id = None

if "career_profile_id" not in st.session_state:
    st.session_state.career_profile_id = None

if "persisted_profile_signature" not in st.session_state:
    st.session_state.persisted_profile_signature = None

if "career_opportunity_id" not in st.session_state:
    st.session_state.career_opportunity_id = None

if "career_analysis_id" not in st.session_state:
    st.session_state.career_analysis_id = None

if "career_application_id" not in st.session_state:
    st.session_state.career_application_id = None

if "persistence_ready" not in st.session_state:
    st.session_state.persistence_ready = False

if "persistence_error" not in st.session_state:
    st.session_state.persistence_error = None

try:
    initialize_persistence()
    st.session_state.persistence_ready = True
    st.session_state.persistence_error = None
except Exception as exc:
    st.session_state.persistence_ready = False
    st.session_state.persistence_error = str(exc)


default_profile = load_default_profile()

# Resolve a identidade autenticada para o usuário persistente do CareerCompass.
if st.session_state.persistence_ready and st.session_state.career_user_id is None:
    try:
        st.session_state.career_user_id = ensure_user(
            name=auth_name,
            email=auth_email,
            auth_user_id=auth_user_id,
        )
    except Exception as exc:
        st.session_state.persistence_error = str(exc)

if (
    st.session_state.persistence_ready
    and st.session_state.career_user_id
    and not st.session_state.profile_repository_initialized
):
    try:
        stored_profile = get_user_active_profile(st.session_state.career_user_id)
        if stored_profile and stored_profile.get("raw_profile_text"):
            stored_type = stored_profile.get("profile_type") or "resume"
            stored_text = stored_profile["raw_profile_text"]
            st.session_state.career_profile_id = stored_profile["id"]
            st.session_state.persisted_profile_signature = (
                stored_profile.get("content_hash")
                or hashlib.sha256(
                    stored_text.encode("utf-8", errors="ignore")
                ).hexdigest()
            )

            if stored_type == "default":
                st.session_state.resume_text = None
                st.session_state.resume_name = None
                st.session_state.resume_source_name = None
            else:
                st.session_state.resume_text = stored_text
                st.session_state.resume_name = (
                    stored_profile.get("profile_name") or "Currículo"
                )
                st.session_state.resume_source_name = stored_profile.get("source_name")

        st.session_state.profile_repository_initialized = True
    except Exception as exc:
        st.session_state.persistence_error = str(exc)
        st.session_state.profile_repository_initialized = True

profile = (
    st.session_state.resume_text
    if st.session_state.resume_text
    else default_profile
)


# =========================================================
# IDENTIDADE VISUAL — CAREERCOMPASS AI 5.0
# =========================================================

st.markdown(
    """
<style>
:root{
    --bg:#07111f;
    --bg2:#0a1628;
    --panel:#0d1b2e;
    --panel2:#10223a;
    --border:rgba(255,255,255,.10);
    --text:#f4f8ff;
    --muted:#91a0b5;
    --blue:#2ea6ff;
    --violet:#7866ff;
    --green:#19c37d;
    --amber:#f0a63a;
}
html,body,[class*="css"]{
    font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}
.stApp{
    background:
        radial-gradient(circle at 90% 0%,rgba(46,166,255,.12),transparent 25%),
        radial-gradient(circle at 70% 5%,rgba(120,102,255,.09),transparent 19%),
        linear-gradient(180deg,#06101d 0%,#07111f 50%,#081423 100%);
    color:var(--text);
}
.block-container{
    max-width:1580px;
    padding-top:.55rem;
    padding-left:1.7rem;
    padding-right:1.7rem;
    padding-bottom:4rem;
}
section[data-testid="stSidebar"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}

h1,h2,h3,h4{color:var(--text)!important;letter-spacing:-.035em;}
p,li,label{color:#b2bfd0!important;}
small{color:#7f90a7!important;}

.stButton button{
    min-height:42px;
    border-radius:10px;
    border:1px solid var(--border);
    background:#0e1d31;
    color:#e7effa;
    font-weight:650;
    transition:.18s ease;
}
.stButton button:hover{
    transform:translateY(-1px);
    border-color:rgba(84,185,255,.45);
    background:#112541;
    box-shadow:0 10px 24px rgba(0,0,0,.18);
}
.stButton button[kind="primary"]{
    background:linear-gradient(135deg,#2f6dff 0%,#1db8ff 100%);
    border:none;
    box-shadow:0 12px 26px rgba(35,117,255,.28);
}
.stTextArea textarea,.stTextInput input{
    background:#0b1829!important;
    color:#eef5ff!important;
    border:1px solid var(--border)!important;
    border-radius:11px!important;
}
[data-testid="stFileUploaderDropzone"]{
    background:#0b1829!important;
    border:1px dashed rgba(255,255,255,.18)!important;
    border-radius:12px!important;
}
[data-testid="stFileUploaderDropzone"] *{color:#c8d3e3!important;}
[data-testid="stFileUploaderDropzone"] button{
    background:#10223a!important;
    color:#eef5ff!important;
    border:1px solid var(--border)!important;
}
[data-testid="stAlert"]{border-radius:11px!important;}
div[data-testid="stVerticalBlockBorderWrapper"]{
    background:linear-gradient(180deg,#0d1b2e 0%,#0b1829 100%);
    border:1px solid var(--border)!important;
    border-radius:15px!important;
    box-shadow:0 14px 34px rgba(0,0,0,.16);
}
div[data-testid="stMetric"]{
    background:#0d1b2e;
    border:1px solid var(--border);
    border-radius:14px;
    padding:17px 18px;
}
div[data-testid="stMetric"] label{
    color:#8190a4!important;
    font-size:.70rem!important;
    font-weight:800!important;
    text-transform:uppercase;
    letter-spacing:.08em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{
    color:#f4f8ff!important;
    letter-spacing:-.04em;
}

/* native tabs */
div[data-baseweb="tab-list"]{
    border-bottom:1px solid rgba(255,255,255,.10);
}
button[data-baseweb="tab"]{
    color:#8fa0b7!important;
    font-weight:700!important;
}
button[data-baseweb="tab"][aria-selected="true"]{
    color:#5fc3ff!important;
}

/* product blocks rendered via st.html */
.cc-top{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:20px;
    padding:8px 2px 14px;
    border-bottom:1px solid rgba(255,255,255,.08);
    margin-bottom:12px;
}
.cc-brand{display:flex;align-items:center;gap:11px;}
.cc-logo{
    width:40px;height:40px;border-radius:11px;
    display:flex;align-items:center;justify-content:center;
    background:radial-gradient(circle at 30% 30%,#38d8ff 0%,#2f74ff 45%,#6e5cff 100%);
    color:white;font-weight:900;
    box-shadow:0 8px 22px rgba(46,166,255,.24);
}
.cc-brand-title{font-weight:850;color:#fff;font-size:1.02rem;}
.cc-brand-sub{font-size:.68rem;color:#75869f;margin-top:1px;}
.cc-user{display:flex;align-items:center;gap:10px;}
.cc-user-copy{text-align:right;}
.cc-user-name{color:#fff;font-size:.78rem;font-weight:750;}
.cc-user-status{color:#26d28d;font-size:.67rem;margin-top:2px;}
.cc-avatar{
    width:34px;height:34px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    background:#1a2a41;border:1px solid var(--border);
    color:#fff;font-weight:800;font-size:.72rem;
}

.cc-strip{
    display:grid;grid-template-columns:1.45fr 1fr 1fr;
    background:rgba(10,22,40,.78);
    border:1px solid rgba(255,255,255,.07);
    border-radius:14px;
    overflow:hidden;
    margin:10px 0 16px;
}
.cc-strip-cell{padding:14px 18px;border-right:1px solid rgba(255,255,255,.07);}
.cc-strip-cell:last-child{border-right:none;}
.cc-label{
    color:#708198;font-size:.64rem;font-weight:850;
    letter-spacing:.13em;text-transform:uppercase;
}
.cc-value{color:#f5f8fd;font-size:.87rem;font-weight:750;margin-top:5px;}
.cc-sub{color:#4bb8ff;font-size:.68rem;margin-top:3px;}

.cc-card-html{
    background:linear-gradient(180deg,#0d1b2e 0%,#0b1829 100%);
    border:1px solid var(--border);
    border-radius:15px;
    padding:20px;
    box-shadow:0 18px 36px rgba(0,0,0,.14);
    height:100%;
    box-sizing:border-box;
}
.cc-card-kicker{
    color:#cbd6e5;font-size:.67rem;font-weight:850;
    letter-spacing:.13em;text-transform:uppercase;margin-bottom:12px;
}
.cc-score-layout{
    display:grid;grid-template-columns:180px 1fr;gap:18px;align-items:center;
}
.cc-ring{
    width:150px;height:150px;border-radius:50%;
    padding:13px;margin:auto;
    background:conic-gradient(#32b7ff 0 40%,#6d5cff 40% 78%,#1b2b43 78% 100%);
}
.cc-ring-inner{
    width:100%;height:100%;border-radius:50%;
    background:#0c192b;display:flex;flex-direction:column;
    align-items:center;justify-content:center;
}
.cc-ring-score{color:#fff;font-size:2.2rem;font-weight:850;letter-spacing:-.06em;}
.cc-ring-caption{color:#9aa9bb;font-size:.72rem;}
.cc-score-label{text-align:center;color:#40aaff;font-weight:800;margin-top:8px;}
.cc-note{color:#d3dce7;font-size:.80rem;line-height:1.5;margin-bottom:12px;}
.cc-bar-row{
    display:grid;grid-template-columns:100px 1fr 36px;
    gap:9px;align-items:center;margin:8px 0;
    color:#a8b5c5;font-size:.70rem;
}
.cc-bar{height:6px;background:#1d2b3f;border-radius:999px;overflow:hidden;}
.cc-bar-fill{height:100%;background:linear-gradient(90deg,#4b66ff,#2db8ff);border-radius:999px;}

.cc-next-box{
    border:1px solid rgba(255,255,255,.08);
    background:rgba(255,255,255,.02);
    border-radius:12px;padding:17px;
}
.cc-next-title{color:#fff;font-size:1.3rem;font-weight:850;letter-spacing:-.035em;margin-top:7px;}
.cc-next-copy{color:#b4bfce;font-size:.78rem;line-height:1.5;margin-top:10px;}
.cc-match{float:right;color:#69dfa9;font-size:1.45rem;font-weight:850;}
.cc-badges{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;}
.cc-badge{
    padding:6px 8px;border-radius:8px;background:#11233a;
    border:1px solid rgba(255,255,255,.07);color:#9fd6ff;font-size:.66rem;
}

.cc-activity{display:flex;flex-direction:column;gap:11px;}
.cc-act{display:grid;grid-template-columns:26px 1fr;gap:9px;align-items:center;}
.cc-act-icon{
    width:26px;height:26px;border-radius:50%;background:#153860;
    display:flex;align-items:center;justify-content:center;color:#62c7ff;font-size:.68rem;
}
.cc-act-title{color:#e8eef7;font-size:.71rem;font-weight:750;}
.cc-act-sub{color:#75869b;font-size:.62rem;margin-top:2px;}

.cc-journey{
    display:grid;grid-template-columns:repeat(5,1fr);gap:0;
    margin-top:12px;
}
.cc-step{position:relative;padding-right:18px;}
.cc-step:before{
    content:"";position:absolute;top:9px;left:14px;right:-4px;height:2px;background:#2a3b53;
}
.cc-step:last-child:before{right:50%;}
.cc-dot{
    width:18px;height:18px;border-radius:50%;
    background:#2f6cff;border:3px solid #143052;
    position:relative;z-index:2;margin-bottom:8px;
}
.cc-step.pending .cc-dot{background:#536277;}
.cc-step-no{color:#4caeff;font-size:.62rem;font-weight:800;}
.cc-step-name{color:#f0f4fa;font-size:.83rem;font-weight:750;margin-top:3px;}
.cc-step-copy{color:#78899e;font-size:.64rem;line-height:1.35;margin-top:3px;}

.cc-table{width:100%;border-collapse:collapse;font-size:.70rem;}
.cc-table th{
    color:#708198;text-transform:uppercase;letter-spacing:.08em;
    font-size:.58rem;text-align:left;padding:7px 7px;
    border-bottom:1px solid rgba(255,255,255,.07);
}
.cc-table td{color:#d7e0eb;padding:9px 7px;border-bottom:1px solid rgba(255,255,255,.05);}
.cc-good{color:#51dc9d!important;font-weight:800;}
.cc-mid{color:#f1ad47!important;font-weight:800;}

.cc-insight{display:grid;grid-template-columns:30px 1fr;gap:9px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.05);}
.cc-insight:last-child{border-bottom:none;}
.cc-insight-icon{
    width:28px;height:28px;border-radius:50%;background:#123a2e;
    display:flex;align-items:center;justify-content:center;color:#49db9e;font-size:.68rem;
}
.cc-insight-title{color:#edf3fa;font-size:.71rem;font-weight:750;}
.cc-insight-copy{color:#7f8ea2;font-size:.63rem;line-height:1.35;margin-top:2px;}

.cc-quick{
    border:1px solid rgba(255,255,255,.07);border-radius:10px;background:#0e1d31;
    min-height:64px;display:flex;align-items:center;justify-content:center;
    text-align:center;color:#dce5ef;font-size:.66rem;font-weight:700;padding:8px;
}

.cc-module-header{
    padding:20px 22px;border:1px solid var(--border);
    background:linear-gradient(180deg,#0d1b2e,#0b1829);
    border-radius:14px;margin:14px 0 18px;
}
.cc-module-header h2{margin:0!important;color:#fff!important;}
.cc-module-header p{margin:7px 0 0!important;color:#8fa0b7!important;}
.cc-agent-label{
    color:#3aaeff;font-size:.64rem;font-weight:850;
    letter-spacing:.13em;text-transform:uppercase;margin-bottom:7px;
}
.cc-summary{
    padding:18px 20px;background:#0d1b2e;border:1px solid var(--border);
    border-radius:13px;color:#aebacc;line-height:1.6;
}
.cc-footer{
    text-align:center;color:#53657d;font-size:.70rem;margin-top:36px;
    padding-top:15px;border-top:1px solid rgba(255,255,255,.06);
}
@media(max-width:1100px){
    .cc-strip{grid-template-columns:1fr;}
    .cc-strip-cell{border-right:none;border-bottom:1px solid rgba(255,255,255,.07);}
    .cc-score-layout{grid-template-columns:1fr;}
    .cc-journey{grid-template-columns:1fr 1fr;}
}
</style>
    """,
    unsafe_allow_html=True,
)

def render_html(content: str) -> None:
    """
    Renderiza HTML real.
    Usa st.html quando disponível para evitar que o Markdown
    transforme blocos HTML em código literal.
    """
    if hasattr(st, "html"):
        st.html(content)
    else:
        st.markdown(content, unsafe_allow_html=True)

# =========================================================
# SIDEBAR — DESATIVADA
# =========================================================

# =========================================================
# PROFILE ENGINE
# =========================================================

structured_profile = build_professional_profile(
    profile
)

if not st.session_state.candidate_name_input:
    st.session_state.candidate_name_input = (
        structured_profile.candidate_name
        if structured_profile.candidate_name
        else "Candidato"
    )

profile_signature = hashlib.sha256(
    profile.encode("utf-8", errors="ignore")
).hexdigest()

if st.session_state.persistence_ready:
    try:
        if st.session_state.career_user_id is None:
            st.session_state.career_user_id = ensure_user(
                name=auth_name,
                email=auth_email,
                auth_user_id=auth_user_id,
            )

        if (
            st.session_state.career_profile_id is None
            or st.session_state.persisted_profile_signature != profile_signature
        ):
            st.session_state.career_profile_id = persist_profile(
                user_id=st.session_state.career_user_id,
                raw_profile_text=profile,
                structured_profile=structured_profile,
                profile_name=(
                    st.session_state.resume_name
                    if st.session_state.resume_text
                    else "Perfil padrão"
                ),
                source_name=(
                    st.session_state.resume_source_name
                    if st.session_state.resume_text
                    else "user-profile.md"
                ),
                content_hash=profile_signature,
                profile_type=(
                    "resume" if st.session_state.resume_text else "default"
                ),
            )
            st.session_state.persisted_profile_signature = profile_signature

    except Exception as exc:
        st.session_state.persistence_error = str(exc)


# =========================================================
# TOP NAVIGATION + HOME
# =========================================================

active_flow = st.session_state.selected_flow

candidate_display = (
    structured_profile.candidate_name
    if structured_profile.candidate_name
    else "Candidato"
)

candidate_initials = "".join(
    part[0].upper()
    for part in candidate_display.split()
    if part
)[:2] or "CC"

render_html(
    f"""
<div class="cc-top">
    <div class="cc-brand">
        <div class="cc-logo">C</div>
        <div>
            <div class="cc-brand-title">CareerCompass AI</div>
            <div class="cc-brand-sub">Career Intelligence Platform</div>
        </div>
    </div>
    <div class="cc-user">
        <div class="cc-user-copy">
            <div class="cc-user-name">{candidate_display}</div>
            <div class="cc-user-status">● Perfil ativo</div>
        </div>
        <div class="cc-avatar">{candidate_initials}</div>
    </div>
</div>
"""
)

account_col, logout_col = st.columns([8.6, 1.4])
with account_col:
    st.caption(f"Sessão autenticada · {auth_email}")
with logout_col:
    if st.button(
        "Sair",
        key="careercompass_logout",
        use_container_width=True,
    ):
        try:
            sign_out(auth_session.access_token)
        except Exception:
            pass
        _clear_app_session_after_logout()
        st.rerun()


nav1, nav2, nav3, nav4, nav5, nav6 = st.columns(6)

with nav1:
    if st.button("Overview", key="nav_home", use_container_width=True):
        st.session_state.selected_flow = "home"
        st.rerun()

with nav2:
    if st.button("Oportunidades", key="nav_scout", use_container_width=True):
        st.session_state.selected_flow = "scout"
        st.rerun()

with nav3:
    if st.button("Career Fit", key="nav_curator", use_container_width=True):
        st.session_state.selected_flow = "curator"
        st.rerun()

with nav4:
    if st.button("Candidaturas", key="nav_applications", use_container_width=True):
        st.session_state.selected_flow = "applications"
        st.rerun()

with nav5:
    if st.button("Coach", key="nav_coach", use_container_width=True):
        st.session_state.selected_flow = "coach"
        st.rerun()

with nav6:
    if st.button("Relatórios", key="nav_report", use_container_width=True):
        st.session_state.selected_flow = "report"
        st.rerun()

with st.expander("Perfil e currículo", expanded=False):
    repo_col, upload_col, info_col = st.columns([1.25, 1.05, 1.1])

    repository_profiles = []
    if st.session_state.persistence_ready and st.session_state.career_user_id:
        try:
            repository_profiles = get_profile_repository(
                st.session_state.career_user_id
            )
        except Exception as exc:
            st.session_state.persistence_error = str(exc)

    with repo_col:
        st.markdown("### Banco de perfis")

        if repository_profiles:
            profile_ids = [item["id"] for item in repository_profiles]
            current_profile_id = st.session_state.career_profile_id
            current_index = (
                profile_ids.index(current_profile_id)
                if current_profile_id in profile_ids
                else 0
            )

            selected_profile_id = st.selectbox(
                "Versões disponíveis",
                options=profile_ids,
                index=current_index,
                format_func=lambda profile_id: next(
                    (
                        ("● " if item.get("is_active") else "")
                        + (item.get("profile_name") or "Perfil")
                        for item in repository_profiles
                        if item["id"] == profile_id
                    ),
                    profile_id,
                ),
                key="profile_repository_selector",
            )

            selected_profile = next(
                (
                    item
                    for item in repository_profiles
                    if item["id"] == selected_profile_id
                ),
                None,
            )

            if selected_profile:
                source_label = selected_profile.get("source_name") or "Fonte não registrada"
                created_label = (selected_profile.get("created_at") or "")[:10]
                st.caption(
                    f"Fonte: {source_label}"
                    + (f" · Criado em {created_label}" if created_label else "")
                )

            if st.button(
                "Usar perfil selecionado",
                key="activate_repository_profile",
                use_container_width=True,
            ):
                try:
                    activated = activate_profile(
                        st.session_state.career_user_id,
                        selected_profile_id,
                    )
                    if activated:
                        activated_text = activated.get("raw_profile_text") or default_profile
                        activated_type = activated.get("profile_type") or "resume"

                        st.session_state.career_profile_id = activated["id"]
                        st.session_state.persisted_profile_signature = (
                            activated.get("content_hash")
                            or hashlib.sha256(
                                activated_text.encode("utf-8", errors="ignore")
                            ).hexdigest()
                        )

                        if activated_type == "default":
                            st.session_state.resume_text = None
                            st.session_state.resume_name = None
                            st.session_state.resume_source_name = None
                        else:
                            st.session_state.resume_text = activated_text
                            st.session_state.resume_name = (
                                activated.get("profile_name") or "Currículo"
                            )
                            st.session_state.resume_source_name = activated.get("source_name")

                        st.session_state.scout_results = None
                        st.session_state.career_report = None
                        st.session_state.career_report_pdf = None
                        st.session_state.candidate_name_input = ""
                        reset_coach()
                        reset_opportunity_analysis()
                        st.rerun()
                except Exception as exc:
                    st.error(str(exc))

            st.caption(f"{len(repository_profiles)} versão(ões) armazenada(s).")
        else:
            st.info("Nenhuma versão armazenada ainda.")

    with upload_col:
        st.markdown("### Adicionar currículo")
        profile_version_name = st.text_input(
            "Nome da versão",
            placeholder="Ex.: CV Comercial",
            key="profile_version_name_input",
        )

        uploaded_resume = st.file_uploader(
            "Adicionar PDF ou DOCX",
            type=["pdf", "docx"],
            help="O currículo será armazenado como uma nova versão do perfil.",
            key="top_resume_uploader",
        )

        if uploaded_resume is not None:
            try:
                extracted_text = extract_resume_text(
                    uploaded_resume.name,
                    uploaded_resume.getvalue(),
                )
                logical_name = (
                    profile_version_name.strip()
                    if profile_version_name.strip()
                    else Path(uploaded_resume.name).stem
                )

                if (
                    st.session_state.resume_source_name != uploaded_resume.name
                    or st.session_state.resume_text != extracted_text
                    or st.session_state.resume_name != logical_name
                ):
                    st.session_state.resume_text = extracted_text
                    st.session_state.resume_name = logical_name
                    st.session_state.resume_source_name = uploaded_resume.name
                    st.session_state.scout_results = None
                    st.session_state.career_report = None
                    st.session_state.career_report_pdf = None
                    st.session_state.candidate_name_input = ""
                    st.session_state.career_profile_id = None
                    st.session_state.persisted_profile_signature = None

                    reset_coach()
                    reset_opportunity_analysis()
                    st.rerun()

            except ResumeParserError as exc:
                st.error(str(exc))

    with info_col:
        st.markdown("### Perfil ativo")
        st.write(f"**Candidato:** {candidate_display}")
        st.write(
            f"**Versão:** "
            f"{st.session_state.resume_name if st.session_state.resume_text else 'Perfil padrão'}"
        )
        if st.session_state.resume_source_name:
            st.caption(f"Arquivo: {st.session_state.resume_source_name}")

        st.write(
            f"**Senioridade:** "
            f"{structured_profile.seniority or 'Não identificada'}"
        )

        if st.session_state.persistence_error:
            st.caption(
                "Persistência em modo degradado: "
                + st.session_state.persistence_error
            )

        if st.session_state.resume_text:
            if st.button(
                "Voltar ao perfil padrão",
                key="top_use_default",
                use_container_width=True,
            ):
                default_repository_profile = next(
                    (
                        item
                        for item in repository_profiles
                        if item.get("profile_type") == "default"
                    ),
                    None,
                )

                if default_repository_profile:
                    try:
                        activate_profile(
                            st.session_state.career_user_id,
                            default_repository_profile["id"],
                        )
                        st.session_state.career_profile_id = default_repository_profile["id"]
                        st.session_state.persisted_profile_signature = (
                            default_repository_profile.get("content_hash")
                        )
                    except Exception as exc:
                        st.session_state.persistence_error = str(exc)
                else:
                    st.session_state.career_profile_id = None
                    st.session_state.persisted_profile_signature = None

                st.session_state.resume_text = None
                st.session_state.resume_name = None
                st.session_state.resume_source_name = None
                st.session_state.scout_results = None
                st.session_state.career_report = None
                st.session_state.career_report_pdf = None
                st.session_state.candidate_name_input = ""
                reset_coach()
                reset_opportunity_analysis()
                st.rerun()


if st.session_state.selected_flow == "home":

    # ---------------------------------------------------------
    # SPRINT 2 — LONGITUDINAL CAREER INTELLIGENCE
    # ---------------------------------------------------------
    career_history = []
    application_history = []
    career_analytics = None
    application_intelligence = None
    executive_intelligence = None

    if st.session_state.persistence_ready and st.session_state.career_user_id:
        try:
            career_history = get_analysis_history(
                st.session_state.career_user_id,
                limit=100,
            )
            application_history = get_application_pipeline(
                st.session_state.career_user_id
            )

            career_analytics = analyze_career_history(
                career_history
            )
            application_intelligence = analyze_application_history(
                applications=application_history,
                analyses=career_history,
            )
            executive_intelligence = build_executive_intelligence(
                analyses=career_history,
                applications=application_history,
            )
        except Exception as exc:
            st.session_state.persistence_error = str(exc)

    resume_label = (
        st.session_state.resume_name
        if st.session_state.resume_text
        else "Perfil padrão"
    )

    persisted_analysis_title = next(
        (
            str(item.get("job_title") or "").strip()
            for item in career_history
            if str(item.get("job_title") or "").strip()
        ),
        "",
    )

    analysis_label = (
        st.session_state.analyzed_job_title
        or persisted_analysis_title
        or "Nenhuma oportunidade analisada"
    )

    render_html(
        f"""
<div class="cc-strip">
    <div class="cc-strip-cell">
        <div class="cc-label">Perfil ativo</div>
        <div class="cc-value">{candidate_display}</div>
        <div class="cc-sub">{structured_profile.seniority or 'Senioridade não identificada'}</div>
    </div>
    <div class="cc-strip-cell">
        <div class="cc-label">Currículo</div>
        <div class="cc-value">{resume_label}</div>
        <div class="cc-sub">Fonte utilizada na análise</div>
    </div>
    <div class="cc-strip-cell">
        <div class="cc-label">Última análise</div>
        <div class="cc-value">{analysis_label}</div>
        <div class="cc-sub">Contexto profissional atual</div>
    </div>
</div>
"""
    )

    areas_count = len(structured_profile.areas)
    hard_count = len(structured_profile.hard_skills)
    tools_count = len(structured_profile.tools)
    mgmt_count = len(structured_profile.management_skills)

    completeness = 0
    completeness += 20 if structured_profile.candidate_name else 0
    completeness += 20 if (
        structured_profile.seniority
        and structured_profile.seniority != "Não identificada"
    ) else 0
    completeness += min(20, areas_count * 5)
    completeness += min(20, hard_count * 3)
    completeness += min(20, tools_count * 3)
    completeness = min(completeness, 100)

    competence_score = min(
        100,
        35 + hard_count * 6 + tools_count * 3,
    )

    experience_score = min(
        100,
        45 + mgmt_count * 7,
    )

    seniority_score = (
        100
        if (
            structured_profile.seniority
            and structured_profile.seniority != "Não identificada"
        )
        else 35
    )

    alignment_score = completeness

    overall_score = round(
        competence_score * .30
        + experience_score * .25
        + seniority_score * .25
        + alignment_score * .20
    )

    if overall_score >= 80:
        overall_label = "Strong Fit"
    elif overall_score >= 65:
        overall_label = "Competitive"
    elif overall_score >= 50:
        overall_label = "Developing"
    else:
        overall_label = "Build Profile"

    # Quando existe histórico persistido, o Career Intelligence Score deixa de
    # ser apenas uma leitura estática do perfil e passa a refletir a trajetória.
    score_note = (
        "Seu perfil é avaliado por evidências profissionais, "
        "competências, senioridade e completude das informações."
    )

    if (
        executive_intelligence is not None
        and career_analytics is not None
        and career_analytics.total_analyses > 0
    ):
        overall_score = round(
            executive_intelligence.career_intelligence_score
        )

        if overall_score >= 80:
            overall_label = "Strong Intelligence"
        elif overall_score >= 65:
            overall_label = "Competitive"
        elif overall_score >= 50:
            overall_label = "Developing"
        else:
            overall_label = "Build Momentum"

        score_note = (
            f"Score longitudinal · {career_analytics.total_analyses} análise(s) · "
            f"Momentum {executive_intelligence.momentum} · "
            f"Confiança {executive_intelligence.confidence_score:.0f}%."
        )

    if st.session_state.ats_report is not None:
        next_title = (
            st.session_state.analyzed_job_title
            or "Oportunidade analisada"
        )
        match_score = st.session_state.ats_report.score
        mandatory = st.session_state.ats_report.mandatory_coverage
        keyword = st.session_state.ats_report.keyword_coverage
        if st.session_state.career_decision is not None:
            decision = st.session_state.career_decision
            next_copy = decision.next_best_action
            next_badges = [
                decision.decision,
                f"Decision {decision.decision_score}%",
                f"ATS {match_score}%",
            ]
        else:
            next_copy = (
                "A oportunidade já possui análise de aderência "
                "e inteligência ATS."
            )
            next_badges = [
                f"ATS {match_score}%",
                f"Obrigatórios {mandatory}%",
                f"Keywords {keyword}%",
            ]
    else:
        next_title = "Analise uma oportunidade"
        match_score = None
        next_copy = (
            "Cole uma vaga para comparar requisitos, senioridade, "
            "ATS e estratégia de candidatura."
        )
        next_badges = [
            "Career Fit",
            "ATS Intelligence",
            "CV Tailoring",
        ]

    if (
        st.session_state.ats_report is None
        and executive_intelligence is not None
        and executive_intelligence.next_best_action
    ):
        next_title = "Prioridade da trajetória"
        next_copy = executive_intelligence.next_best_action
        match_score = None
        next_badges = [
            f"Momentum {executive_intelligence.momentum}",
            f"Career Fit {executive_intelligence.career_fit_average:.0f}%",
            f"ATS {executive_intelligence.ats_average:.0f}%",
        ]

    badges_html = "".join(
        f'<span class="cc-badge">{item}</span>'
        for item in next_badges
    )

    match_html = (
        f'<span class="cc-match">{match_score}%</span>'
        if match_score is not None
        else ""
    )

    activities = []

    if st.session_state.resume_text:
        activities.append(
            (
                "CV",
                "Currículo carregado",
                st.session_state.resume_name or "Currículo",
            )
        )

    if st.session_state.curator_result is not None:
        activities.append(
            (
                "✓",
                "Career Fit concluído",
                st.session_state.analyzed_job_title or "Oportunidade",
            )
        )

    if st.session_state.ats_report is not None:
        activities.append(
            (
                "A",
                "ATS Intelligence",
                f"{st.session_state.ats_report.score}%",
            )
        )

    if st.session_state.tailoring_report is not None:
        activities.append(
            (
                "T",
                "CV Tailoring gerado",
                f"{st.session_state.tailoring_report.tailoring_score}%",
            )
        )

    if st.session_state.scout_results:
        activities.append(
            (
                "R",
                "Radar atualizado",
                f"{len(st.session_state.scout_results)} caminhos",
            )
        )

    if st.session_state.coach_feedback:
        activities.append(
            (
                "C",
                "Entrevista simulada",
                f"{len(st.session_state.coach_feedback)} etapas",
            )
        )

    if not activities:
        activities = [
            ("•", "Perfil disponível", "Pronto para análise"),
            ("→", "Próxima ação", "Analise uma oportunidade"),
        ]

    activity_html = "".join(
        f"""
<div class="cc-act">
    <div class="cc-act-icon">{icon}</div>
    <div>
        <div class="cc-act-title">{title}</div>
        <div class="cc-act-sub">{sub}</div>
    </div>
</div>
"""
        for icon, title, sub in activities[:5]
    )

    score_col, next_col, activity_col = st.columns(
        [1.15, 1.15, .62],
        gap="medium",
    )

    with score_col:
        with st.container(border=True):
            render_html(
                f"""
<div class="cc-card-kicker">Career Intelligence Score</div>
<div class="cc-score-layout">
    <div>
        <div class="cc-ring">
            <div class="cc-ring-inner">
                <div class="cc-ring-score">{overall_score}</div>
                <div class="cc-ring-caption">de 100</div>
            </div>
        </div>
        <div class="cc-score-label">{overall_label}</div>
    </div>
    <div>
        <div class="cc-note">{score_note}</div>

        <div class="cc-bar-row">
            <span>Competências</span>
            <div class="cc-bar">
                <div class="cc-bar-fill" style="width:{competence_score}%"></div>
            </div>
            <span>{competence_score}%</span>
        </div>

        <div class="cc-bar-row">
            <span>Experiência</span>
            <div class="cc-bar">
                <div class="cc-bar-fill" style="width:{experience_score}%"></div>
            </div>
            <span>{experience_score}%</span>
        </div>

        <div class="cc-bar-row">
            <span>Senioridade</span>
            <div class="cc-bar">
                <div class="cc-bar-fill" style="width:{seniority_score}%"></div>
            </div>
            <span>{seniority_score}%</span>
        </div>

        <div class="cc-bar-row">
            <span>Perfil</span>
            <div class="cc-bar">
                <div class="cc-bar-fill" style="width:{alignment_score}%"></div>
            </div>
            <span>{alignment_score}%</span>
        </div>
    </div>
</div>
"""
            )

    with next_col:
        with st.container(border=True):
            render_html(
                f"""
<div class="cc-card-kicker">Next Best Action</div>
<div class="cc-next-box">
    {match_html}
    <div class="cc-label">Oportunidade em destaque</div>
    <div class="cc-next-title">{next_title}</div>
    <div class="cc-sub">Career Intelligence Workspace</div>
    <div class="cc-next-copy">{next_copy}</div>
    <div class="cc-badges">{badges_html}</div>
</div>
"""
            )

            if st.button(
                "Analisar oportunidade",
                key="home_primary_action",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.selected_flow = "curator"
                st.rerun()

    with activity_col:
        with st.container(border=True):
            render_html(
                f"""
<div class="cc-card-kicker">Atividade recente</div>
<div class="cc-activity">{activity_html}</div>
"""
            )

    with st.container(border=True):
        render_html(
            f"""
<div class="cc-card-kicker">Sua jornada de carreira</div>
<div class="cc-journey">
    <div class="cc-step">
        <div class="cc-dot"></div>
        <div class="cc-step-no">01</div>
        <div class="cc-step-name">Perfil</div>
        <div class="cc-step-copy">Estruture suas evidências profissionais.</div>
    </div>
    <div class="cc-step">
        <div class="cc-dot"></div>
        <div class="cc-step-no">02</div>
        <div class="cc-step-name">Descobrir</div>
        <div class="cc-step-copy">Explore caminhos profissionais aderentes.</div>
    </div>
    <div class="cc-step {'pending' if st.session_state.curator_result is None else ''}">
        <div class="cc-dot"></div>
        <div class="cc-step-no">03</div>
        <div class="cc-step-name">Career Fit</div>
        <div class="cc-step-copy">Avalie vaga, requisitos e ATS.</div>
    </div>
    <div class="cc-step {'pending' if st.session_state.tailoring_report is None else ''}">
        <div class="cc-dot"></div>
        <div class="cc-step-no">04</div>
        <div class="cc-step-name">CV Intelligence</div>
        <div class="cc-step-copy">Otimize posicionamento e evidências.</div>
    </div>
    <div class="cc-step {'pending' if not st.session_state.coach_feedback else ''}">
        <div class="cc-dot"></div>
        <div class="cc-step-no">05</div>
        <div class="cc-step-name">Interview Coach</div>
        <div class="cc-step-copy">Prepare respostas contextualizadas.</div>
    </div>
</div>
"""
        )

    # ---------------------------------------------------------
    # EXECUTIVE DASHBOARD — SPRINT 2
    # ---------------------------------------------------------
    if executive_intelligence is not None:
        st.markdown("### Executive Career Intelligence")

        ex1, ex2, ex3, ex4, ex5 = st.columns(5)

        with ex1:
            st.metric(
                "Career Intelligence",
                f"{executive_intelligence.career_intelligence_score:.0f}/100",
            )

        with ex2:
            trend_delta = (
                f"{career_analytics.career_fit_trend:+.1f}"
                if career_analytics is not None
                else None
            )
            st.metric(
                "Career Fit médio",
                f"{executive_intelligence.career_fit_average:.1f}%",
                delta=trend_delta,
            )

        with ex3:
            st.metric(
                "ATS médio",
                f"{executive_intelligence.ats_average:.1f}%",
            )

        with ex4:
            st.metric(
                "Entrevistas",
                executive_intelligence.interviews,
                delta=(
                    f"{executive_intelligence.interview_rate:.1f}% conversão"
                    if executive_intelligence.applications
                    else None
                ),
            )

        with ex5:
            st.metric(
                "Ofertas",
                executive_intelligence.offers,
                delta=(
                    f"{executive_intelligence.offer_rate:.1f}% conversão"
                    if executive_intelligence.interviews
                    else None
                ),
            )

        exec_left, exec_right = st.columns(
            [1.25, 1],
            gap="medium",
        )

        with exec_left:
            with st.container(border=True):
                st.markdown("#### Inteligência longitudinal")
                st.write(executive_intelligence.summary)

                if executive_intelligence.executive_insights:
                    for insight in executive_intelligence.executive_insights[:4]:
                        st.write(f"• {insight}")

        with exec_right:
            with st.container(border=True):
                st.markdown("#### Prioridades")

                if executive_intelligence.development_priorities:
                    for priority in executive_intelligence.development_priorities[:3]:
                        st.write(f"• {priority}")
                elif executive_intelligence.top_risks:
                    for risk in executive_intelligence.top_risks[:3]:
                        st.write(f"• {risk}")
                else:
                    st.write(
                        "O histórico ainda não identificou uma prioridade "
                        "recorrente de desenvolvimento."
                    )

                st.caption(
                    f"Momentum: {executive_intelligence.momentum} · "
                    f"Confiança: {executive_intelligence.confidence_score:.0f}%"
                )

        if career_analytics is not None and career_analytics.trajectory:
            with st.expander(
                "Ver evolução das análises",
                expanded=False,
            ):
                trend_rows = [
                    {
                        "Análise": point.index,
                        "Data": (point.created_at or "")[:10],
                        "Oportunidade": point.job_title or "Oportunidade",
                        "Empresa": point.company or "—",
                        "Career Fit": point.career_fit_score,
                        "ATS": point.ats_score,
                        "Tailoring": point.tailoring_score,
                    }
                    for point in career_analytics.trajectory[-12:]
                ]
                st.dataframe(
                    trend_rows,
                    use_container_width=True,
                    hide_index=True,
                )

        if (
            application_intelligence is not None
            and application_intelligence.profile_performance
        ):
            identified_profile_performance = [
                item
                for item in application_intelligence.profile_performance
                if item.profile_id != "perfil_nao_identificado"
            ]

            if identified_profile_performance:
                with st.expander(
                    "Performance por versão de perfil",
                    expanded=False,
                ):
                    profile_name_map = {
                        item["id"]: (
                            item.get("profile_name")
                            or item.get("source_name")
                            or item["id"]
                        )
                        for item in repository_profiles
                    }

                    performance_rows = [
                        {
                            "Perfil": profile_name_map.get(
                                item.profile_id,
                                item.profile_id,
                            ),
                            "Candidaturas": item.total_applications,
                            "Entrevistas": item.interviews,
                            "Ofertas": item.offers,
                            "Interview Rate": f"{item.interview_rate:.1f}%",
                            "Offer Rate": f"{item.offer_rate:.1f}%",
                        }
                        for item in identified_profile_performance
                    ]

                    st.dataframe(
                        performance_rows,
                        use_container_width=True,
                        hide_index=True,
                    )

        st.markdown("")

    bottom1, bottom2, bottom3 = st.columns(
        [1.25, .72, .82],
        gap="medium",
    )

    if st.session_state.scout_results:
        rows = []

        for result in st.session_state.scout_results[:4]:
            css_class = (
                "cc-good"
                if result.score >= 75
                else "cc-mid"
            )

            rows.append(
                f"""
<tr>
    <td>{result.title}</td>
    <td>Perfil ativo</td>
    <td class="{css_class}">{result.score}%</td>
    <td>{result.level}</td>
</tr>
"""
            )

        opportunity_rows = "".join(rows)

    else:
        opportunity_rows = """
<tr>
    <td colspan="4" style="color:#6f7f95;">
        Execute o Radar de Oportunidades para preencher este painel.
    </td>
</tr>
"""

    with bottom1:
        with st.container(border=True):
            render_html(
                f"""
<div class="cc-card-kicker">Oportunidades recomendadas</div>
<table class="cc-table">
    <thead>
        <tr>
            <th>Posição</th>
            <th>Fonte</th>
            <th>Match</th>
            <th>Nível</th>
        </tr>
    </thead>
    <tbody>{opportunity_rows}</tbody>
</table>
"""
            )

            if st.button(
                "Explorar oportunidades",
                key="home_scout_action",
                use_container_width=True,
            ):
                st.session_state.selected_flow = "scout"
                st.rerun()

    insight_items = []

    if structured_profile.management_skills:
        insight_items.append(
            (
                "✓",
                "Competências de gestão",
                f"{len(structured_profile.management_skills)} competências identificadas",
            )
        )

    if structured_profile.hard_skills:
        insight_items.append(
            (
                "#",
                "Base técnica",
                f"{len(structured_profile.hard_skills)} hard skills reconhecidas",
            )
        )

    if structured_profile.evidence_terms:
        insight_items.append(
            (
                "↗",
                "Evidências profissionais",
                f"{len(structured_profile.evidence_terms)} termos de resultado",
            )
        )

    if (
        st.session_state.ats_report is not None
        and st.session_state.ats_report.mandatory_gaps
    ):
        insight_items.append(
            (
                "!",
                "Gap prioritário",
                st.session_state.ats_report.mandatory_gaps[0],
            )
        )

    if not insight_items:
        insight_items = [
            (
                "→",
                "Comece pelo Career Fit",
                "Compare seu perfil com uma vaga real.",
            ),
            (
                "+",
                "Amplie o perfil",
                "Carregue um currículo completo para enriquecer a análise.",
            ),
        ]

    insight_html = "".join(
        f"""
<div class="cc-insight">
    <div class="cc-insight-icon">{icon}</div>
    <div>
        <div class="cc-insight-title">{title}</div>
        <div class="cc-insight-copy">{copy}</div>
    </div>
</div>
"""
        for icon, title, copy in insight_items[:4]
    )

    with bottom2:
        with st.container(border=True):
            render_html(
                f"""
<div class="cc-card-kicker">Insights para você</div>
{insight_html}
"""
            )

    with bottom3:
        with st.container(border=True):
            render_html(
                """
<div class="cc-card-kicker">Acessos rápidos</div>
"""
            )

            q1, q2 = st.columns(2)

            with q1:
                if st.button(
                    "Career Fit",
                    key="quick_fit",
                    use_container_width=True,
                ):
                    st.session_state.selected_flow = "curator"
                    st.rerun()

                if st.button(
                    "Coach",
                    key="quick_coach",
                    use_container_width=True,
                ):
                    st.session_state.selected_flow = "coach"
                    st.rerun()

            with q2:
                if st.button(
                    "Oportunidades",
                    key="quick_scout",
                    use_container_width=True,
                ):
                    st.session_state.selected_flow = "scout"
                    st.rerun()

                if st.button(
                    "Relatório",
                    key="quick_report",
                    use_container_width=True,
                ):
                    st.session_state.selected_flow = "report"
                    st.rerun()

# =========================================================
# SCOUT
# =========================================================

elif st.session_state.selected_flow == "scout":

    st.markdown(
        """
        <div class="cc-module-header">
            <div class="cc-agent-label">Scout</div>
            <h2>Oportunidades</h2>
            <p>
                Identifique funções profissionais com maior aderência
                às competências e conhecimentos registrados no perfil ativo.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.resume_text:
        st.success(
            f"Analisando currículo: {st.session_state.resume_name}"
        )

    with st.expander(
        "Ver diagnóstico utilizado pelo Scout"
    ):

        st.write(
            f"**Candidato:** {structured_profile.candidate_name}"
        )

        st.write(
            f"**Senioridade:** {structured_profile.seniority}"
        )

        st.write(
            f"**Áreas:** {format_items(structured_profile.areas)}"
        )

        st.write(
            f"**Hard Skills:** "
            f"{format_items(structured_profile.hard_skills)}"
        )

        st.write(
            f"**Gestão:** "
            f"{format_items(structured_profile.management_skills)}"
        )

    if st.button(
        "Mapear oportunidades",
        type="primary",
        use_container_width=True,
    ):

        st.session_state.scout_results = discover_roles(
            profile
        )

        st.session_state.career_report = None
        st.session_state.career_report_pdf = None

    results = st.session_state.scout_results

    if results:

        st.markdown(
            "### Ranking de aderência"
        )

        top_result = results[0]

        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric(
                "Melhor aderência",
                f"{top_result.score}%",
            )

        with m2:
            st.metric(
                "Função prioritária",
                top_result.title,
            )

        with m3:
            st.metric(
                "Funções analisadas",
                len(results),
            )

        st.markdown("")

        for position, result in enumerate(
            results,
            start=1,
        ):

            with st.container(
                border=True
            ):

                col_rank, col_info, col_score = st.columns(
                    [0.4, 2.5, 1]
                )

                with col_rank:
                    st.markdown(
                        f"## {position}"
                    )

                with col_info:
                    st.markdown(
                        f"### {result.title}"
                    )
                    st.write(
                        f"**{result.level}**"
                    )
                    st.caption(
                        result.reason
                    )

                with col_score:
                    st.metric(
                        "Aderência",
                        f"{result.score}%",
                    )

                st.progress(
                    result.score / 100
                )


# =========================================================
# CURATOR
# =========================================================

elif st.session_state.selected_flow == "curator":

    st.markdown(
        """<div class="cc-module-header">
<div class="cc-agent-label">Curator 2.0</div>
<h2>Career Fit + ATS Intelligence</h2>
<p>Compare o perfil ativo com uma oportunidade, avalie aderência, cobertura ATS, gaps, recomendações e estratégia de customização do currículo.</p>
</div>""",
        unsafe_allow_html=True,
    )

    if st.session_state.resume_text:
        st.success(
            f"Perfil analisado: {st.session_state.resume_name}"
        )

    left, right = st.columns(
        [1.55, 1]
    )

    with left:

        with st.container(
            border=True
        ):

            st.markdown(
                "### Oportunidade"
            )

            job_title = st.text_input(
                "Cargo / título da oportunidade",
                key="job_title_input",
                placeholder="Ex.: Gerente de Projetos e Performance",
            )

            job_description = st.text_area(
                "Descrição da vaga",
                key="job_description_input",
                height=320,
                placeholder=(
                    "Cole aqui a descrição completa da oportunidade, "
                    "incluindo responsabilidades, requisitos obrigatórios, "
                    "diferenciais e informações sobre a função."
                ),
            )

            analyze_col, clear_col = st.columns([1.7, 1])

            with analyze_col:
                analyze = st.button(
                    "Analisar oportunidade",
                    type="primary",
                    use_container_width=True,
                )

            with clear_col:
                st.button(
                    "Limpar análise",
                    key="clear_opportunity_analysis",
                    use_container_width=True,
                    on_click=clear_opportunity_workspace,
                )

    with right:

        with st.container(
            border=True
        ):

            st.markdown(
                "### Perfil profissional identificado"
            )

            st.write(
                f"**Candidato:** "
                f"{structured_profile.candidate_name}"
            )

            st.write(
                f"**Senioridade:** "
                f"{structured_profile.seniority}"
            )

            st.write(
                f"**Áreas:** "
                f"{format_items(structured_profile.areas)}"
            )

            st.write(
                f"**Hard Skills:** "
                f"{format_items(structured_profile.hard_skills)}"
            )

            st.write(
                f"**Ferramentas:** "
                f"{format_items(structured_profile.tools)}"
            )

            st.caption(
                "O Curator 2.0 usa o currículo ativo como fonte de evidências."
            )

    if analyze:

        if not job_description.strip():

            st.warning(
                "Cole a descrição da vaga antes de iniciar a análise."
            )

        else:

            analyzed_title = (
                job_title.strip()
                if job_title.strip()
                else "Oportunidade analisada"
            )

            with st.spinner(
                "Executando Opportunity Intelligence, Fit, ATS, Decision Intelligence e CV Tailoring..."
            ):

                opportunity_profile = analyze_opportunity(
                    job_title=analyzed_title,
                    job_description=job_description,
                )

                curator_result = analyze_compatibility(
                    profile=profile,
                    job_description=job_description,
                )

                ats_report = analyze_ats(
                    profile=profile,
                    job_description=job_description,
                )

                recommendation_report = build_recommendations(
                    ats_report
                )

                tailoring_report = tailor_cv(
                    profile_text=profile,
                    job_description=job_description,
                    job_title=analyzed_title,
                    ats_report=ats_report,
                    recommendation_report=recommendation_report,
                )

                career_decision = build_career_decision(
                    career_fit_report=curator_result,
                    ats_report=ats_report,
                    tailoring_report=tailoring_report,
                    opportunity_profile=opportunity_profile,
                )

            st.session_state.curator_result = curator_result
            st.session_state.ats_report = ats_report
            st.session_state.recommendation_report = recommendation_report
            st.session_state.tailoring_report = tailoring_report
            st.session_state.opportunity_profile = opportunity_profile
            st.session_state.career_decision = career_decision
            st.session_state.analyzed_job_title = analyzed_title
            st.session_state.analyzed_job_description = job_description
            st.session_state.career_application_id = None

            if (
                st.session_state.persistence_ready
                and st.session_state.career_user_id
                and st.session_state.career_profile_id
            ):
                try:
                    opportunity_id = persist_opportunity(
                        user_id=st.session_state.career_user_id,
                        job_title=analyzed_title,
                        job_description=job_description,
                        source="Career Fit",
                    )

                    analysis_id = persist_career_analysis(
                        user_id=st.session_state.career_user_id,
                        profile_id=st.session_state.career_profile_id,
                        opportunity_id=opportunity_id,
                        career_fit_report=curator_result,
                        ats_report=ats_report,
                        recommendation_report=recommendation_report,
                        tailoring_report=tailoring_report,
                    )

                    st.session_state.career_opportunity_id = opportunity_id
                    st.session_state.career_analysis_id = analysis_id
                    st.session_state.persistence_error = None

                except Exception as exc:
                    st.session_state.persistence_error = str(exc)

            reset_coach()

    result = st.session_state.curator_result
    ats_report = st.session_state.ats_report
    recommendation_report = st.session_state.recommendation_report
    tailoring_report = st.session_state.tailoring_report
    opportunity_profile = st.session_state.opportunity_profile
    career_decision = st.session_state.career_decision

    if (
        result
        and ats_report
        and recommendation_report
        and tailoring_report
        and opportunity_profile
        and career_decision
    ):

        st.markdown(
            "## Diagnóstico integrado"
        )

        if st.session_state.analyzed_job_title:
            st.caption(
                f"Oportunidade analisada: "
                f"{st.session_state.analyzed_job_title}"
            )

        metric1, metric2, metric3, metric4 = st.columns(4)

        with metric1:
            st.metric(
                "Career Fit",
                f"{result['score']}%",
            )

        with metric2:
            st.metric(
                "ATS Score",
                f"{ats_report.score}%",
            )

        with metric3:
            st.metric(
                "Obrigatórios",
                f"{ats_report.mandatory_coverage}%",
            )

        with metric4:
            st.metric(
                "Tailoring",
                f"{tailoring_report.tailoring_score}%",
            )

        st.markdown("")

        with st.container(border=True):
            st.markdown("### Decision Intelligence")
            d1, d2, d3 = st.columns(3)
            with d1:
                st.metric("Recomendação", career_decision.decision)
            with d2:
                st.metric("Decision Score", f"{career_decision.decision_score}%")
            with d3:
                st.metric("Confiança", f"{career_decision.confidence_score}%")
            st.write(f"**Next Best Action:** {career_decision.next_best_action}")
            if career_decision.rationale:
                with st.expander("Por que esta recomendação?"):
                    for item in career_decision.rationale:
                        st.write(f"• {item}")

        with st.expander("Opportunity Intelligence", expanded=False):
            o1, o2, o3 = st.columns(3)
            with o1:
                st.metric("Senioridade da vaga", opportunity_profile.seniority)
            with o2:
                st.metric("Modelo", opportunity_profile.work_model)
            with o3:
                st.metric("Confiança da extração", f"{opportunity_profile.confidence_score}%")
            st.write(f"**Localização:** {opportunity_profile.location or 'Não identificada'}")
            st.write(f"**Competências detectadas:** {format_items(opportunity_profile.skills)}")
            st.write(f"**Ferramentas:** {format_items(opportunity_profile.tools)}")
            st.write(f"**Metodologias:** {format_items(opportunity_profile.methodologies)}")

        tab_fit, tab_ats, tab_rec, tab_cv = st.tabs(
            [
                "🎯 Fit",
                "🧠 ATS Intelligence",
                "🧭 Recomendações",
                "📝 CV Tailoring",
            ]
        )

        # =================================================
        # TAB FIT
        # =================================================

        with tab_fit:

            fit1, fit2, fit3 = st.columns(3)

            with fit1:
                st.metric(
                    "Classificação",
                    result["compatibility"],
                )

            with fit2:
                st.metric(
                    "Cobertura",
                    f"{result['score_details']['coverage']}%",
                )

            with fit3:
                st.metric(
                    "Requisitos analisados",
                    result["requirements_count"],
                )

            col_strengths, col_gaps = st.columns(2)

            with col_strengths:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### ✓ Aderências"
                    )

                    if result["strengths"]:

                        for skill in result["strengths"]:
                            st.success(
                                skill
                            )

                    else:

                        st.info(
                            "Nenhuma aderência foi identificada "
                            "nos requisitos analisados."
                        )

            with col_gaps:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### ⚠ Pontos sem evidência"
                    )

                    if result["gaps"]:

                        for skill in result["gaps"]:
                            st.warning(
                                skill
                            )

                    else:

                        st.success(
                            "Nenhuma lacuna foi identificada "
                            "nos requisitos analisados."
                        )

            st.markdown(
                "### Aderência por dimensão"
            )

            if result["category_summary"]:

                for category, summary in result["category_summary"].items():

                    with st.container(
                        border=True
                    ):

                        c1, c2, c3 = st.columns(
                            [2, 1, 1]
                        )

                        with c1:
                            st.write(
                                f"**{category}**"
                            )

                        with c2:
                            st.write(
                                f"{summary['attended']} de "
                                f"{summary['total']} atendidos"
                            )

                        with c3:
                            st.metric(
                                "Score",
                                f"{summary['score']}%",
                            )

                        st.progress(
                            summary["score"] / 100
                        )

            with st.expander(
                "Ver detalhamento do Fit"
            ):

                for item in result["matches"]:

                    st.write(
                        f"**{item.skill}** · "
                        f"{item.category} · "
                        f"{item.priority} · "
                        f"{item.status}"
                    )

        # =================================================
        # TAB ATS
        # =================================================

        with tab_ats:

            ats1, ats2, ats3, ats4 = st.columns(4)

            with ats1:
                st.metric(
                    "ATS Score",
                    f"{ats_report.score}%",
                )

            with ats2:
                st.metric(
                    "Classificação",
                    ats_report.classification,
                )

            with ats3:
                st.metric(
                    "Keywords",
                    f"{ats_report.keyword_coverage}%",
                )

            with ats4:
                seniority_display = (
                    f"{ats_report.seniority_score}%"
                    if ats_report.seniority_score is not None
                    else "N/A"
                )

                st.metric(
                    "Senioridade",
                    seniority_display,
                )

            a1, a2 = st.columns(2)

            with a1:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Requisitos obrigatórios"
                    )

                    st.metric(
                        "Cobertura",
                        f"{ats_report.mandatory_coverage}%",
                    )

                    if ats_report.mandatory_gaps:

                        st.markdown(
                            "**Gaps obrigatórios**"
                        )

                        for skill in ats_report.mandatory_gaps:
                            st.warning(
                                skill
                            )

                    else:

                        st.success(
                            "Nenhum gap obrigatório identificado."
                        )

            with a2:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Diferenciais"
                    )

                    st.metric(
                        "Cobertura",
                        f"{ats_report.preferred_coverage}%",
                    )

                    if ats_report.preferred_gaps:

                        st.markdown(
                            "**Diferenciais sem evidência**"
                        )

                        for skill in ats_report.preferred_gaps:
                            st.info(
                                skill
                            )

                    else:

                        st.success(
                            "Nenhum gap diferencial identificado."
                        )

            st.markdown(
                "### Requisitos detectados"
            )

            with st.expander(
                "Ver matriz ATS completa"
            ):

                for item in ats_report.requirements:

                    status_icon = (
                        "✓"
                        if item.status == "Atende"
                        else "⚠"
                    )

                    st.write(
                        f"{status_icon} **{item.skill}** · "
                        f"{item.category} · "
                        f"{item.priority} · "
                        f"{item.status}"
                    )

        # =================================================
        # TAB RECOMMENDATIONS
        # =================================================

        with tab_rec:

            st.markdown(
                "### Próximas ações prioritárias"
            )

            if recommendation_report.priority_actions:

                for action in recommendation_report.priority_actions:
                    st.warning(
                        action
                    )

            else:

                st.success(
                    "Nenhuma ação crítica foi identificada."
                )

            r1, r2 = st.columns(2)

            with r1:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Posicionamento"
                    )

                    for item in recommendation_report.positioning_guidance:
                        st.write(
                            f"• {item}"
                        )

                    st.markdown(
                        "### Currículo"
                    )

                    for item in recommendation_report.cv_guidance:
                        st.write(
                            f"• {item}"
                        )

            with r2:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Entrevista"
                    )

                    for item in recommendation_report.interview_guidance:
                        st.write(
                            f"• {item}"
                        )

            with st.expander(
                "Ver recomendações detalhadas"
            ):

                for item in recommendation_report.recommendations:

                    st.markdown(
                        f"#### {item.title}"
                    )

                    st.write(
                        f"**Categoria:** {item.category}"
                    )

                    st.write(
                        f"**Prioridade:** {item.priority}"
                    )

                    st.write(
                        item.action
                    )

                    st.caption(
                        item.rationale
                    )

        # =================================================
        # TAB CV TAILORING
        # =================================================

        with tab_cv:

            st.markdown(
                "### Estratégia de customização"
            )

            t1, t2 = st.columns(
                [2, 1]
            )

            with t1:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Headline sugerida"
                    )

                    st.write(
                        tailoring_report.headline
                    )

                    st.markdown(
                        "### Resumo profissional sugerido"
                    )

                    st.write(
                        tailoring_report.professional_summary
                    )

            with t2:

                st.metric(
                    "Tailoring Readiness",
                    f"{tailoring_report.tailoring_score}%",
                )

                st.markdown(
                    "**Competências prioritárias**"
                )

                st.write(
                    format_items(
                        tailoring_report.priority_skills
                    )
                )

                st.markdown(
                    "**Keywords ATS seguras**"
                )

                st.write(
                    format_items(
                        tailoring_report.ats_keywords
                    )
                )

            c1, c2 = st.columns(2)

            with c1:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Evidências a destacar"
                    )

                    for item in tailoring_report.evidence_to_highlight:
                        st.success(
                            item
                        )

                    st.markdown(
                        "### Recomendações de edição"
                    )

                    for item in tailoring_report.editing_recommendations:
                        st.write(
                            f"• {item}"
                        )

            with c2:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Gaps que devem ser respeitados"
                    )

                    if tailoring_report.gaps_to_respect:

                        for item in tailoring_report.gaps_to_respect:
                            st.warning(
                                item
                            )

                    else:

                        st.success(
                            "Nenhum gap crítico adicional "
                            "precisa ser protegido no tailoring."
                        )

                    st.markdown(
                        "### Ponte para entrevista"
                    )

                    for item in tailoring_report.interview_bridge:
                        st.write(
                            f"• {item}"
                        )

            st.info(
                "O CV Tailoring reorganiza e enfatiza evidências "
                "já existentes. Ele não autoriza incluir experiência, "
                "competência, cargo, formação ou resultado sem comprovação."
            )

        st.markdown("")

        tracking_col, interview_col = st.columns(2)

        with tracking_col:
            if st.session_state.career_application_id:
                st.success("Oportunidade adicionada ao acompanhamento.")
            elif (
                st.session_state.persistence_ready
                and st.session_state.career_user_id
                and st.session_state.career_opportunity_id
            ):
                if st.button(
                    "Adicionar às candidaturas",
                    key="add_application_current",
                    use_container_width=True,
                ):
                    try:
                        st.session_state.career_application_id = persist_application(
                            user_id=st.session_state.career_user_id,
                            opportunity_id=st.session_state.career_opportunity_id,
                            analysis_id=st.session_state.career_analysis_id,
                            status="planned",
                        )
                        st.session_state.persistence_error = None
                        st.rerun()
                    except Exception as exc:
                        st.session_state.persistence_error = str(exc)
            else:
                st.caption(
                    "Acompanhamento ficará disponível após a persistência da análise."
                )

        with interview_col:
            prepare_interview = st.button(
                "🎤 Preparar entrevista para esta oportunidade",
                type="primary",
                use_container_width=True,
            )

        if prepare_interview:
            reset_coach()
            st.session_state.selected_flow = "coach"
            st.rerun()


# =========================================================
# APPLICATION TRACKER
# =========================================================

elif st.session_state.selected_flow == "applications":

    st.markdown(
        """<div class="cc-module-header">
<div class="cc-agent-label">Career Pipeline</div>
<h2>Candidaturas</h2>
<p>Acompanhe oportunidades analisadas, evolução das candidaturas e indicadores da sua jornada profissional.</p>
</div>""",
        unsafe_allow_html=True,
    )

    if not st.session_state.persistence_ready:
        st.error(
            "A camada de persistência não está disponível nesta sessão."
        )
        if st.session_state.persistence_error:
            st.caption(st.session_state.persistence_error)

    elif not st.session_state.career_user_id:
        st.info("Nenhum usuário persistente foi inicializado.")

    else:
        try:
            metrics = get_career_dashboard_metrics(
                st.session_state.career_user_id
            )
            applications = get_application_pipeline(
                st.session_state.career_user_id
            )
            analyses_history = get_analysis_history(
                st.session_state.career_user_id,
                limit=100,
            )
            opportunity_history = get_opportunity_history(
                st.session_state.career_user_id,
                limit=100,
            )

            real_analyses_for_gaps = [
                item
                for item in analyses_history
                if item.get("company") != "CareerCompass Test Company"
            ]
            gap_report = analyze_career_gaps(real_analyses_for_gaps)

            m1, m2, m3, m4 = st.columns(4)

            with m1:
                st.metric(
                    "Análises",
                    metrics.get("total_analyses", 0),
                )

            with m2:
                st.metric(
                    "Candidaturas",
                    metrics.get("total_applications", 0),
                )

            with m3:
                st.metric(
                    "Entrevistas",
                    metrics.get("interviews", 0),
                )

            with m4:
                st.metric(
                    "Conversão em entrevista",
                    f"{metrics.get('interview_conversion', 0)}%",
                )

            st.markdown("### Pipeline")

            visible_applications = [
                item
                for item in applications
                if item.get("company") != "CareerCompass Test Company"
            ]

            if not visible_applications:
                st.info(
                    "Nenhuma candidatura real registrada ainda. "
                    "Analise uma oportunidade no Career Fit e use "
                    "'Adicionar às candidaturas'."
                )

            status_labels = {
                "planned": "Planejada",
                "applied": "Candidatado",
                "interview": "Entrevista",
                "offer": "Oferta",
                "rejected": "Não avançou",
                "withdrawn": "Retirada",
            }

            status_options = list(status_labels.keys())

            for application in visible_applications:
                application_id = application["id"]
                current_status = application.get("status", "planned")

                with st.container(border=True):
                    left, middle, right = st.columns(
                        [2.2, 1.1, 1],
                        gap="medium",
                    )

                    with left:
                        st.markdown(
                            f"### {application.get('job_title') or 'Oportunidade'}"
                        )
                        st.caption(
                            application.get("company")
                            or "Empresa não informada"
                        )

                        created_at = application.get("created_at")
                        if created_at:
                            st.write(
                                f"**Registrada em:** {created_at[:10]}"
                            )

                    with middle:
                        selected_status = st.selectbox(
                            "Status",
                            options=status_options,
                            index=(
                                status_options.index(current_status)
                                if current_status in status_options
                                else 0
                            ),
                            format_func=lambda value: status_labels[value],
                            key=f"application_status_{application_id}",
                        )

                    with right:
                        st.write("")
                        st.write("")
                        if st.button(
                            "Atualizar",
                            key=f"update_application_{application_id}",
                            use_container_width=True,
                        ):
                            try:
                                change_application_status(
                                    application_id=application_id,
                                    status=selected_status,
                                )
                                st.session_state.persistence_error = None
                                st.rerun()
                            except Exception as exc:
                                st.session_state.persistence_error = str(exc)

            st.markdown("### Career Gap Intelligence")

            g1, g2, g3 = st.columns(3)
            with g1:
                st.metric("Gaps identificados", len(gap_report.recurrent_gaps))
            with g2:
                top_gap = gap_report.recurrent_gaps[0].gap if gap_report.recurrent_gaps else "—"
                st.metric("Gap prioritário", top_gap)
            with g3:
                st.metric("Confiança histórica", f"{gap_report.confidence_score}%")

            st.caption(gap_report.summary)

            if gap_report.recurrent_gaps:
                for gap in gap_report.recurrent_gaps[:5]:
                    with st.container(border=True):
                        gc1, gc2, gc3 = st.columns([2, 1, 1])
                        with gc1:
                            st.write(f"**{gap.gap}**")
                            st.caption(gap.recommendation)
                        with gc2:
                            st.metric("Recorrência", f"{gap.occurrence_rate}%")
                        with gc3:
                            st.metric("Prioridade", gap.priority)
            else:
                st.info("Analise mais oportunidades para formar inteligência longitudinal de gaps.")

            st.markdown("### Career Intelligence histórico")

            h1, h2, h3 = st.columns(3)

            with h1:
                st.metric(
                    "Career Fit médio",
                    f"{metrics.get('avg_career_fit', 0)}%",
                )

            with h2:
                st.metric(
                    "ATS médio",
                    f"{metrics.get('avg_ats_score', 0)}%",
                )

            with h3:
                st.metric(
                    "Melhor Career Fit",
                    f"{metrics.get('best_career_fit', 0)}%",
                )

            with st.expander(
                "Ver histórico de análises",
                expanded=False,
            ):
                real_analyses = [
                    item
                    for item in analyses_history
                    if item.get("company") != "CareerCompass Test Company"
                ]

                if real_analyses:
                    for item in real_analyses:
                        st.write(
                            f"**{item.get('job_title') or 'Oportunidade'}** "
                            f"· Career Fit {item.get('career_fit_score') or 0}% "
                            f"· ATS {item.get('ats_score') or 0}% "
                            f"· Tailoring {item.get('tailoring_score') or 0}%"
                        )
                else:
                    st.caption("Nenhuma análise real persistida ainda.")

            with st.expander(
                "Ver oportunidades registradas",
                expanded=False,
            ):
                real_opportunities = [
                    item
                    for item in opportunity_history
                    if item.get("company") != "CareerCompass Test Company"
                ]

                if real_opportunities:
                    for item in real_opportunities:
                        st.write(
                            f"**{item.get('job_title') or 'Oportunidade'}** "
                            f"· {item.get('status') or 'analyzed'}"
                        )
                else:
                    st.caption("Nenhuma oportunidade real persistida ainda.")

        except Exception as exc:
            st.session_state.persistence_error = str(exc)
            st.error(
                "Não foi possível carregar o histórico persistente."
            )
            st.caption(str(exc))


# =========================================================
# COACH
# =========================================================

elif st.session_state.selected_flow == "coach":

    st.markdown(
        """<div class="cc-module-header">
<div class="cc-agent-label">Coach 2.0</div>
<h2>Interview Coach</h2>
<p>Pratique sua narrativa profissional com perguntas contextualizadas pela oportunidade, pelas forças e pelos gaps identificados.</p>
</div>""",
        unsafe_allow_html=True,
    )

    ats_report = st.session_state.ats_report
    tailoring_report = st.session_state.tailoring_report
    analyzed_job_title = st.session_state.analyzed_job_title

    if st.session_state.resume_text:
        st.success(
            f"Contexto profissional: {st.session_state.resume_name}"
        )

    if ats_report and tailoring_report:

        st.success(
            f"Entrevista contextualizada para: "
            f"{analyzed_job_title or 'oportunidade analisada'}"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "ATS Score",
                f"{ats_report.score}%",
            )

        with c2:
            st.metric(
                "Obrigatórios",
                f"{ats_report.mandatory_coverage}%",
            )

        with c3:
            st.metric(
                "Tailoring",
                f"{tailoring_report.tailoring_score}%",
            )

    else:

        st.info(
            "Nenhuma oportunidade foi analisada nesta sessão. "
            "O Coach funcionará no modo geral. Para perguntas "
            "contextualizadas, execute primeiro a Análise de Fit."
        )

    with st.expander(
        "Ver contexto profissional da entrevista"
    ):

        st.write(
            f"**Candidato:** "
            f"{structured_profile.candidate_name}"
        )

        st.write(
            f"**Senioridade:** "
            f"{structured_profile.seniority}"
        )

        st.write(
            f"**Áreas de atuação:** "
            f"{format_items(structured_profile.areas)}"
        )

        st.write(
            f"**Competências:** "
            f"{format_items(structured_profile.hard_skills)}"
        )

        st.write(
            f"**Gestão:** "
            f"{format_items(structured_profile.management_skills)}"
        )

        if ats_report:

            st.write(
                f"**Forças para a oportunidade:** "
                f"{format_items(ats_report.strengths)}"
            )

            st.write(
                f"**Gaps obrigatórios:** "
                f"{format_items(ats_report.mandatory_gaps)}"
            )

    step_number = st.session_state.coach_step

    step = get_step(
        step_number,
        job_title=analyzed_job_title,
        ats_report=ats_report,
        tailoring_report=tailoring_report,
    )

    progress_col, status_col = st.columns(
        [3, 1]
    )

    with progress_col:
        st.progress(
            step_number / 6
        )

    with status_col:
        st.caption(
            f"Etapa {step_number} de 6"
        )

    with st.container(
        border=True
    ):

        st.markdown(
            f"### {step.title}"
        )

        st.write(
            step.question
        )

        if step.objective:
            st.caption(
                f"Objetivo da etapa: {step.objective}"
            )

        if step.target_skills:
            st.info(
                "Competências prioritárias nesta pergunta: "
                + ", ".join(step.target_skills)
            )

        current_answer = st.text_area(
            "Sua resposta",
            key=f"coach_answer_{step_number}",
            height=220,
            placeholder=(
                "Responda como se estivesse em uma entrevista real. "
                "Use contexto, responsabilidade, ação e resultado. "
                "Sempre que possível, inclua evidências mensuráveis."
            ),
        )

        col_evaluate, col_reset = st.columns(
            [2, 1]
        )

        with col_evaluate:

            evaluate = st.button(
                "Avaliar resposta",
                type="primary",
                use_container_width=True,
            )

        with col_reset:

            if st.button(
                "Reiniciar simulação",
                use_container_width=True,
            ):

                reset_coach()
                st.rerun()

        if evaluate:

            if not current_answer.strip():

                st.warning(
                    "Digite sua resposta antes de solicitar a avaliação."
                )

            else:

                feedback = evaluate_answer(
                    current_answer,
                    target_skills=step.target_skills,
                    step_number=step_number,
                )

                st.session_state.coach_answers[
                    step_number
                ] = current_answer

                st.session_state.coach_feedback[
                    step_number
                ] = feedback

    feedback = st.session_state.coach_feedback.get(
        step_number
    )

    if feedback:

        st.markdown(
            "### Feedback do Coach"
        )

        metric1, metric2, metric3, metric4 = st.columns(4)

        with metric1:
            st.metric(
                "Score",
                f"{feedback['score']}%",
            )

        with metric2:
            st.metric(
                "Performance",
                feedback["performance"],
            )

        with metric3:
            st.metric(
                "STAR",
                f"{feedback['star_score']}%",
            )

        with metric4:
            st.metric(
                "Palavras",
                feedback["word_count"],
            )

        with st.container(
            border=True
        ):

            st.success(
                f"**Clareza:** {feedback['clarity']}"
            )

            st.markdown(
                f"**Evidências identificadas**  \n"
                f"{feedback['evidence']}"
            )

            if feedback["target_skills"]:

                if feedback["skills_mentioned"]:
                    st.success(
                        "**Competências conectadas à resposta:** "
                        + ", ".join(
                            feedback["skills_mentioned"]
                        )
                    )
                else:
                    st.warning(
                        "A resposta ainda não conecta explicitamente "
                        "as competências prioritárias desta etapa."
                    )

            star = feedback["star"]

            star1, star2, star3, star4 = st.columns(4)

            with star1:
                st.write(
                    "✓ Contexto"
                    if star["situation"]
                    else "○ Contexto"
                )

            with star2:
                st.write(
                    "✓ Responsabilidade"
                    if star["task"]
                    else "○ Responsabilidade"
                )

            with star3:
                st.write(
                    "✓ Ação"
                    if star["action"]
                    else "○ Ação"
                )

            with star4:
                st.write(
                    "✓ Resultado"
                    if star["result"]
                    else "○ Resultado"
                )

            st.info(
                f"**Recomendação do Coach:** "
                f"{feedback['recommendation']}"
            )

        if step_number < 6:

            if st.button(
                "Continuar para próxima etapa →",
                type="primary",
                use_container_width=True,
            ):

                st.session_state.coach_step += 1
                st.rerun()

        else:

            st.success(
                "Simulação concluída."
            )

            with st.container(
                border=True
            ):

                st.markdown(
                    "### Resultado da simulação"
                )

                completed = len(
                    st.session_state.coach_answers
                )

                scores = [
                    item.get("score", 0)
                    for item in st.session_state.coach_feedback.values()
                ]

                average_score = (
                    round(
                        sum(scores) / len(scores)
                    )
                    if scores
                    else 0
                )

                result1, result2 = st.columns(2)

                with result1:
                    st.metric(
                        "Etapas concluídas",
                        f"{completed}/6",
                    )

                with result2:
                    st.metric(
                        "Score médio",
                        f"{average_score}%",
                    )

                if st.button(
                    "Iniciar nova entrevista",
                    use_container_width=True,
                ):

                    reset_coach()
                    st.rerun()


# =========================================================
# RELATÓRIO PROFISSIONAL
# =========================================================

elif st.session_state.selected_flow == "report":

    st.markdown(
        """
        <div class="cc-module-header">
            <div class="cc-agent-label">Career Assessment</div>
            <h2>Career Report</h2>
            <p>
                Consolide as principais informações identificadas no currículo
                e nas análises realizadas pelo CareerCompass AI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.resume_text:
        st.success(
            f"Fonte ativa: {st.session_state.resume_name}"
        )
    else:
        st.info(
            "O relatório será gerado a partir do perfil profissional padrão."
        )

    st.markdown(
        "### Identificação do candidato"
    )

    st.caption(
        "O CareerCompass sugere o nome identificado no currículo. "
        "Revise ou edite antes de gerar o relatório."
    )

    candidate_name = st.text_input(
        "Nome do candidato",
        key="candidate_name_input",
    )

    if (
        structured_profile.candidate_name
        and structured_profile.candidate_name != "Candidato"
    ):

        st.caption(
            f"Nome detectado automaticamente: "
            f"{structured_profile.candidate_name}"
        )

    if st.session_state.scout_results:

        st.success(
            "Resultados do Radar de Oportunidades disponíveis "
            "para inclusão no relatório."
        )

    else:

        st.info(
            "O Radar de Oportunidades ainda não foi executado nesta sessão. "
            "O relatório pode ser gerado mesmo assim."
        )

    generate_report = st.button(
        "Gerar relatório profissional",
        type="primary",
        use_container_width=True,
    )

    if generate_report:

        source_name = (
            st.session_state.resume_name
            if st.session_state.resume_name
            else "Perfil profissional padrão"
        )

        report = build_career_report(
            structured_profile=structured_profile,
            candidate_name=(
                candidate_name.strip()
                if candidate_name.strip()
                else None
            ),
            source_name=source_name,
            scout_results=st.session_state.scout_results,
        )

        st.session_state.career_report = report

        try:

            st.session_state.career_report_pdf = (
                build_career_report_pdf(
                    report
                )
            )

        except Exception as exc:

            st.session_state.career_report_pdf = None

            st.error(
                "O relatório foi gerado, mas ocorreu um erro "
                "durante a criação do PDF."
            )

            st.caption(
                f"Detalhe técnico: {exc}"
            )

    report = st.session_state.career_report

    if report:

        st.markdown(
            "## Career Assessment Report"
        )

        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric(
                "Senioridade",
                report.seniority,
            )

        with m2:
            st.metric(
                "Áreas identificadas",
                len(report.areas),
            )

        with m3:
            st.metric(
                "Caminhos sugeridos",
                len(report.recommended_roles),
            )

        with st.container(
            border=True
        ):

            st.markdown(
                "### Resumo do candidato"
            )

            st.write(
                f"**Candidato:** {report.candidate_name}"
            )

            st.write(
                f"**Fonte analisada:** {report.source_name}"
            )

            st.write(
                f"**Data da análise:** {report.generated_at}"
            )

            st.write(
                f"**Senioridade identificada:** {report.seniority}"
            )

        st.markdown(
            "### Resumo executivo"
        )

        st.markdown(
            f"""<div class="cc-summary">
{report.executive_summary}
</div>""",
            unsafe_allow_html=True,
        )

        st.markdown("")

        left, right = st.columns(2)

        with left:

            with st.container(
                border=True
            ):

                st.markdown(
                    "### Principais competências"
                )

                st.markdown(
                    "**Áreas**"
                )

                st.write(
                    format_items(
                        report.areas
                    )
                )

                st.markdown(
                    "**Hard Skills**"
                )

                st.write(
                    format_items(
                        report.hard_skills
                    )
                )

                st.markdown(
                    "**Ferramentas**"
                )

                st.write(
                    format_items(
                        report.tools
                    )
                )

                st.markdown(
                    "**Gestão**"
                )

                st.write(
                    format_items(
                        report.management_skills
                    )
                )

        with right:

            with st.container(
                border=True
            ):

                st.markdown(
                    "### Diagnóstico"
                )

                st.markdown(
                    "**Principais forças**"
                )

                for item in report.strengths:

                    st.success(
                        item
                    )

                st.markdown(
                    "**Pontos de atenção**"
                )

                for item in report.attention_points:

                    st.warning(
                        item
                    )

        if report.recommended_roles:

            st.markdown(
                "### Caminhos profissionais"
            )

            for position, role in enumerate(
                report.recommended_roles,
                start=1,
            ):

                with st.container(
                    border=True
                ):

                    c1, c2 = st.columns(
                        [3, 1]
                    )

                    with c1:

                        st.markdown(
                            f"### {position}. {role['title']}"
                        )

                        st.write(
                            role["level"]
                        )

                        if role["reason"]:

                            st.caption(
                                role["reason"]
                            )

                    with c2:

                        st.metric(
                            "Aderência",
                            f"{role['score']}%",
                        )

        st.markdown(
            "### Recomendações"
        )

        with st.container(
            border=True
        ):

            for recommendation in report.recommendations:

                st.write(
                    f"• {recommendation}"
                )

        markdown_report = report_to_markdown(
            report
        )

        with st.expander(
            "Visualizar relatório completo em Markdown"
        ):

            st.markdown(
                markdown_report
            )

        st.markdown(
            "### Exportar relatório"
        )

        export_col1, export_col2 = st.columns(2)

        with export_col1:

            if st.session_state.career_report_pdf:

                filename = (
                    "career-assessment-"
                    + safe_filename(
                        report.candidate_name
                    )
                    + ".pdf"
                )

                st.download_button(
                    label="⬇ Baixar relatório em PDF",
                    data=st.session_state.career_report_pdf,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )

            else:

                st.warning(
                    "PDF ainda não disponível para este relatório."
                )

        with export_col2:

            markdown_filename = (
                "career-assessment-"
                + safe_filename(
                    report.candidate_name
                )
                + ".md"
            )

            st.download_button(
                label="⬇ Baixar relatório em Markdown",
                data=markdown_report,
                file_name=markdown_filename,
                mime="text/markdown",
                use_container_width=True,
            )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="cc-footer">
        CareerCompass AI · Career Intelligence Platform
    </div>
    """,
    unsafe_allow_html=True,
)
