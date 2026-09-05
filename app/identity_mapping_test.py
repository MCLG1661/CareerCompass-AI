"""
CareerCompass AI
Sprint 4.2 — Identity Mapping Isolated Test

Validates the full identity chain:

Supabase Auth login
    -> auth_user_id
    -> public.users auth_user_id mapping
    -> CareerCompass application user_id
    -> existing persisted career data

This test intentionally does not modify main.py.
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
    page_title="CareerCompass AI — Identity Mapping Test",
    page_icon="🧭",
    layout="centered",
)

SESSION_KEY = "identity_mapping_test_session"


def _safe_count(value) -> int:
    return len(value) if isinstance(value, list) else 0


st.title("🧭 CareerCompass AI — Identity Mapping Test")
st.caption("Sprint 4.2 · Auth → usuário histórico → dados persistidos")

try:
    health = initialize_persistence()
    backend = get_storage_backend()
except Exception as exc:
    st.error("Não foi possível inicializar a persistência.")
    st.exception(exc)
    st.stop()

if backend != "supabase":
    st.error(
        "Este teste precisa usar o backend Supabase. "
        "O backend atual é SQLite."
    )
    st.info(
        "Adicione SUPABASE_SECRET_KEY ao arquivo local "
        ".streamlit/secrets.toml antes de executar este teste."
    )
    st.stop()

st.success("Backend Supabase ativo.")

session = st.session_state.get(SESSION_KEY)

if session is None:
    with st.form("identity_login_form"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar e validar identidade")

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
auth_user_id = auth_user.id

user_metadata = getattr(auth_user, "user_metadata", None) or {}
auth_name = (
    user_metadata.get("full_name")
    or user_metadata.get("name")
    or user_metadata.get("display_name")
    or None
)

st.subheader("1. Supabase Auth")
st.write(f"**Auth UID:** `{auth_user_id}`")
st.write(f"**E-mail:** {auth_user.email or '—'}")
st.write(f"**Nome:** {auth_name or '—'}")

try:
    app_user_id = ensure_user(
        name=auth_name,
        email=auth_user.email,
        auth_user_id=auth_user_id,
    )
except Exception as exc:
    st.error("Falha ao resolver o usuário CareerCompass pelo auth_user_id.")
    st.exception(exc)
    st.stop()

st.subheader("2. Identity Mapping")
st.success("Identidade autenticada resolvida no CareerCompass.")
st.write(f"**CareerCompass user_id:** `{app_user_id}`")

try:
    snapshot = build_career_snapshot(app_user_id)
except Exception as exc:
    st.error("O usuário foi resolvido, mas não foi possível carregar o histórico.")
    st.exception(exc)
    st.stop()

profiles = snapshot.get("profiles") or []
opportunities = snapshot.get("recent_opportunities") or []
analyses = snapshot.get("recent_analyses") or []
applications = snapshot.get("applications") or []
active_profile = snapshot.get("active_profile")
metrics = snapshot.get("metrics") or {}

st.subheader("3. Dados históricos recuperados")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Perfis", _safe_count(profiles))
c2.metric("Oportunidades*", _safe_count(opportunities))
c3.metric("Análises*", _safe_count(analyses))
c4.metric("Candidaturas", _safe_count(applications))

st.caption(
    "* O snapshot usa limite de 20 para oportunidades e análises; "
    "os números exibidos aqui são suficientes para validar a associação."
)

if active_profile:
    st.write(
        "**Perfil ativo:** "
        + str(
            active_profile.get("profile_name")
            or active_profile.get("source_name")
            or active_profile.get("id")
            or "Encontrado"
        )
    )
else:
    st.write("**Perfil ativo:** nenhum")

st.write(
    "**Total de análises nas métricas:** "
    f"{metrics.get('total_analyses', 0)}"
)

mapping_ok = bool(app_user_id and (_safe_count(profiles) > 0 or metrics.get("total_analyses", 0) > 0))

if mapping_ok:
    st.success(
        "SPRINT 4.2 VALIDADO: o login Supabase está ligado "
        "ao usuário CareerCompass que possui o histórico existente."
    )
else:
    st.warning(
        "A identidade foi resolvida, mas nenhum histórico relevante foi encontrado. "
        "Não faça integração no main.py antes de revisar o vínculo."
    )

if st.button("Sair do teste"):
    try:
        sign_out(session.access_token)
    except Exception:
        pass
    st.session_state.pop(SESSION_KEY, None)
    st.rerun()
