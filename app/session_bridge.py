"""CareerCompass AI - browser session bridge (Sprint 4.6C).

Persists only the Supabase refresh token in the browser so a full Streamlit
reload can reconstruct a server-confirmed AuthSession. No service-role secret,
access JWT, profile data, or application data is stored by this component.
"""
from __future__ import annotations

import streamlit as st

_STORAGE_KEY = "careercompass.supabase.refresh_token.v1"

_SESSION_BRIDGE_JS = r"""
export default function({ data, setStateValue }) {
    const storageKey = data.storage_key;
    const action = data.action || "read";

    try {
        if (action === "save") {
            const token = data.refresh_token || "";
            if (token) {
                window.localStorage.setItem(storageKey, token);
            } else {
                window.localStorage.removeItem(storageKey);
            }
        } else if (action === "clear") {
            window.localStorage.removeItem(storageKey);
        }

        const stored = window.localStorage.getItem(storageKey) || "";
        setStateValue("refresh_token", stored);
        setStateValue("ready", true);
        setStateValue("error", "");
    } catch (err) {
        setStateValue("refresh_token", "");
        setStateValue("ready", true);
        setStateValue("error", String(err?.message || err || "browser_storage_error"));
    }
}
"""

_browser_session_component = st.components.v2.component(
    "careercompass_browser_session_bridge",
    js=_SESSION_BRIDGE_JS,
)


def mount_browser_session_bridge(
    *,
    action: str,
    refresh_token: str | None = None,
    key: str,
):
    """Mount the invisible browser bridge and return its state result."""
    if action not in {"read", "save", "clear"}:
        raise ValueError("Ação de sessão de navegador inválida.")

    return _browser_session_component(
        data={
            "action": action,
            "storage_key": _STORAGE_KEY,
            "refresh_token": refresh_token or "",
        },
        default={
            "refresh_token": "",
            "ready": False,
            "error": "",
        },
        key=key,
        on_refresh_token_change=lambda: None,
        on_ready_change=lambda: None,
        on_error_change=lambda: None,
        height=0,
    )
