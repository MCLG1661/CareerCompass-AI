from pathlib import Path

import streamlit as st

from coach_engine import evaluate_answer, get_step
from curator_engine import analyze_compatibility
from scout_engine import discover_roles


# =========================================================
# CONFIGURAÇÃO
# =========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT_DIR / "data" / "user-profile.md"
ICON_PATH = ROOT_DIR / "CareerCompass-icon.png"


def load_profile() -> str:
    if not PROFILE_PATH.exists():
        return "Perfil profissional não encontrado."

    return PROFILE_PATH.read_text(encoding="utf-8")


def reset_coach():
    st.session_state.coach_step = 1
    st.session_state.coach_answers = {}
    st.session_state.coach_feedback = {}

    for i in range(1, 7):
        key = f"coach_answer_{i}"

        if key in st.session_state:
            del st.session_state[key]


st.set_page_config(
    page_title="CareerCompass AI",
    page_icon="🧭",
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


profile = load_profile()


# =========================================================
# IDENTIDADE VISUAL
# =========================================================

st.markdown(
    """
    <style>

    /* Base */
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

    /* Sidebar */
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

    /* Tipografia */
    h1, h2, h3 {
        color: #111827;
        letter-spacing: -0.02em;
    }

    p {
        color: #4b5563;
    }

    /* Botões */
    .stButton button {
        border-radius: 10px;
        min-height: 44px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton button:hover {
        transform: translateY(-1px);
    }

    /* Inputs */
    .stTextArea textarea {
        border-radius: 12px;
        border: 1px solid #d8deea;
        background: white;
    }

    /* Métricas */
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e3e8f0;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
    }

    /* Containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border-radius: 16px;
        border-color: #e3e8f0;
        box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
    }

    /* Hero */
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

    /* Status pill */
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

    /* Card textual */
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

    /* Module header */
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

    /* Footer */
    .cc-footer {
        color: #98a2b3;
        text-align: center;
        font-size: 0.78rem;
        margin-top: 42px;
        padding-top: 20px;
        border-top: 1px solid #e8ecf2;
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

    st.markdown("---")

    st.markdown("### Perfil")

    st.success("Perfil profissional carregado")

    with st.expander("Visualizar perfil"):
        st.markdown(profile)

    st.markdown("---")

    st.caption(
        "Maestro AI coordena os módulos "
        "especializados da plataforma."
    )


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
<div class="cc-hero">
<div class="cc-eyebrow">CAREER INTELLIGENCE PLATFORM</div>
<h1>CareerCompass AI</h1>
<p>Transforme experiência profissional, competências e objetivos de carreira em decisões mais estruturadas para recolocação, desenvolvimento e processos seletivos.</p>
<div class="cc-status">● Perfil ativo</div>
</div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HOME
# =========================================================

if st.session_state.selected_flow == "home":

    st.markdown("## Seu centro de inteligência de carreira")

    st.caption(
        "Escolha o módulo mais adequado ao momento da sua jornada profissional."
    )

    col1, col2, col3 = st.columns(3)

    # Scout
    with col1:

        with st.container(border=True):

            st.markdown(
                """
                <div class="cc-agent-label">Scout</div>
                <div class="cc-card-title">
                    🔎 Radar de Oportunidades
                </div>
                <div class="cc-card-text">
                    Descubra funções e caminhos profissionais com maior
                    aderência às competências do seu perfil.
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

    # Curator
    with col2:

        with st.container(border=True):

            st.markdown(
                """
                <div class="cc-agent-label">Curator</div>
                <div class="cc-card-title">
                    🎯 Análise de Fit Profissional
                </div>
                <div class="cc-card-text">
                    Compare uma oportunidade específica com seu perfil
                    e identifique aderências e lacunas.
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

    # Coach
    with col3:

        with st.container(border=True):

            st.markdown(
                """
                <div class="cc-agent-label">Coach</div>
                <div class="cc-card-title">
                    🎤 Simulador de Entrevistas
                </div>
                <div class="cc-card-text">
                    Pratique respostas em uma entrevista estruturada
                    e receba feedback sobre sua comunicação.
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

    st.markdown("")

    st.markdown("### Visão da jornada")

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric(
            "Módulos ativos",
            "3",
        )

    with metric2:
        st.metric(
            "Perfil",
            "Pronto",
        )

    with metric3:
        st.metric(
            "Entrevista",
            "6 etapas",
        )

    with metric4:
        st.metric(
            "Status",
            "MVP v0.2",
        )

    st.markdown("")

    with st.container(border=True):

        st.markdown("### Como o CareerCompass AI trabalha")

        process1, process2, process3 = st.columns(3)

        with process1:
            st.markdown("**1. Compreende**")
            st.write(
                "O perfil profissional funciona como base "
                "de contexto para as análises."
            )

        with process2:
            st.markdown("**2. Analisa**")
            st.write(
                "Cada módulo especializado processa uma "
                "necessidade diferente da jornada."
            )

        with process3:
            st.markdown("**3. Orienta**")
            st.write(
                "Os resultados são transformados em informações "
                "práticas para apoiar decisões."
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
                às competências e conhecimentos registrados no seu perfil.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_intro, col_action = st.columns([2.2, 1])

    with col_intro:

        st.markdown("### Descubra onde seu perfil pode gerar valor")

        st.write(
            "O Scout analisa as competências presentes no perfil "
            "e cria um ranking inicial de caminhos profissionais."
        )

    with col_action:

        map_roles = st.button(
            "Mapear oportunidades",
            type="primary",
            use_container_width=True,
        )

    if map_roles:

        results = discover_roles(profile)

        if results:

            st.markdown("### Ranking de aderência")

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

                with st.container(border=True):

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
                Compare seu perfil com os requisitos de uma oportunidade
                e obtenha uma leitura objetiva de aderências e gaps.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.55, 1])

    with left:

        with st.container(border=True):

            st.markdown("### Oportunidade")

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

        with st.container(border=True):

            st.markdown("### O que será analisado")

            st.markdown(
                """
                **Competências técnicas**
                Ferramentas, conhecimentos e tecnologias.

                **Aderência profissional**
                Correspondência entre perfil e função.

                **Pontos sem evidência**
                Requisitos da vaga ainda não demonstrados no perfil.

                **Compatibilidade geral**
                Indicador resumido para apoiar a decisão de candidatura.
                """
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

            st.markdown("### Diagnóstico")

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

                with st.container(border=True):

                    st.markdown("### ✓ Aderências")

                    if result["strengths"]:

                        for skill in result["strengths"]:
                            st.success(skill)

                    else:

                        st.info(
                            "Nenhuma aderência técnica foi "
                            "identificada nos termos analisados."
                        )

            with col_gaps:

                with st.container(border=True):

                    st.markdown("### ⚠ Pontos sem evidência")

                    if result["gaps"]:

                        for skill in result["gaps"]:
                            st.warning(skill)

                    else:

                        st.success(
                            "Nenhuma lacuna identificada nas "
                            "competências analisadas."
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

    step_number = st.session_state.coach_step
    step = get_step(step_number)

    progress_col, status_col = st.columns([3, 1])

    with progress_col:
        st.progress(
            step_number / 6
        )

    with status_col:
        st.caption(
            f"Etapa {step_number} de 6"
        )

    with st.container(border=True):

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

        col_evaluate, col_reset = st.columns([2, 1])

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

        st.markdown("### Feedback do Coach")

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

        with st.container(border=True):

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

            with st.container(border=True):

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
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="cc-footer">
        CareerCompass AI · Career Intelligence Platform · MVP v0.2
    </div>
    """,
    unsafe_allow_html=True,
)
