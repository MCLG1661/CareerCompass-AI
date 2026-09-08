"""
CareerCompass AI
Sprint 5.1D — Career Direction Persistence Isolated Test

Validates:
- Supabase Auth login.
- JWT binding to persistence.
- CareerCompass user resolution.
- Creation of a Career Direction.
- Retrieval of the active Career Direction.
- Retrieval of Career Direction history.
- RLS-scoped access for the authenticated user.

This test creates one controlled Career Direction record for the signed-in user.
"""

from __future__ import annotations

import streamlit as st

from auth_engine import sign_in_with_password
from persistence_service import (
    bind_authenticated_session,
    clear_authenticated_session,
    ensure_user,
    get_career_direction_history,
    get_storage_backend,
    get_user_active_career_direction,
    persist_career_direction,
)


st.set_page_config(
    page_title="CareerCompass AI — Sprint 5.1D",
    page_icon="🧭",
    layout="centered",
)

SESSION_KEY = "sprint51d_auth_session"
RESULT_KEY = "sprint51d_result"


def _auth_name(auth_user) -> str | None:
    metadata = getattr(auth_user, "user_metadata", None) or {}
    return (
        str(metadata.get("full_name") or "").strip()
        or str(metadata.get("name") or "").strip()
        or str(metadata.get("display_name") or "").strip()
        or None
    )


def _reset_test() -> None:
    try:
        clear_authenticated_session()
    except Exception:
        pass
    st.session_state.pop(SESSION_KEY, None)
    st.session_state.pop(RESULT_KEY, None)


st.title("🧭 CareerCompass AI — Sprint 5.1D")
st.caption("Teste isolado de persistência da Career Direction")

backend = get_storage_backend()
if backend != "supabase":
    st.error(f"Este teste exige Supabase. Backend atual: {backend}")
    st.stop()

session = st.session_state.get(SESSION_KEY)

if session is None:
    st.info(
        "Faça login para criar uma Career Direction de teste no seu próprio usuário."
    )

    with st.form("sprint51d_login"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button(
            "Entrar e testar Career Direction",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not email.strip() or not password:
            st.warning("Informe e-mail e senha.")
            st.stop()

        try:
            session = sign_in_with_password(email.strip(), password)
            st.session_state[SESSION_KEY] = session
            st.session_state.pop(RESULT_KEY, None)
            st.rerun()
        except Exception as exc:
            st.error("Falha no login.")
            st.exception(exc)

    st.stop()

auth_user = session.user

try:
    bind_authenticated_session(session.access_token)
except Exception as exc:
    st.error("Falha ao vincular JWT à persistência.")
    st.exception(exc)
    st.stop()

try:
    app_user_id = ensure_user(
        name=_auth_name(auth_user),
        email=auth_user.email,
        auth_user_id=auth_user.id,
    )
except Exception as exc:
    st.error("Falha ao resolver o usuário CareerCompass.")
    st.exception(exc)
    st.stop()

st.success("Login e identidade CareerCompass resolvidos.")
st.write(f"**Conta:** {auth_user.email or 'Conta Supabase'}")

if not st.session_state.get(RESULT_KEY):
    st.warning(
        "O teste criará uma Career Direction controlada e a marcará como ativa."
    )

    if st.button(
        "Criar Career Direction de teste",
        type="primary",
        use_container_width=True,
    ):
        try:
            direction_id = persist_career_direction(
                app_user_id,
                target_roles=[
                    "Head de Data & AI",
                    "Gerente de Transformação Digital",
                ],
                target_seniority="Executiva / Liderança",
                target_areas=[
                    "Dados",
                    "Inteligência Artificial",
                    "Transformação Digital",
                ],
                target_industries=[
                    "Tecnologia",
                    "Serviços",
                ],
                work_modes=[
                    "Híbrido",
                    "Remoto",
                ],
                target_locations=[
                    "Rio de Janeiro",
                    "São Paulo",
                    "Portugal",
                ],
                relocation_available=True,
                salary_min=22000,
                salary_currency="BRL",
                time_horizon_months=24,
                priorities={
                    "growth": 5,
                    "leadership": 5,
                    "learning": 4,
                    "compensation": 4,
                },
                constraints={
                    "avoid_roles_below_seniority": True,
                },
                career_goal=(
                    "Consolidar uma posição de liderança na interseção entre "
                    "gestão, dados, IA e transformação digital."
                ),
                make_active=True,
            )

            active = get_user_active_career_direction(app_user_id)
            history = get_career_direction_history(app_user_id, limit=20)

            if not active:
                raise RuntimeError(
                    "A Career Direction foi criada, mas nenhuma direção ativa foi retornada."
                )

            if str(active.get("id")) != str(direction_id):
                raise RuntimeError(
                    "A Career Direction ativa não corresponde ao registro recém-criado."
                )

            st.session_state[RESULT_KEY] = {
                "direction_id": direction_id,
                "active": active,
                "history_count": len(history),
            }
            st.rerun()

        except Exception as exc:
            st.error("Falha ao persistir ou recuperar a Career Direction.")
            st.exception(exc)

    if st.button("Cancelar teste", use_container_width=True):
        _reset_test()
        st.rerun()

    st.stop()

result = st.session_state[RESULT_KEY]
active = result["active"]

st.success(
    "SPRINT 5.1D VALIDADO: Career Direction criada, recuperada como ativa "
    "e listada no histórico sob JWT + RLS."
)

c1, c2 = st.columns(2)
c1.metric("Direção ativa", "SIM")
c2.metric("Histórico", result["history_count"])

st.subheader("Career Direction ativa")
st.write(
    "**Cargos-alvo:** "
    + ", ".join(active.get("target_roles") or [])
)
st.write(
    "**Senioridade:** "
    + str(active.get("target_seniority") or "—")
)
st.write(
    "**Áreas:** "
    + ", ".join(active.get("target_areas") or [])
)
st.write(
    "**Setores:** "
    + ", ".join(active.get("target_industries") or [])
)
st.write(
    "**Modelo de trabalho:** "
    + ", ".join(active.get("work_modes") or [])
)
st.write(
    "**Localizações:** "
    + ", ".join(active.get("target_locations") or [])
)
st.write(
    f"**Remuneração mínima:** "
    f"{active.get('salary_currency') or 'BRL'} "
    f"{active.get('salary_min') or 0}"
)
st.write(
    f"**Horizonte:** "
    f"{active.get('time_horizon_months') or '—'} meses"
)
st.write(
    "**Objetivo:** "
    + str(active.get("career_goal") or "—")
)

st.caption(
    "O teste não exibe tokens. O registro foi criado no usuário autenticado "
    "e acessado através das policies RLS."
)

if st.button("Encerrar teste local", use_container_width=True):
    _reset_test()
    st.rerun()
