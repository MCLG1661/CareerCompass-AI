"""
CareerCompass AI
Sprint 4.5B — Authenticated JWT + RLS Isolated Test

Validates:
Supabase Auth -> access_token -> token-aware persistence -> PostgREST -> RLS -> own data.
"""

from __future__ import annotations

import streamlit as st

from auth_engine import sign_in_with_password, sign_out
from persistence_service import (
    bind_authenticated_session,
    build_career_snapshot,
    clear_authenticated_session,
    ensure_user,
    get_storage_backend,
    persistence_uses_authenticated_session,
)

st.set_page_config(
    page_title="CareerCompass AI — Sprint 4.5B",
    page_icon="🧭",
    layout="centered",
)

SESSION_KEY = "sprint45b_auth_session"

st.title("🧭 CareerCompass AI — Sprint 4.5B")
st.caption("JWT autenticado + PostgREST + RLS")

backend = get_storage_backend()
if backend != "supabase":
    st.error(f"Este teste exige Supabase. Backend atual: {backend}")
    st.stop()

session = st.session_state.get(SESSION_KEY)

if session is None:
    with st.form("sprint45b_login"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button(
            "Entrar e testar RLS",
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
            st.rerun()
        except Exception as exc:
            st.error("Falha no login.")
            st.exception(exc)

    st.stop()

auth_user = session.user
metadata = getattr(auth_user, "user_metadata", None) or {}
auth_name = (
    metadata.get("full_name")
    or metadata.get("name")
    or metadata.get("display_name")
    or None
)

try:
    bind_authenticated_session(session.access_token)
except Exception as exc:
    st.error("Falha ao vincular o JWT à persistência.")
    st.exception(exc)
    st.stop()

st.subheader("1. Sessão")
st.write(f"**Auth UID:** `{auth_user.id}`")
st.write(f"**E-mail:** {auth_user.email or '—'}")
st.write(
    "**Persistência autenticada:** "
    + ("SIM" if persistence_uses_authenticated_session() else "NÃO")
)

if not persistence_uses_authenticated_session():
    st.error("O token não ficou vinculado ao backend.")
    st.stop()

try:
    app_user_id = ensure_user(
        name=auth_name,
        email=auth_user.email,
        auth_user_id=auth_user.id,
    )
except Exception as exc:
    st.error("RLS bloqueou ou falhou ao resolver o usuário CareerCompass.")
    st.exception(exc)
    st.stop()

st.subheader("2. Identidade CareerCompass")
st.write(f"**CareerCompass user_id:** `{app_user_id}`")

try:
    snapshot = build_career_snapshot(app_user_id)
except Exception as exc:
    st.error("Falha ao carregar os dados do usuário via JWT + RLS.")
    st.exception(exc)
    st.stop()

profiles = snapshot.get("profiles") or []
analyses = snapshot.get("recent_analyses") or []
applications = snapshot.get("applications") or []
opportunities = snapshot.get("recent_opportunities") or []
metrics = snapshot.get("metrics") or {}

st.subheader("3. Dados visíveis via RLS")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Perfis", len(profiles))
c2.metric("Oportunidades", len(opportunities))
c3.metric("Análises", len(analyses))
c4.metric("Candidaturas", len(applications))

st.write(
    f"**Total de análises nas métricas:** "
    f"{metrics.get('total_analyses', 0)}"
)

st.success(
    "SPRINT 4.5B VALIDADO: a persistência está operando com o JWT "
    "do usuário autenticado e o snapshot foi carregado através das policies RLS."
)

if st.button("Sair do teste"):
    try:
        clear_authenticated_session()
    except Exception:
        pass

    try:
        sign_out(session.access_token)
    except Exception:
        pass

    st.session_state.pop(SESSION_KEY, None)
    st.rerun()
