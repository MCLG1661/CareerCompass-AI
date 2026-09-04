"""
CareerCompass AI
Persistence Backend Cloud Test
"""

from __future__ import annotations

import streamlit as st

from persistence_service import (
    get_storage_backend,
    initialize_persistence,
    run_self_test,
)

st.set_page_config(
    page_title="CareerCompass Persistence Test",
    page_icon="🧭",
    layout="centered",
)

st.title("CareerCompass AI — Persistence Test")

try:
    health = initialize_persistence()
    result = run_self_test()
    backend = get_storage_backend()

    if result.get("status") == "ok":
        st.success("Status: OK")
    else:
        st.error(f"Status: {result.get('status', 'unknown')}")

    st.metric("Backend ativo", backend)

    if backend == "supabase":
        st.success("Seleção automática confirmada: Supabase Cloud.")
    else:
        st.warning("Backend ativo não é Supabase.")

    st.subheader("Health")
    st.json(health)

    st.subheader("Self-test")
    st.json(result)

except Exception as exc:
    st.error("Falha no teste de persistência.")
    st.exception(exc)
