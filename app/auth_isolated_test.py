"""
CareerCompass AI - Sprint 4.1 Auth Isolated Test
"""

import streamlit as st

from auth_engine import (
    AuthRequestError,
    auth_health_check,
    get_user,
    send_password_recovery,
    sign_in_with_password,
    sign_out,
    sign_up,
)

st.set_page_config(page_title="CareerCompass Auth Test", page_icon="🧭", layout="centered")

if "auth_test_session" not in st.session_state:
    st.session_state.auth_test_session = None

st.title("CareerCompass AI — Auth Test")
st.caption("Sprint 4.1 · cadastro, login, sessão e logout.")

health = auth_health_check()
if health.get("status") != "ok":
    st.error("Configuração do Supabase Auth incompleta.")
    st.json(health)
    st.stop()

st.success("Supabase Auth configurado.")

session = st.session_state.auth_test_session

if session is not None:
    try:
        user = get_user(session.access_token)
        st.success("Sessão autenticada.")
        st.write(f"**UID:** `{user.id}`")
        st.write(f"**E-mail:** {user.email or '—'}")
        st.write("**E-mail confirmado:** " + ("Sim" if user.email_confirmed_at else "Não"))
        if user.user_metadata.get("full_name"):
            st.write(f"**Nome:** {user.user_metadata['full_name']}")
        if st.button("Sair", type="primary", use_container_width=True):
            sign_out(session.access_token)
            st.session_state.auth_test_session = None
            st.rerun()
    except Exception as exc:
        st.session_state.auth_test_session = None
        st.error(f"Sessão inválida: {exc}")
else:
    login_tab, signup_tab, recovery_tab = st.tabs(["Entrar", "Criar conta", "Recuperar senha"])

    with login_tab:
        email = st.text_input("E-mail", key="login_email")
        password = st.text_input("Senha", type="password", key="login_password")
        if st.button("Entrar", type="primary", use_container_width=True, key="login_button"):
            try:
                st.session_state.auth_test_session = sign_in_with_password(email, password)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with signup_tab:
        name = st.text_input("Nome", key="signup_name")
        email = st.text_input("E-mail", key="signup_email")
        password = st.text_input("Senha", type="password", key="signup_password")
        if st.button("Criar conta", type="primary", use_container_width=True, key="signup_button"):
            try:
                result = sign_up(email, password, full_name=name)
                if result.confirmation_required:
                    st.success(result.message)
                    st.info("Confirme o e-mail e depois volte à aba Entrar.")
                elif result.session is not None:
                    st.session_state.auth_test_session = result.session
                    st.rerun()
                else:
                    st.success(result.message)
            except Exception as exc:
                st.error(str(exc))

    with recovery_tab:
        email = st.text_input("E-mail da conta", key="recovery_email")
        if st.button("Enviar recuperação", use_container_width=True, key="recovery_button"):
            try:
                send_password_recovery(email)
                st.success("Se o e-mail estiver cadastrado, as instruções serão enviadas.")
            except Exception as exc:
                st.error(str(exc))
