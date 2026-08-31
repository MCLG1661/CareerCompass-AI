from pathlib import Path

import streamlit as st

from coach_engine import evaluate_answer, get_step
from curator_engine import analyze_compatibility
from scout_engine import discover_roles


ROOT_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT_DIR / "data" / "user-profile.md"


def load_profile() -> str:
    if not PROFILE_PATH.exists():
        return "Perfil profissional não encontrado."

    return PROFILE_PATH.read_text(encoding="utf-8")


st.set_page_config(
    page_title="CareerCompass AI",
    page_icon="🧭",
    layout="wide",
)


if "selected_flow" not in st.session_state:
    st.session_state.selected_flow = None

if "coach_step" not in st.session_state:
    st.session_state.coach_step = 1

if "coach_answers" not in st.session_state:
    st.session_state.coach_answers = {}

if "coach_feedback" not in st.session_state:
    st.session_state.coach_feedback = {}


profile = load_profile()


# =========================================================
# CABEÇALHO
# =========================================================

st.title("🧭 CareerCompass AI")
st.caption(
    "Assistente multiagente para carreira, vagas e preparação profissional."
)

st.divider()


# =========================================================
# PERFIL + MENU
# =========================================================

col_profile, col_actions = st.columns([1, 1.3])


with col_profile:
    st.subheader("Perfil profissional")

    with st.expander(
        "Visualizar perfil carregado",
        expanded=False,
    ):
        st.markdown(profile)


with col_actions:
    st.subheader("Como posso ajudar?")

    if st.button(
        "🔎 Scout — Descobrir oportunidades",
        use_container_width=True,
    ):
        st.session_state.selected_flow = "scout"

    if st.button(
        "🎯 Curator — Analisar compatibilidade",
        use_container_width=True,
    ):
        st.session_state.selected_flow = "curator"

    if st.button(
        "🎤 Coach — Simular entrevista",
        use_container_width=True,
    ):
        st.session_state.selected_flow = "coach"


st.divider()


# =========================================================
# SCOUT
# =========================================================

if st.session_state.selected_flow == "scout":

    st.header("🔎 Scout — Descubra seus melhores caminhos")
    st.caption(
        "Analiso seu perfil para identificar funções "
        "profissionais com maior aderência."
    )

    st.info(
        "O Scout utiliza as competências registradas no seu "
        "perfil para ranquear funções compatíveis."
    )

    if st.button(
        "Mapear oportunidades",
        type="primary",
    ):

        results = discover_roles(profile)

        st.subheader("Ranking de aderência")

        for position, result in enumerate(
            results,
            start=1,
        ):

            st.markdown(
                f"### {position}. {result.title}"
            )

            col1, col2 = st.columns([1, 2])

            with col1:
                st.metric(
                    "Aderência",
                    f"{result.score}%",
                )

            with col2:
                st.write(
                    f"**Classificação:** {result.level}"
                )

                st.write(result.reason)

            st.progress(
                result.score / 100
            )

            st.divider()


# =========================================================
# CURATOR
# =========================================================

elif st.session_state.selected_flow == "curator":

    st.header("🎯 Curator — Avalie sua aderência")
    st.caption(
        "Compare seu perfil com uma oportunidade específica."
    )

    job_description = st.text_area(
        "Cole a descrição da vaga",
        height=260,
        placeholder=(
            "Inclua cargo, responsabilidades, requisitos obrigatórios, "
            "diferenciais, localização e modelo de trabalho."
        ),
    )

    if st.button(
        "Analisar vaga",
        type="primary",
    ):

        if not job_description.strip():

            st.warning(
                "Cole a descrição da vaga antes de iniciar a análise."
            )

        else:

            result = analyze_compatibility(
                profile=profile,
                job_description=job_description,
            )

            st.subheader("Resultado da análise")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Compatibilidade",
                    f"{result['score']}%",
                )

            with col2:
                st.metric(
                    "Classificação",
                    result["compatibility"],
                )

            st.subheader("Aderências identificadas")

            if result["strengths"]:

                for skill in result["strengths"]:
                    st.success(f"✓ {skill}")

            else:

                st.info(
                    "Nenhuma aderência técnica foi identificada "
                    "com base nos termos analisados."
                )

            st.subheader(
                "Pontos sem evidência no perfil"
            )

            if result["gaps"]:

                for skill in result["gaps"]:
                    st.warning(f"⚠ {skill}")

            else:

                st.success(
                    "Nenhuma lacuna foi identificada entre "
                    "as competências detectadas na vaga."
                )

            with st.expander(
                "Detalhamento técnico"
            ):

                for item in result["matches"]:

                    st.write(
                        f"**{item.skill}:** {item.status}"
                    )


# =========================================================
# COACH
# =========================================================

elif st.session_state.selected_flow == "coach":

    st.header("🎤 Coach — Prepare-se para entrevistas")
    st.caption(
        "Pratique respostas em seis etapas e receba feedback estruturado."
    )

    step_number = st.session_state.coach_step
    step = get_step(step_number)

    st.progress(
        step_number / 6
    )

    st.subheader(
        f"Etapa {step.number} de 6 — {step.title}"
    )

    st.write(step.question)

    current_answer = st.text_area(
        "Sua resposta",
        key=f"coach_answer_{step_number}",
        height=180,
        placeholder="Digite sua resposta como se estivesse em uma entrevista real.",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Avaliar resposta",
            type="primary",
            use_container_width=True,
        ):

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

        st.subheader("Feedback do Coach")

        st.success(
            f"**Clareza:** {feedback['clarity']}"
        )

        st.write(
            f"**Evidências:** {feedback['evidence']}"
        )

        st.info(
            f"**Recomendação:** {feedback['recommendation']}"
        )

        st.caption(
            f"Palavras na resposta: {feedback['word_count']}"
        )

        if step_number < 6:

            if st.button(
                "Próxima etapa →",
                use_container_width=True,
            ):

                st.session_state.coach_step += 1
                st.rerun()

        else:

            st.success(
                "Entrevista concluída."
            )

            st.subheader(
                "Resumo da simulação"
            )

            completed = len(
                st.session_state.coach_answers
            )

            st.metric(
                "Etapas concluídas",
                f"{completed}/6",
            )

            if st.button(
                "Reiniciar entrevista",
                use_container_width=True,
            ):

                st.session_state.coach_step = 1
                st.session_state.coach_answers = {}
                st.session_state.coach_feedback = {}

                for i in range(1, 7):
                    key = f"coach_answer_{i}"

                    if key in st.session_state:
                        del st.session_state[key]

                st.rerun()

    with col2:

        if st.button(
            "Reiniciar simulação",
            use_container_width=True,
        ):

            st.session_state.coach_step = 1
            st.session_state.coach_answers = {}
            st.session_state.coach_feedback = {}

            for i in range(1, 7):
                key = f"coach_answer_{i}"

                if key in st.session_state:
                    del st.session_state[key]

            st.rerun()


# =========================================================
# ESTADO INICIAL
# =========================================================

else:

    st.info(
        "Escolha Scout, Curator ou Coach para começar."
    )
