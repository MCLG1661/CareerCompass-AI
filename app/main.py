from pathlib import Path

import streamlit as st
from PIL import Image

from coach_engine import evaluate_answer, get_step
from curator_engine import analyze_compatibility
from pdf_engine import build_career_report_pdf
from profile_engine import build_professional_profile
from report_engine import build_career_report, report_to_markdown
from resume_parser import ResumeParserError, extract_resume_text
from scout_engine import discover_roles


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
    initial_sidebar_state="expanded",
)


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

if "scout_results" not in st.session_state:
    st.session_state.scout_results = None

if "career_report" not in st.session_state:
    st.session_state.career_report = None

if "career_report_pdf" not in st.session_state:
    st.session_state.career_report_pdf = None

if "candidate_name_input" not in st.session_state:
    st.session_state.candidate_name_input = ""


default_profile = load_default_profile()

profile = (
    st.session_state.resume_text
    if st.session_state.resume_text
    else default_profile
)


# =========================================================
# IDENTIDADE VISUAL
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at top right,
                rgba(86, 115, 255, 0.08),
                transparent 28%
            ),
            #f7f9fc;
    }

    .block-container {
        max-width: 1380px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #10172a 0%,
                #172036 55%,
                #10172a 100%
            );
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    section[data-testid="stSidebar"] * {
        color: #f5f7fb;
    }

    section[data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,0.06);
        color: #f5f7fb;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px;
        min-height: 44px;
        transition: 0.2s ease;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.12);
        border-color: rgba(255,255,255,0.22);
    }

    h1, h2, h3 {
        color: #111827;
        letter-spacing: -0.02em;
    }

    p {
        color: #4b5563;
    }

    .stButton button {
        border-radius: 10px;
        min-height: 44px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton button:hover {
        transform: translateY(-1px);
    }

    .stTextArea textarea,
    .stTextInput input {
        border-radius: 12px;
        border: 1px solid #d8deea;
        background: white;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e3e8f0;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border-radius: 16px;
        border-color: #e3e8f0;
        box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
    }

    .cc-hero {
        padding: 30px 34px;
        border-radius: 20px;
        background:
            linear-gradient(
                135deg,
                #111827 0%,
                #182747 55%,
                #304b85 100%
            );
        margin-bottom: 26px;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.18);
    }

    .cc-eyebrow {
        color: #a9bbff;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .cc-hero h1 {
        color: white;
        margin: 0;
        font-size: 2.25rem;
    }

    .cc-hero p {
        color: #d9e0ef;
        margin-top: 10px;
        margin-bottom: 0;
        max-width: 780px;
        font-size: 1.02rem;
        line-height: 1.6;
    }

    .cc-status {
        display: inline-block;
        background: #e8fff2;
        color: #087443;
        border: 1px solid #c6f3dc;
        border-radius: 999px;
        padding: 6px 11px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-top: 14px;
    }

    .cc-card-title {
        font-size: 1.08rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 6px;
    }

    .cc-card-text {
        font-size: 0.90rem;
        color: #667085;
        min-height: 46px;
        line-height: 1.5;
    }

    .cc-agent-label {
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #667085;
        margin-bottom: 10px;
    }

    .cc-module-header {
        padding: 22px 26px;
        background: white;
        border: 1px solid #e3e8f0;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
    }

    .cc-module-header h2 {
        margin: 0;
    }

    .cc-module-header p {
        margin-top: 8px;
        margin-bottom: 0;
    }

    .cc-summary {
        padding: 20px 22px;
        background: #f8faff;
        border: 1px solid #dbe4ff;
        border-radius: 14px;
        color: #344054;
        line-height: 1.7;
    }

    .cc-footer {
        color: #98a2b3;
        text-align: center;
        font-size: 0.78rem;
        margin-top: 42px;
        padding-top: 20px;
        border-top: 1px solid #e8ecf2;
    }

    section[data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] {
        background: #ffffff;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
    }

    section[data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] * {
        color: #334155 !important;
    }

    section[data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] button {
        background: #f8fafc !important;
        color: #111827 !important;
        border: 1px solid #cbd5e1 !important;
    }

    section[data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] button:hover {
        background: #eef2f7 !important;
        color: #111827 !important;
        border-color: #94a3b8 !important;
        transform: none;
    }

    section[data-testid="stSidebar"]
    [data-testid="stFileUploader"] small {
        color: #64748b !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    if ICON_PATH.exists():
        st.image(
            str(ICON_PATH),
            width=72,
        )

    st.markdown("## CareerCompass AI")
    st.caption("Career Intelligence Platform")

    st.markdown("---")

    if st.button(
        "⌂  Visão geral",
        use_container_width=True,
    ):
        st.session_state.selected_flow = "home"
        st.rerun()

    if st.button(
        "🔎  Radar de Oportunidades",
        use_container_width=True,
    ):
        st.session_state.selected_flow = "scout"
        st.rerun()

    if st.button(
        "🎯  Análise de Fit",
        use_container_width=True,
    ):
        st.session_state.selected_flow = "curator"
        st.rerun()

    if st.button(
        "🎤  Simulador de Entrevistas",
        use_container_width=True,
    ):
        st.session_state.selected_flow = "coach"
        st.rerun()

    if st.button(
        "📄  Relatório Profissional",
        use_container_width=True,
    ):
        st.session_state.selected_flow = "report"
        st.rerun()

    st.markdown("---")

    st.markdown("### Perfil")

    uploaded_resume = st.file_uploader(
        "Carregar currículo",
        type=["pdf", "docx"],
        help="Envie um currículo em PDF ou DOCX.",
    )

    if uploaded_resume is not None:
        try:
            extracted_text = extract_resume_text(
                uploaded_resume.name,
                uploaded_resume.getvalue(),
            )

            if (
                st.session_state.resume_name != uploaded_resume.name
                or st.session_state.resume_text != extracted_text
            ):
                st.session_state.resume_text = extracted_text
                st.session_state.resume_name = uploaded_resume.name
                st.session_state.scout_results = None
                st.session_state.career_report = None
                st.session_state.career_report_pdf = None
                st.session_state.candidate_name_input = ""

                reset_coach()

            profile = st.session_state.resume_text

            st.success(
                "Currículo carregado com sucesso"
            )

            st.caption(
                f"Arquivo ativo: {uploaded_resume.name}"
            )

        except ResumeParserError as exc:
            st.error(str(exc))

    if st.session_state.resume_text:

        st.info(
            "Perfil em uso: currículo enviado"
        )

        if st.button(
            "Usar perfil padrão",
            use_container_width=True,
        ):
            st.session_state.resume_text = None
            st.session_state.resume_name = None
            st.session_state.scout_results = None
            st.session_state.career_report = None
            st.session_state.career_report_pdf = None
            st.session_state.candidate_name_input = ""

            reset_coach()
            st.rerun()

    else:
        st.success(
            "Perfil padrão carregado"
        )

    with st.expander(
        "Visualizar perfil em uso"
    ):
        st.text(profile)

    st.markdown("---")

    st.caption(
        "Maestro AI coordena os módulos especializados da plataforma."
    )


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


# =========================================================
# HERO
# =========================================================

st.markdown(
    """<div class="cc-hero">
<div class="cc-eyebrow">CAREER INTELLIGENCE PLATFORM</div>
<h1>CareerCompass AI</h1>
<p>Transforme experiência profissional, competências e objetivos de carreira em decisões mais estruturadas para recolocação, desenvolvimento e processos seletivos.</p>
<div class="cc-status">● Perfil ativo</div>
</div>""",
    unsafe_allow_html=True,
)


# =========================================================
# HOME
# =========================================================

if st.session_state.selected_flow == "home":

    st.markdown(
        "## Seu centro de inteligência de carreira"
    )

    st.caption(
        "Escolha o módulo mais adequado ao momento da sua jornada profissional."
    )

    if st.session_state.resume_text:
        st.success(
            f"Currículo ativo: {st.session_state.resume_name}"
        )
    else:
        st.info(
            "A plataforma está utilizando o perfil profissional padrão."
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):

            st.markdown(
                """
                <div class="cc-agent-label">Scout</div>
                <div class="cc-card-title">🔎 Radar de Oportunidades</div>
                <div class="cc-card-text">
                    Descubra funções profissionais com maior aderência ao seu perfil.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")

            if st.button(
                "Explorar oportunidades →",
                key="home_scout",
                use_container_width=True,
                type="primary",
            ):
                st.session_state.selected_flow = "scout"
                st.rerun()

    with col2:
        with st.container(border=True):

            st.markdown(
                """
                <div class="cc-agent-label">Curator</div>
                <div class="cc-card-title">🎯 Análise de Fit</div>
                <div class="cc-card-text">
                    Compare uma vaga com seu perfil e identifique aderências e gaps.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")

            if st.button(
                "Analisar oportunidade →",
                key="home_curator",
                use_container_width=True,
            ):
                st.session_state.selected_flow = "curator"
                st.rerun()

    with col3:
        with st.container(border=True):

            st.markdown(
                """
                <div class="cc-agent-label">Coach</div>
                <div class="cc-card-title">🎤 Simulador de Entrevistas</div>
                <div class="cc-card-text">
                    Pratique respostas e receba feedback estruturado.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")

            if st.button(
                "Iniciar preparação →",
                key="home_coach",
                use_container_width=True,
            ):
                st.session_state.selected_flow = "coach"
                st.rerun()

    with col4:
        with st.container(border=True):

            st.markdown(
                """
                <div class="cc-agent-label">Assessment</div>
                <div class="cc-card-title">📄 Relatório Profissional</div>
                <div class="cc-card-text">
                    Consolide o diagnóstico do candidato em um relatório estruturado.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")

            if st.button(
                "Gerar assessment →",
                key="home_report",
                use_container_width=True,
            ):
                st.session_state.selected_flow = "report"
                st.rerun()

    st.markdown("")

    st.markdown(
        "## Diagnóstico do Perfil Profissional"
    )

    st.caption(
        "Leitura estruturada do perfil ativo realizada pelo Profile Engine."
    )

    d1, d2, d3, d4 = st.columns(4)

    with d1:
        st.metric(
            "Senioridade",
            structured_profile.seniority,
        )

    with d2:
        st.metric(
            "Áreas identificadas",
            len(structured_profile.areas),
        )

    with d3:
        st.metric(
            "Hard Skills",
            len(structured_profile.hard_skills),
        )

    with d4:
        st.metric(
            "Ferramentas",
            len(structured_profile.tools),
        )

    with st.container(border=True):

        left, right = st.columns(2)

        with left:

            st.markdown(
                "### Perfil de atuação"
            )

            st.markdown(
                "**Candidato identificado**"
            )

            st.write(
                structured_profile.candidate_name
            )

            st.markdown(
                "**Áreas profissionais**"
            )

            st.write(
                format_items(
                    structured_profile.areas
                )
            )

            st.markdown(
                "**Hard Skills**"
            )

            st.write(
                format_items(
                    structured_profile.hard_skills
                )
            )

            st.markdown(
                "**Ferramentas e tecnologias**"
            )

            st.write(
                format_items(
                    structured_profile.tools
                )
            )

        with right:

            st.markdown(
                "### Competências complementares"
            )

            st.markdown(
                "**Gestão e liderança**"
            )

            st.write(
                format_items(
                    structured_profile.management_skills
                )
            )

            st.markdown(
                "**Metodologias**"
            )

            st.write(
                format_items(
                    structured_profile.methodologies
                )
            )

            st.markdown(
                "**Idiomas identificados**"
            )

            st.write(
                format_items(
                    structured_profile.languages
                )
            )

            st.markdown(
                "**Evidências de resultados**"
            )

            st.write(
                format_items(
                    structured_profile.evidence_terms
                )
            )


# =========================================================
# SCOUT
# =========================================================

elif st.session_state.selected_flow == "scout":

    st.markdown(
        """
        <div class="cc-module-header">
            <div class="cc-agent-label">Scout</div>
            <h2>🔎 Radar de Oportunidades</h2>
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
        """
        <div class="cc-module-header">
            <div class="cc-agent-label">Curator</div>
            <h2>🎯 Análise de Fit Profissional</h2>
            <p>
                Compare o perfil ativo com os requisitos de uma oportunidade
                e obtenha uma leitura objetiva de aderências e gaps.
            </p>
        </div>
        """,
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

            job_description = st.text_area(
                "Descrição da vaga",
                height=320,
                placeholder=(
                    "Cole aqui a descrição completa da oportunidade, "
                    "incluindo responsabilidades, requisitos, diferenciais "
                    "e informações sobre a função."
                ),
                label_visibility="collapsed",
            )

            analyze = st.button(
                "Analisar compatibilidade",
                type="primary",
                use_container_width=True,
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

    if analyze:

        if not job_description.strip():

            st.warning(
                "Cole a descrição da vaga antes de iniciar a análise."
            )

        else:

            result = analyze_compatibility(
                profile=profile,
                job_description=job_description,
            )

            st.markdown(
                "### Diagnóstico"
            )

            metric1, metric2, metric3 = st.columns(3)

            with metric1:
                st.metric(
                    "Compatibilidade",
                    f"{result['score']}%",
                )

            with metric2:
                st.metric(
                    "Classificação",
                    result["compatibility"],
                )

            with metric3:
                st.metric(
                    "Competências analisadas",
                    len(result["matches"]),
                )

            st.markdown("")

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
                            "Nenhuma aderência técnica foi identificada "
                            "nos termos analisados."
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
                            "Nenhuma lacuna identificada nas competências analisadas."
                        )

            with st.expander(
                "Ver detalhamento da análise"
            ):

                for item in result["matches"]:
                    st.write(
                        f"**{item.skill}:** {item.status}"
                    )


# =========================================================
# COACH
# =========================================================

elif st.session_state.selected_flow == "coach":

    st.markdown(
        """
        <div class="cc-module-header">
            <div class="cc-agent-label">Coach</div>
            <h2>🎤 Simulador de Entrevistas</h2>
            <p>
                Pratique sua narrativa profissional em uma entrevista
                estruturada e receba feedback após cada resposta.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.resume_text:
        st.success(
            f"Contexto da entrevista: {st.session_state.resume_name}"
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

    step_number = st.session_state.coach_step
    step = get_step(
        step_number
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

        current_answer = st.text_area(
            "Sua resposta",
            key=f"coach_answer_{step_number}",
            height=220,
            placeholder=(
                "Responda como se estivesse em uma entrevista real. "
                "Procure utilizar exemplos, ações e resultados."
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
                    current_answer
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

        metric1, metric2 = st.columns(2)

        with metric1:
            st.metric(
                "Palavras",
                feedback["word_count"],
            )

        with metric2:
            st.metric(
                "Etapa",
                f"{step_number}/6",
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

                st.metric(
                    "Etapas concluídas",
                    f"{completed}/6",
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
            <h2>📄 Relatório Profissional</h2>
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
