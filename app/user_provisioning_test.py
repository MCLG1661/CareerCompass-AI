"""
CareerCompass AI
Sprint 4.4 — Authenticated User Provisioning Test
"""

from __future__ import annotations

import streamlit as st

from auth_engine import sign_in_with_password, sign_out
from persistence_service import (
    build_career_snapshot,
    ensure_user,
    get_storage_backend,
    initialize_persistence,
)

st.set_page_config(
    page_title="CareerCompass AI — Sprint 4.4 Test",
    page_icon="🧭",
    layout="centered",
)

SESSION_KEY = "sprint44_auth_session"

st.title("🧭 CareerCompass AI — Sprint 4.4")
st.caption("Provisionamento seguro de novo usuário autenticado")

try:
    initialize_persistence()
    backend = get_storage_backend()
except Exception as exc:
    st.error("Não foi possível inicializar a persistência.")
    st.exception(exc)
    st.stop()

if backend != "supabase":
    st.error(f"Este teste exige Supabase. Backend atual: {backend}")
    st.stop()

st.success("Backend Supabase ativo.")

session = st.session_state.get(SESSION_KEY)

if session is None:
    with st.form("sprint44_login"):
        email = st.text_input("E-mail da NOVA conta de teste")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button(
            "Entrar e provisionar usuário",
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

st.subheader("1. Identidade autenticada")
st.write(f"**Auth UID:** `{auth_user.id}`")
st.write(f"**E-mail:** {auth_user.email or '—'}")
st.write(f"**Nome:** {auth_name or '—'}")

try:
    first_user_id = ensure_user(
        name=auth_name,
        email=auth_user.email,
        auth_user_id=auth_user.id,
    )
    second_user_id = ensure_user(
        name=auth_name,
        email=auth_user.email,
        auth_user_id=auth_user.id,
    )
except Exception as exc:
    st.error("Falha ao provisionar o usuário CareerCompass.")
    st.exception(exc)
    st.stop()

st.subheader("2. Provisionamento")
st.write(f"**Primeira resolução:** `{first_user_id}`")
st.write(f"**Segunda resolução:** `{second_user_id}`")

idempotent = first_user_id == second_user_id
if idempotent:
    st.success("Idempotência validada: o mesmo Auth UID retorna o mesmo usuário.")
else:
    st.error("Falha: o mesmo Auth UID gerou usuários diferentes.")
    st.stop()

try:
    snapshot = build_career_snapshot(first_user_id)
except Exception as exc:
    st.error("Usuário criado, mas o snapshot não pôde ser carregado.")
    st.exception(exc)
    st.stop()

profiles = snapshot.get("profiles") or []
analyses = snapshot.get("recent_analyses") or []
applications = snapshot.get("applications") or []

st.subheader("3. Isolamento inicial")
c1, c2, c3 = st.columns(3)
c1.metric("Perfis", len(profiles))
c2.metric("Análises", len(analyses))
c3.metric("Candidaturas", len(applications))

fresh = len(profiles) == 0 and len(analyses) == 0 and len(applications) == 0

if idempotent and fresh:
    st.success(
        "SPRINT 4.4 VALIDADO: nova identidade autenticada recebeu um "
        "CareerCompass user próprio, estável e sem herdar dados de outro usuário."
    )
elif idempotent:
    st.warning(
        "O mapeamento é estável, mas esta conta já possui dados. "
        "Use uma conta Auth realmente nova para validar o provisionamento inicial."
    )

if st.button("Sair do teste"):
    try:
        sign_out(session.access_token)
    except Exception:
        pass
    st.session_state.pop(SESSION_KEY, None)
    st.rerun()
