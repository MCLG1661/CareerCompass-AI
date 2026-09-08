"""
CareerCompass AI
Sprint 4.7B — Bidirectional Cross-User Read/Write Isolation Test

Validates, using two authenticated Supabase users:
- A cannot SELECT B's career profile by known profile ID.
- B cannot SELECT A's career profile by known profile ID.
- A cannot PATCH B's career profile by known profile ID.
- B cannot PATCH A's career profile by known profile ID.
- The legitimate owner verifies the original profile name is unchanged after
  the foreign PATCH attempt.

This is intentionally non-destructive:
- The attempted foreign PATCH uses a temporary marker.
- A passing RLS policy returns no updated foreign row.
- The owner then re-reads the profile to prove no mutation occurred.
"""

from __future__ import annotations

from uuid import uuid4

import streamlit as st

from auth_engine import sign_in_with_password
from persistence_service import (
    bind_authenticated_session,
    build_career_snapshot,
    clear_authenticated_session,
    ensure_user,
    get_storage_backend,
)
import supabase_database_engine as cloud_db


st.set_page_config(
    page_title="CareerCompass AI — Sprint 4.7B",
    page_icon="🧭",
    layout="wide",
)

SESSION_A_KEY = "sprint47b_session_a"
SESSION_B_KEY = "sprint47b_session_b"
RESULT_KEY = "sprint47b_result"


def _auth_name(auth_user) -> str | None:
    metadata = getattr(auth_user, "user_metadata", None) or {}
    return (
        str(metadata.get("full_name") or "").strip()
        or str(metadata.get("name") or "").strip()
        or str(metadata.get("display_name") or "").strip()
        or None
    )


def _reset() -> None:
    try:
        clear_authenticated_session()
    except Exception:
        pass
    for key in (SESSION_A_KEY, SESSION_B_KEY, RESULT_KEY):
        st.session_state.pop(key, None)


def _login_form(label: str, session_key: str):
    session = st.session_state.get(session_key)
    if session is not None:
        st.success(f"{label}: login concluído.")
        st.write(f"**Conta:** {session.user.email or 'Conta Supabase'}")
        return session

    with st.form(f"{session_key}_form"):
        st.subheader(label)
        email = st.text_input("E-mail", key=f"{session_key}_email")
        password = st.text_input(
            "Senha",
            type="password",
            key=f"{session_key}_password",
        )
        submitted = st.form_submit_button(
            f"Entrar como {label}",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not email.strip() or not password:
            st.warning(f"{label}: informe e-mail e senha.")
            return None
        try:
            session = sign_in_with_password(email.strip(), password)
            st.session_state[session_key] = session
            st.session_state.pop(RESULT_KEY, None)
            st.rerun()
        except Exception as exc:
            st.error(f"{label}: falha no login.")
            st.exception(exc)

    return None


def _own_context(session):
    bind_authenticated_session(session.access_token)
    auth_user = session.user
    app_user_id = ensure_user(
        name=_auth_name(auth_user),
        email=auth_user.email,
        auth_user_id=auth_user.id,
    )
    snapshot = build_career_snapshot(app_user_id)
    return app_user_id, snapshot


def _first_profile(snapshot):
    profiles = snapshot.get("profiles") or []
    if not profiles:
        return None
    profile = profiles[0] or {}
    profile_id = str(profile.get("id") or "").strip()
    if not profile_id:
        return None
    return profile


def _read_profile_with_current_jwt(profile_id: str):
    return cloud_db.get_career_profile(profile_id)


def _foreign_patch_with_current_jwt(profile_id: str, marker: str):
    return cloud_db._request(
        "career_profiles",
        method="PATCH",
        params={
            "id": f"eq.{profile_id}",
        },
        body={
            "profile_name": marker,
        },
        return_representation=True,
    )


def _record(checks, name: str, passed: bool, detail: str) -> None:
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "detail": detail,
        }
    )


st.title("🧭 CareerCompass AI — Sprint 4.7B")
st.caption("SELECT + UPDATE cruzado bidirecional sob JWT + RLS")

backend = get_storage_backend()
if backend != "supabase":
    st.error(f"Este teste exige Supabase. Backend atual: {backend}")
    st.stop()

col_a, col_b = st.columns(2)

with col_a:
    session_a = _login_form("Usuário A", SESSION_A_KEY)

with col_b:
    session_b = _login_form("Usuário B", SESSION_B_KEY)

if session_a is None or session_b is None:
    st.info("Faça login com duas contas Supabase diferentes para continuar.")
    st.stop()

if str(session_a.user.id) == str(session_b.user.id):
    st.error("Use duas contas Supabase diferentes.")
    st.stop()

st.divider()

