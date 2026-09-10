"""
CareerCompass AI — SQLite -> Supabase Migration Tool

Run locally:
    python -m streamlit run app/sqlite_to_supabase_migration.py

Safety properties:
- reads SQLite only;
- writes only to Supabase;
- deterministic UUID mapping;
- idempotent upserts;
- credentials stay in memory only.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "careercompass.db"
NS = uuid.UUID("118ea38f-a0b2-46f7-b2ae-11d16b72a07d")


def uid(kind: str, legacy_id: str) -> str:
    return str(uuid.uuid5(NS, f"{kind}:{legacy_id}"))


def parse_json(value: Any) -> Any:
    if value in (None, ""):
        return {}
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return value


def rows(db: Path, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def users(db: Path) -> list[dict[str, Any]]:
    return rows(db, """
        SELECT u.*,
          (SELECT COUNT(*) FROM career_profiles p WHERE p.user_id=u.id) profiles_count,
          (SELECT COUNT(*) FROM opportunities o WHERE o.user_id=u.id) opportunities_count,
          (SELECT COUNT(*) FROM analyses a WHERE a.user_id=u.id) analyses_count,
          (SELECT COUNT(*) FROM applications ap WHERE ap.user_id=u.id) applications_count,
          (SELECT COUNT(*) FROM career_events e WHERE e.user_id=u.id) events_count
        FROM users u
        ORDER BY analyses_count DESC, applications_count DESC,
                 opportunities_count DESC, profiles_count DESC, u.created_at ASC
    """)


def counts_sqlite(db: Path, user_id: str) -> dict[str, int]:
    result = {}
    for table in ["career_profiles", "opportunities", "analyses", "applications", "career_events"]:
        result[table] = int(rows(db, f"SELECT COUNT(*) total FROM {table} WHERE user_id=?", (user_id,))[0]["total"])
    return result


class SB:
    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.key = key.strip()

    def call(self, table: str, method="GET", params=None, body=None, upsert=False):
        endpoint = f"{self.url}/rest/v1/{table}"
        if params:
            endpoint += "?" + urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if method in {"POST", "PATCH"}:
            headers["Prefer"] = (
                "resolution=merge-duplicates,return=representation"
                if upsert else "return=representation"
            )
        data = None if body is None else json.dumps(body, ensure_ascii=False, default=str).encode()
        req = Request(endpoint, data=data, method=method, headers=headers)
        try:
            with urlopen(req, timeout=25) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else []
        except HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            raise RuntimeError(f"Supabase HTTP {exc.code}: {raw}") from exc
        except URLError as exc:
            raise RuntimeError(f"Falha de rede: {exc.reason}") from exc

    def default_user(self):
        r = self.call("users", params={"select":"*","name":"eq.CareerCompass User","order":"created_at.asc","limit":1})
        return r[0] if r else None

    def counts(self, user_id: str) -> dict[str, int]:
        out = {}
        for table in ["career_profiles", "opportunities", "analyses", "applications", "career_events"]:
            out[table] = len(self.call(table, params={"select":"id","user_id":f"eq.{user_id}"}) or [])
        return out


def migrate(db: Path, source_user: str, sb: SB, target_user: str) -> dict[str, int]:
    profiles = rows(db, "SELECT * FROM career_profiles WHERE user_id=? ORDER BY created_at", (source_user,))
    opportunities = rows(db, "SELECT * FROM opportunities WHERE user_id=? ORDER BY created_at", (source_user,))
    analyses = rows(db, "SELECT * FROM analyses WHERE user_id=? ORDER BY created_at", (source_user,))
    applications = rows(db, "SELECT * FROM applications WHERE user_id=? ORDER BY created_at", (source_user,))
    events = rows(db, "SELECT * FROM career_events WHERE user_id=? ORDER BY created_at", (source_user,))

    pmap = {r["id"]: uid("profile", r["id"]) for r in profiles}
    omap = {r["id"]: uid("opportunity", r["id"]) for r in opportunities}
    amap = {r["id"]: uid("analysis", r["id"]) for r in analyses}
    appmap = {r["id"]: uid("application", r["id"]) for r in applications}
    emap = {r["id"]: uid("event", r["id"]) for r in events}

    sb.call("career_profiles", "PATCH", {"user_id":f"eq.{target_user}","is_active":"eq.true"}, {"is_active":False})

    done = {"career_profiles":0,"opportunities":0,"analyses":0,"applications":0,"career_events":0}

    for r in profiles:
        sb.call("career_profiles", "POST", {"on_conflict":"id"}, {
            "id":pmap[r["id"]], "user_id":target_user,
            "profile_name":r.get("profile_name") or "Perfil principal",
            "source_name":r.get("source_name"), "content_hash":r.get("content_hash"),
            "profile_type":r.get("profile_type") or "resume",
            "profile_data":{"raw_profile_text":r.get("raw_profile_text") or "", "structured_profile":parse_json(r.get("structured_profile"))},
            "is_active":bool(r.get("is_active")), "is_archived":bool(r.get("is_archived")),
            "last_used_at":r.get("last_used_at"), "created_at":r.get("created_at"), "updated_at":r.get("updated_at"),
        }, True)
        done["career_profiles"] += 1

    for r in opportunities:
        sb.call("opportunities", "POST", {"on_conflict":"id"}, {
            "id":omap[r["id"]], "user_id":target_user,
            "job_title":r.get("job_title") or "Oportunidade", "company":r.get("company"),
            "description":r.get("job_description") or "", "source":r.get("source"), "source_url":r.get("source_url"),
            "status":r.get("status") or "analyzed", "opportunity_data":{},
            "created_at":r.get("created_at"), "updated_at":r.get("updated_at"),
        }, True)
        done["opportunities"] += 1

    for r in analyses:
        if r.get("profile_id") not in pmap or r.get("opportunity_id") not in omap:
            continue
        sb.call("analyses", "POST", {"on_conflict":"id"}, {
            "id":amap[r["id"]], "user_id":target_user,
            "profile_id":pmap[r["profile_id"]], "opportunity_id":omap[r["opportunity_id"]],
            "career_fit_score":r.get("career_fit_score"), "ats_score":r.get("ats_score"), "tailoring_score":r.get("tailoring_score"),
            "curator_report":parse_json(r.get("career_fit_report")), "ats_report":parse_json(r.get("ats_report")),
            "tailoring_report":parse_json(r.get("tailoring_report")), "opportunity_report":{},
            "decision_report":{"classification":r.get("classification"), "recommendation":r.get("recommendation"), "recommendation_report":parse_json(r.get("recommendation_report"))},
            "decision_score":None, "created_at":r.get("created_at"),
        }, True)
        done["analyses"] += 1

    for r in applications:
        if r.get("opportunity_id") not in omap:
            continue
        sb.call("applications", "POST", {"on_conflict":"id"}, {
            "id":appmap[r["id"]], "user_id":target_user,
            "opportunity_id":omap[r["opportunity_id"]],
            "analysis_id":amap.get(r.get("analysis_id")) if r.get("analysis_id") else None,
            "status":r.get("status") or "planned", "applied_at":r.get("applied_at"), "interview_at":r.get("interview_at"),
            "outcome":r.get("outcome"), "notes":r.get("notes"), "created_at":r.get("created_at"), "updated_at":r.get("updated_at"),
        }, True)
        done["applications"] += 1

    def remap(t, i):
        if not i: return None
        t = (t or "").lower()
        if t in {"career_profile","profile"}: return pmap.get(i, i)
        if t == "opportunity": return omap.get(i, i)
        if t == "analysis": return amap.get(i, i)
        if t == "application": return appmap.get(i, i)
        return i

    for r in events:
        sb.call("career_events", "POST", {"on_conflict":"id"}, {
            "id":emap[r["id"]], "user_id":target_user, "event_type":r.get("event_type") or "legacy_event",
            "event_data":{"entity_type":r.get("entity_type"), "entity_id":remap(r.get("entity_type"), r.get("entity_id")), "data":parse_json(r.get("event_data")), "migration_source":"sqlite", "legacy_event_id":r.get("id")},
            "created_at":r.get("created_at"),
        }, True)
        done["career_events"] += 1

    return done


st.set_page_config(page_title="CareerCompass SQLite → Supabase", page_icon="🧭", layout="wide")
st.title("CareerCompass AI — Migração SQLite → Supabase")
st.caption("Ferramenta local, não destrutiva e idempotente.")

db = Path(st.text_input("SQLite local", value=str(DEFAULT_DB)))
if not db.exists():
    st.error(f"Banco não encontrado: {db}")
    st.stop()

local_users = users(db)
if not local_users:
    st.error("Nenhum usuário encontrado no SQLite.")
    st.stop()

labels = {f"{u.get('name') or 'Sem nome'} | {u['id']} | {u['analyses_count']} análises | {u['applications_count']} candidaturas":u['id'] for u in local_users}
label = st.selectbox("Usuário local de origem", list(labels.keys()), index=0)
source_user = labels[label]
st.subheader("Prévia do SQLite")
st.json(counts_sqlite(db, source_user))

st.divider()
st.subheader("Credenciais do Supabase")
st.info("Cole as credenciais apenas nesta tela local. Elas não são gravadas em arquivo.")
url = st.text_input("SUPABASE_URL")
key = st.text_input("SUPABASE_SECRET_KEY", type="password")

if url and key:
    try:
        sb = SB(url, key)
        cloud_user = sb.default_user()
        if not cloud_user:
            st.error("Usuário cloud 'CareerCompass User' não encontrado.")
            st.stop()
        target = str(cloud_user["id"])
        st.success("Usuário de produção encontrado no Supabase.")
        st.write(f"Destino: **{cloud_user.get('name', 'CareerCompass User')}**")
        st.write(f"ID cloud: `{target}`")
        st.subheader("Supabase antes da migração")
        st.json(sb.counts(target))
        confirmed = st.checkbox("Confirmo a cópia dos dados locais para o Supabase, sem apagar o SQLite.")
        if st.button("Migrar SQLite → Supabase", type="primary", disabled=not confirmed):
            with st.spinner("Migrando..."):
                done = migrate(db, source_user, sb, target)
                after = sb.counts(target)
            st.success("Migração concluída.")
            st.subheader("Registros processados")
            st.json(done)
            st.subheader("Supabase após a migração")
            st.json(after)
    except Exception as exc:
        st.error("Falha na migração.")
        st.exception(exc)
else:
    st.warning("Informe SUPABASE_URL e SUPABASE_SECRET_KEY para continuar.")
