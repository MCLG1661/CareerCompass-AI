"""
CareerCompass AI
Sprint 4.6D — Refresh Token Rotation + JWT/RLS Isolated Test

Purpose:
- Authenticate normally with Supabase Auth.
- Force a refresh immediately (without waiting for access-token expiry).
- Confirm that Supabase returns a valid refreshed session.
- Bind the refreshed access token to CareerCompass persistence.
- Resolve the CareerCompass app user and load the user's snapshot through RLS.

Security:
- Passwords/tokens are never printed.
- Tokens remain only in Streamlit session_state for this isolated test.
- This test does not call global sign-out, avoiding unintended invalidation of
  other active CareerCompass sessions for the same account.
"""

from __future__ import annotations

import streamlit as st

from auth_engine import refresh_session, sign_in_with_password
from persistence_service import (
    bind_authenticated_session,
    build_career_snapshot,
    clear_authenticated_session,
    ensure_user,
    get_storage_backend,
    persistence_uses_authenticated_session,
)


st.set_page_config(
    page_title="CareerCompass AI — Sprint 4.6D",
    page_icon="🧭",
    layout="centered",
)

SESSION_KEY = "sprint46d_auth_session"
REFRESH_RESULT_KEY = "sprint46d_refresh_result"


def _auth_user_name(auth_user) -> str | None:
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
    st.session_state.pop(REFRESH_RESULT_KEY, None)


st.title("🧭 CareerCompass AI — Sprint 4.6D")
st.caption("Teste isolado de rotação do refresh token + JWT/RLS")

backend = get_storage_backend()
if backend != "supabase":
    st.error(f"Este teste exige Supabase. Backend atual: {backend}")
    st.stop()

session = st.session_state.get(SESSION_KEY)

if session is None:
    st.info(
        "Faça login somente para executar este teste isolado. "
        "Nenhuma senha ou token será exibido."
    )

    with st.form("sprint46d_login"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button(
            "Entrar para testar refresh",
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
            st.session_state.pop(REFRESH_RESULT_KEY, None)
            st.rerun()
        except Exception as exc:
            st.error("Falha no login do teste.")
            st.exception(exc)

    st.stop()

auth_user = session.user
st.success("Login isolado concluído.")
st.write(f"**Usuário autenticado:** {auth_user.email or 'Conta Supabase'}")
st.write(
    "**Sessão inicial válida:** "
    + ("SIM" if bool(session.access_token and session.refresh_token) else "NÃO")
)

if not st.session_state.get(REFRESH_RESULT_KEY):
    st.warning(
        "Agora vamos forçar a renovação imediatamente. "
        "Não é necessário esperar o access token expirar."
    )

    if st.button(
        "Forçar refresh agora",
        type="primary",
        use_container_width=True,
    ):
        original_access_token = session.access_token
        original_refresh_token = session.refresh_token

        try:
            refreshed = refresh_session(original_refresh_token)

            if str(refreshed.user.id) != str(session.user.id):
                raise RuntimeError(
                    "O usuário retornado após o refresh não corresponde "
                    "ao usuário da sessão original."
                )

            access_rotated = refreshed.access_token != original_access_token
            refresh_rotated = refreshed.refresh_token != original_refresh_token

            bind_authenticated_session(refreshed.access_token)

            if not persistence_uses_authenticated_session():
                raise RuntimeError(
                    "O JWT renovado não ficou vinculado à persistência."
                )

            refreshed_user = refreshed.user
            app_user_id = ensure_user(
                name=_auth_user_name(refreshed_user),
                email=refreshed_user.email,
                auth_user_id=refreshed_user.id,
            )

            snapshot = build_career_snapshot(app_user_id)
            metrics = snapshot.get("metrics") or {}
            profiles = snapshot.get("profiles") or []
            analyses = snapshot.get("recent_analyses") or []
            applications = snapshot.get("applications") or []
            opportunities = snapshot.get("recent_opportunities") or []

            st.session_state[SESSION_KEY] = refreshed
            st.session_state[REFRESH_RESULT_KEY] = {
                "access_rotated": access_rotated,
                "refresh_rotated": refresh_rotated,
                "app_user_id": app_user_id,
                "profiles": len(profiles),
                "opportunities": len(opportunities),
                "analyses": len(analyses),
                "applications": len(applications),
                "total_analyses": metrics.get("total_analyses", 0),
            }
            st.rerun()

        except Exception as exc:
            try:
                clear_authenticated_session()
            except Exception:
                pass
            st.error("Falha no refresh ou na validação JWT/RLS.")
            st.exception(exc)

    if st.button("Cancelar teste", use_container_width=True):
        _reset_test()
        st.rerun()

    st.stop()

result = st.session_state[REFRESH_RESULT_KEY]

st.success(
    "SPRINT 4.6D VALIDADO: refresh executado e sessão renovada "
    "acessou a persistência através de JWT + RLS."
)

c1, c2 = st.columns(2)
c1.metric("Access token renovado", "SIM" if result["access_rotated"] else "NÃO")
c2.metric("Refresh token rotacionado", "SIM" if result["refresh_rotated"] else "NÃO")

st.subheader("Snapshot após o refresh")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Perfis", result["profiles"])
c2.metric("Oportunidades", result["opportunities"])
c3.metric("Análises", result["analyses"])
c4.metric("Candidaturas", result["applications"])

st.write(f"**Total de análises nas métricas:** {result['total_analyses']}")
st.caption(
    "Nenhum token foi exibido. O teste usa o access token renovado "
    "somente para validar a leitura do próprio usuário sob RLS."
)

if st.button("Encerrar teste local", use_container_width=True):
    _reset_test()
    st.rerun()