if not st.session_state.get(RESULT_KEY):
    st.warning(
        "O teste fará tentativas de SELECT e PATCH cruzadas por profile_id conhecido. "
        "O PATCH é validado como não destrutivo: o proprietário confirma depois que "
        "o nome original permaneceu inalterado."
    )

    if st.button(
        "Executar teste final de isolamento",
        type="primary",
        use_container_width=True,
    ):
        try:
            app_user_a, snapshot_a = _own_context(session_a)
            app_user_b, snapshot_b = _own_context(session_b)

            if app_user_a == app_user_b:
                raise RuntimeError(
                    "Falha crítica: duas contas Auth diferentes resolveram "
                    "o mesmo public.users.id."
                )

            profile_a = _first_profile(snapshot_a)
            profile_b = _first_profile(snapshot_b)

            if not profile_a or not profile_b:
                raise RuntimeError(
                    "Cada usuário precisa possuir pelo menos um career_profile "
                    "persistido antes deste teste."
                )

            profile_a_id = str(profile_a["id"])
            profile_b_id = str(profile_b["id"])

            # Capture legitimate originals under each owner's JWT.
            bind_authenticated_session(session_a.access_token)
            owner_a_before = _read_profile_with_current_jwt(profile_a_id)
            if not owner_a_before:
                raise RuntimeError("Usuário A não conseguiu ler o próprio perfil.")
            owner_a_name = str(owner_a_before.get("profile_name") or "")

            bind_authenticated_session(session_b.access_token)
            owner_b_before = _read_profile_with_current_jwt(profile_b_id)
            if not owner_b_before:
                raise RuntimeError("Usuário B não conseguiu ler o próprio perfil.")
            owner_b_name = str(owner_b_before.get("profile_name") or "")

            checks = []

            # ----------------------------------------------------------
            # A attacks B
            # ----------------------------------------------------------
            bind_authenticated_session(session_a.access_token)

            foreign_b_read = _read_profile_with_current_jwt(profile_b_id)
            _record(
                checks,
                "A não lê perfil de B por ID",
                foreign_b_read is None,
                "Bloqueado/oculto pelo RLS."
                if foreign_b_read is None
                else "DADO ESTRANGEIRO VISÍVEL.",
            )

            marker_a_to_b = f"RLS-BLOCK-A2B-{uuid4().hex[:8]}"
            patch_a_to_b = _foreign_patch_with_current_jwt(
                profile_b_id,
                marker_a_to_b,
            )
            patch_a_to_b_blocked = not bool(patch_a_to_b)
            _record(
                checks,
                "A não atualiza perfil de B por ID",
                patch_a_to_b_blocked,
                "PATCH estrangeiro não retornou linha atualizada."
                if patch_a_to_b_blocked
                else "PATCH ESTRANGEIRO RETORNOU DADOS.",
            )

            # Owner B verifies no mutation occurred.
            bind_authenticated_session(session_b.access_token)
            owner_b_after = _read_profile_with_current_jwt(profile_b_id)
            b_unchanged = bool(
                owner_b_after
                and str(owner_b_after.get("profile_name") or "") == owner_b_name
                and str(owner_b_after.get("profile_name") or "") != marker_a_to_b
            )
            _record(
                checks,
                "Perfil de B permaneceu inalterado após PATCH de A",
                b_unchanged,
                "Nome original preservado."
                if b_unchanged
                else "ALTERAÇÃO ESTRANGEIRA DETECTADA.",
            )

            # ----------------------------------------------------------
            # B attacks A
            # ----------------------------------------------------------
            foreign_a_read = _read_profile_with_current_jwt(profile_a_id)
            _record(
                checks,
                "B não lê perfil de A por ID",
                foreign_a_read is None,
                "Bloqueado/oculto pelo RLS."
                if foreign_a_read is None
                else "DADO ESTRANGEIRO VISÍVEL.",
            )

            marker_b_to_a = f"RLS-BLOCK-B2A-{uuid4().hex[:8]}"
            patch_b_to_a = _foreign_patch_with_current_jwt(
                profile_a_id,
                marker_b_to_a,
            )
            patch_b_to_a_blocked = not bool(patch_b_to_a)
            _record(
                checks,
                "B não atualiza perfil de A por ID",
                patch_b_to_a_blocked,
                "PATCH estrangeiro não retornou linha atualizada."
                if patch_b_to_a_blocked
                else "PATCH ESTRANGEIRO RETORNOU DADOS.",
            )

            # Owner A verifies no mutation occurred.
            bind_authenticated_session(session_a.access_token)
            owner_a_after = _read_profile_with_current_jwt(profile_a_id)
            a_unchanged = bool(
                owner_a_after
                and str(owner_a_after.get("profile_name") or "") == owner_a_name
                and str(owner_a_after.get("profile_name") or "") != marker_b_to_a
            )
            _record(
                checks,
                "Perfil de A permaneceu inalterado após PATCH de B",
                a_unchanged,
                "Nome original preservado."
                if a_unchanged
                else "ALTERAÇÃO ESTRANGEIRA DETECTADA.",
            )

            clear_authenticated_session()

            st.session_state[RESULT_KEY] = {
                "passed": all(item["passed"] for item in checks),
                "checks": checks,
                "a_profiles": len(snapshot_a.get("profiles") or []),
                "b_profiles": len(snapshot_b.get("profiles") or []),
            }
            st.rerun()

        except Exception as exc:
            try:
                clear_authenticated_session()
            except Exception:
                pass
            st.error("Falha ao executar o teste final de isolamento.")
            st.exception(exc)

    if st.button("Cancelar teste", use_container_width=True):
        _reset()
        st.rerun()

    st.stop()

result = st.session_state[RESULT_KEY]

if result["passed"]:
    st.success(
        "SPRINT 4.7B VALIDADO: SELECT e UPDATE cruzados foram bloqueados "
        "nos dois sentidos e os perfis legítimos permaneceram inalterados."
    )
else:
    st.error(
        "SPRINT 4.7B FALHOU: pelo menos um acesso cruzado não foi bloqueado "
        "ou houve indício de alteração estrangeira."
    )

c1, c2 = st.columns(2)
c1.metric("Perfis próprios — Usuário A", result["a_profiles"])
c2.metric("Perfis próprios — Usuário B", result["b_profiles"])

st.subheader("Checks finais de isolamento")
for check in result["checks"]:
    prefix = "✅" if check["passed"] else "❌"
    st.write(f"{prefix} **{check['name']}** — {check['detail']}")

st.caption(
    "O teste não exibe tokens, senhas, profile_id ou conteúdo dos currículos. "
    "Ele apenas valida visibilidade e mutação sob JWT + RLS."
)

if st.button("Encerrar teste local", use_container_width=True):
    _reset()
    st.rerun()
