"""
CareerCompass AI
Sprint 3 — Supabase Connection Test

Objetivo:
- validar se os Secrets do Streamlit estão disponíveis;
- testar comunicação real com o Supabase;
- consultar a tabela public.users sem inserir ou alterar dados.

Este arquivo NÃO exibe nem registra a Secret Key.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st


def get_secret(name: str) -> str | None:
    try:
        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except Exception:
        pass

    value = os.getenv(name)
    return value.strip() if value else None


def mask_url(url: str | None) -> str:
    if not url:
        return "não configurada"

    if "://" not in url:
        return "configurada"

    scheme, remainder = url.split("://", 1)
    host = remainder.split("/", 1)[0]

    if len(host) <= 10:
        masked_host = "***"
    else:
        masked_host = f"{host[:5]}…{host[-8:]}"

    return f"{scheme}://{masked_host}"


def supabase_get(
    url: str,
    secret_key: str,
    table: str,
) -> tuple[int, Any]:
    endpoint = (
        f"{url.rstrip('/')}/rest/v1/{table}"
        "?select=id&limit=1"
    )

    request = Request(
        endpoint,
        method="GET",
        headers={
            "apikey": secret_key,
            "Authorization": f"Bearer {secret_key}",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body) if body else []
            return response.status, parsed

    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"message": body}

        return exc.code, parsed

    except URLError as exc:
        return 0, {
            "message": f"Falha de rede: {exc.reason}"
        }


def main() -> None:
    st.set_page_config(
        page_title="CareerCompass AI — Supabase Test",
        page_icon="🧭",
        layout="centered",
    )

    st.title("CareerCompass AI")
    st.subheader("Sprint 3 — Supabase Connection Test")

    supabase_url = get_secret("SUPABASE_URL")
    secret_key = get_secret("SUPABASE_SECRET_KEY")

    if not supabase_url or not secret_key:
        st.error(
            "Secrets ausentes. Verifique SUPABASE_URL e "
            "SUPABASE_SECRET_KEY no ambiente do Streamlit."
        )

        st.write(
            {
                "SUPABASE_URL": bool(supabase_url),
                "SUPABASE_SECRET_KEY": bool(secret_key),
            }
        )
        st.stop()

    st.success("Secrets carregados com segurança.")
    st.caption(
        f"Projeto Supabase: {mask_url(supabase_url)}"
    )

    with st.spinner("Testando comunicação com public.users..."):
        status, payload = supabase_get(
            url=supabase_url,
            secret_key=secret_key,
            table="users",
        )

    if status == 200:
        st.success("Conexão Supabase: OK")
        st.metric("HTTP Status", status)
        st.write(
            "A tabela public.users respondeu corretamente."
        )
        st.caption(
            "Nenhum dado foi inserido, alterado ou excluído."
        )

    else:
        st.error("Conexão Supabase: FALHOU")
        st.metric(
            "HTTP Status",
            status if status else "Rede",
        )

        message = (
            payload.get("message")
            if isinstance(payload, dict)
            else str(payload)
        )

        st.code(
            message or "Erro sem mensagem retornada.",
            language="text",
        )

        if status in (401, 403):
            st.info(
                "Os Secrets chegaram ao app, mas a API ainda "
                "não tem permissão para consultar public.users. "
                "Isso é corrigido no Supabase sem expor a chave."
            )


if __name__ == "__main__":
    main()
