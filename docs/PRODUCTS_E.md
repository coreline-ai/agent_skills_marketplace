✅ 최종 완성 상태(더 이상 “다음 단계” 없음)

API(FastAPI): 공개 UI + Admin API 완비

인입/파싱/집계 워커: 스케줄 실행 가능

웹(Next.js):

Public: TOP10 / Skills 탐색 / 상세

Admin: 로그인 / Raw 큐 / Preview / Candidates / Approve(새로등록/병합) / Skill CRUD

Docker Compose: Postgres + API + Web + Worker(옵션)까지

Seed: 카테고리/소스 기본 데이터 주입

CORS/ENV/문서: 운영에 필요한 최소 구성을 포함


1) FastAPI 최종 보강 (CORS + Seed + Worker 엔트리)
1.1 app/main.py (CORS 추가로 교체)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings
from app.api.router import router

app = FastAPI(title=settings.APP_NAME)

# CORS: Web UI에서 API 호출 가능하게
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영에서는 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

1.2 Seed 스크립트 추가: app/seed.py

(카테고리/태그/소스 최소값 자동 생성)

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.category import Category
from app.models.skill_source import SkillSource


DEFAULT_CATEGORIES = [
    ("productivity", "Productivity", "Productivity & workflow"),
    ("devops", "DevOps", "CI/CD, infra, automation"),
    ("coding", "Coding", "Coding assistants & developer tools"),
    ("media", "Media", "Media generation & editing"),
    ("data", "Data", "Data analysis & ETL"),
]

DEFAULT_SOURCES = [
    ("awesome_list", "list"),
    ("anthropic_skills", "github"),
]


def run():
    db: Session = SessionLocal()
    try:
        # categories
        existing = {c.key: c for c in db.execute(select(Category)).scalars().all()}
        for key, name, desc in DEFAULT_CATEGORIES:
            if key not in existing:
                db.add(Category(key=key, name=name, description=desc, sort_order=0, is_active=True))

        # sources
        existing_s = {s.name: s for s in db.execute(select(SkillSource)).scalars().all()}
        for name, typ in DEFAULT_SOURCES:
            if name not in existing_s:
                db.add(SkillSource(name=name, type=typ, base_url=None, api_url=None, status="active"))

        db.commit()
        print({"ok": True})
    finally:
        db.close()


if __name__ == "__main__":
    run()

2) Next.js 웹 UI (Public + Admin) “완성본”

아래는 /web 폴더로 새로 추가하면 됨.

2.1 web/package.json
{
  "name": "skills-market-web",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000"
  },
  "dependencies": {
    "next": "15.2.4",
    "react": "19.0.0",
    "react-dom": "19.0.0"
  }
}

2.2 web/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone"
};
module.exports = nextConfig;

2.3 web/.env.example
NEXT_PUBLIC_API_BASE="http://localhost:8000"

2.4 web/app/layout.tsx
export const metadata = {
  title: "Agent Skills Marketplace",
  description: "SKILL.md 기반 에이전트 스킬 마켓플레이스"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", margin: 0 }}>
        <div style={{ padding: 16, borderBottom: "1px solid #eee", display: "flex", gap: 12 }}>
          <a href="/" style={{ textDecoration: "none" }}>🏠 Home</a>
          <a href="/skills" style={{ textDecoration: "none" }}>📚 Skills</a>
          <a href="/admin/login" style={{ textDecoration: "none" }}>🛠️ Admin</a>
        </div>
        <div style={{ padding: 16 }}>{children}</div>
      </body>
    </html>
  );
}

2.5 web/app/lib/api.ts (API 클라이언트 + 토큰)
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("admin_token");
}

export function setToken(t: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem("admin_token", t);
}

export function clearToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("admin_token");
}

export async function apiGet(path: string, auth: boolean = false) {
  const headers: any = {};
  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { headers, cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPost(path: string, body: any, auth: boolean = false) {
  const headers: any = { "Content-Type": "application/json" };
  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPatch(path: string, body: any, auth: boolean = false) {
  const headers: any = { "Content-Type": "application/json" };
  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { method: "PATCH", headers, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

2.6 Public: Home (TOP10)
web/app/page.tsx
import { apiGet } from "./lib/api";

export default async function HomePage() {
  const top10 = await apiGet("/rankings/top10");
  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Agent Skills Marketplace</h1>
      <p>오늘의 인기 TOP 10</p>
      <ol>
        {top10.map((s: any) => (
          <li key={s.id}>
            <a href={`/skills/${s.id}`}>{s.name}</a>{" "}
            <span style={{ color: "#666" }}>({s.spec_format}, {s.status})</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

2.7 Public: Skills List (검색/필터/정렬)
web/app/skills/page.tsx
"use client";

import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

export default function SkillsPage() {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("latest");
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const qs = new URLSearchParams();
      if (q) qs.set("q", q);
      qs.set("sort", sort);
      const data = await apiGet(`/skills?${qs.toString()}`);
      setItems(data);
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [sort]);

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Skills</h1>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search..." />
        <button onClick={load}>Search</button>
        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="latest">Latest</option>
          <option value="popular">Popular</option>
        </select>
      </div>

      {loading && <p>Loading...</p>}
      {err && <p style={{ color: "crimson" }}>{err}</p>}

      <ul>
        {items.map((s) => (
          <li key={s.id}>
            <a href={`/skills/${s.id}`}>{s.name}</a>{" "}
            <span style={{ color: "#666" }}>{s.summary || ""}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

2.8 Public: Skill Detail
web/app/skills/[id]/page.tsx
import { apiGet } from "../../lib/api";

export default async function SkillDetailPage({ params }: { params: { id: string } }) {
  const s = await apiGet(`/skills/${params.id}`);
  return (
    <div>
      <h1 style={{ marginTop: 0 }}>{s.name}</h1>
      <p style={{ color: "#666" }}>{s.summary || ""}</p>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <span>status: <b>{s.status}</b></span>
        <span>spec: <b>{s.spec_format}</b></span>
        <span>type: <b>{s.skill_type}</b></span>
      </div>

      {s.tags?.length ? (
        <p>tags: {s.tags.join(", ")}</p>
      ) : null}

      {s.canonical_repo ? (
        <p>
          repo: <a href={`https://github.com/${s.canonical_repo}`} target="_blank">{s.canonical_repo}</a>
        </p>
      ) : null}

      <h3>Description</h3>
      <pre style={{ whiteSpace: "pre-wrap", background: "#fafafa", padding: 12, border: "1px solid #eee" }}>
        {s.description_md || "(empty)"}
      </pre>
    </div>
  );
}

3) Admin UI (로그인/Raw 큐/프리뷰/후보/승인/Skill CRUD)
3.1 web/app/admin/login/page.tsx
"use client";

import { useState } from "react";
import { apiPost, setToken } from "../../lib/api";

export default function AdminLoginPage() {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin1234!");
  const [err, setErr] = useState<string | null>(null);

  async function login() {
    setErr(null);
    try {
      // OAuth2PasswordRequestForm 방식이므로 form-encoded가 정석이지만,
      // MVP 편의상 JSON으로 보내면 서버가 못받을 수 있음 -> 아래처럼 form 방식으로 호출
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setToken(data.access_token);
      window.location.href = "/admin/raw";
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Admin Login</h1>
      <div style={{ display: "grid", gap: 8, maxWidth: 320 }}>
        <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" type="password" />
        <button onClick={login}>Login</button>
        {err && <p style={{ color: "crimson" }}>{err}</p>}
      </div>
    </div>
  );
}

3.2 web/app/admin/raw/page.tsx (Raw 큐 리스트)
"use client";

import { useEffect, useState } from "react";
import { apiGet, clearToken } from "../../lib/api";

export default function AdminRawQueuePage() {
  const [items, setItems] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const data = await apiGet("/admin/raw-skills?status=queued&page=1&size=100", true);
      setItems(data);
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Raw Queue</h1>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <button onClick={load}>Refresh</button>
        <button onClick={() => { clearToken(); window.location.href = "/admin/login"; }}>Logout</button>
        <a href="/admin/skills">Skills CRUD</a>
      </div>

      {err && <p style={{ color: "crimson" }}>{err}</p>}

      <table cellPadding={8} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr style={{ background: "#fafafa" }}>
            <th align="left">name_raw</th>
            <th align="left">repo</th>
            <th align="left">parse</th>
            <th align="left">action</th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id} style={{ borderTop: "1px solid #eee" }}>
              <td>{r.name_raw || "(no name)"}</td>
              <td>{r.github_repo || ""}</td>
              <td>{r.parse_status}</td>
              <td>
                <a href={`/admin/raw/${r.id}`}>Open</a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

3.3 web/app/admin/raw/[id]/page.tsx (Preview + Candidates + Approve)
"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../../lib/api";

export default function AdminRawDetailPage({ params }: { params: { id: string } }) {
  const [preview, setPreview] = useState<any>(null);
  const [cands, setCands] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  const [mode, setMode] = useState<"new" | "merge">("new");
  const [existingSkillId, setExistingSkillId] = useState("");
  const [tags, setTags] = useState("");

  async function load() {
    setErr(null);
    try {
      const p = await apiGet(`/admin/raw-skills/${params.id}/preview`, true);
      const c = await apiGet(`/admin/raw-skills/${params.id}/candidates?limit=10`, true);
      setPreview(p);
      setCands(c);
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  useEffect(() => { load(); }, []);

  async function approve() {
    setErr(null);
    try {
      const tagList = tags.split(",").map(s => s.trim()).filter(Boolean);
      const body: any = {
        raw_skill_id: params.id,
        create_new: mode === "new",
        existing_skill_id: mode === "merge" ? existingSkillId : null,
        tags: tagList
      };
      const res = await apiPost("/admin/raw-skills/approve", body, true);
      alert(`Approved. skill_id=${res.skill_id}`);
      window.location.href = "/admin/raw";
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Raw Detail</h1>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <a href="/admin/raw">← Back</a>
        <button onClick={load}>Reload</button>
      </div>

      {err && <p style={{ color: "crimson" }}>{err}</p>}

      {preview ? (
        <div style={{ display: "grid", gap: 12 }}>
          <div>
            <h3>Basic</h3>
            <pre style={{ whiteSpace: "pre-wrap", background: "#fafafa", padding: 12, border: "1px solid #eee" }}>
{JSON.stringify({
  id: preview.id,
  name_raw: preview.name_raw,
  github_repo: preview.github_repo,
  skill_path: preview.skill_path,
  parse_status: preview.parse_status,
  parse_errors: preview.parse_errors
}, null, 2)}
            </pre>
          </div>

          <div>
            <h3>Preview (parsed)</h3>
            <pre style={{ whiteSpace: "pre-wrap", background: "#fafafa", padding: 12, border: "1px solid #eee" }}>
{JSON.stringify(preview.preview || {}, null, 2)}
            </pre>
          </div>

          <div>
            <h3>Candidates</h3>
            <pre style={{ whiteSpace: "pre-wrap", background: "#fafafa", padding: 12, border: "1px solid #eee" }}>
{JSON.stringify(cands || {}, null, 2)}
            </pre>
          </div>

          <div>
            <h3>Approve</h3>
            <div style={{ display: "grid", gap: 8, maxWidth: 520 }}>
              <div style={{ display: "flex", gap: 12 }}>
                <label><input type="radio" checked={mode === "new"} onChange={() => setMode("new")} /> 새 스킬</label>
                <label><input type="radio" checked={mode === "merge"} onChange={() => setMode("merge")} /> 기존 병합</label>
              </div>
              {mode === "merge" && (
                <input value={existingSkillId} onChange={(e) => setExistingSkillId(e.target.value)} placeholder="existing_skill_id (UUID)" />
              )}
              <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="tags (comma separated)" />
              <button onClick={approve}>Approve</button>
            </div>
          </div>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

3.4 web/app/admin/skills/page.tsx (Skill CRUD 간단판)
"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPatch } from "../../lib/api";

export default function AdminSkillsCrudPage() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [summary, setSummary] = useState("");
  const [tags, setTags] = useState("");

  async function load() {
    setErr(null);
    try {
      const qs = new URLSearchParams();
      if (q) qs.set("q", q);
      const data = await apiGet(`/skills?${qs.toString()}`, false);
      setItems(data);
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  useEffect(() => { load(); }, []);

  async function create() {
    setErr(null);
    try {
      const tagList = tags.split(",").map(s => s.trim()).filter(Boolean);
      const res = await apiPost("/admin/skills", {
        name,
        summary,
        status: "active",
        tags: tagList
      }, true);
      alert(`created: ${res.skill_id}`);
      setName(""); setSummary(""); setTags("");
      await load();
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  async function patchStatus(id: string, status: string) {
    setErr(null);
    try {
      await apiPatch(`/admin/skills/${id}`, { status }, true);
      await load();
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Admin Skills CRUD</h1>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <a href="/admin/raw">← Raw Queue</a>
      </div>

      {err && <p style={{ color: "crimson" }}>{err}</p>}

      <h3>Create</h3>
      <div style={{ display: "grid", gap: 8, maxWidth: 520, marginBottom: 16 }}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="name" />
        <input value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="summary" />
        <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="tags comma separated" />
        <button onClick={create}>Create</button>
      </div>

      <h3>List</h3>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="search..." />
        <button onClick={load}>Search</button>
      </div>

      <table cellPadding={8} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr style={{ background: "#fafafa" }}>
            <th align="left">name</th>
            <th align="left">status</th>
            <th align="left">actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((s) => (
            <tr key={s.id} style={{ borderTop: "1px solid #eee" }}>
              <td><a href={`/skills/${s.id}`}>{s.name}</a></td>
              <td>{s.status}</td>
              <td style={{ display: "flex", gap: 8 }}>
                <button onClick={() => patchStatus(s.id, "active")}>active</button>
                <button onClick={() => patchStatus(s.id, "archived")}>archive</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

4) Docker “한 방 운영” (DB + API + Web + Worker)
4.1 API Dockerfile (루트에 Dockerfile.api)
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY app /app/app
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini

RUN pip install -U pip && pip install -e .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["bash", "-lc", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

4.2 Web Dockerfile (web/Dockerfile)
FROM node:20-slim

WORKDIR /web
COPY package.json /web/package.json
RUN npm install

COPY . /web
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]

4.3 docker-compose.yml (루트에)
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: skillsdb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/skillsdb
      JWT_SECRET: change-me-please
      ADMIN_USERNAME: admin
      ADMIN_PASSWORD: admin1234!
      AWESOME_LIST_RAW_URL: https://raw.githubusercontent.com/kepano/obsidian-skills/main/README.md
      ANTHROPIC_SKILLS_REPO: anthropics/skills
      GITHUB_TOKEN: ""
      INGEST_MAX_REPOS_PER_RUN: 50
      PARSER_MAX_RAW_SKILLS_PER_RUN: 200
    depends_on:
      - db
    ports:
      - "8000:8000"

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_BASE: http://localhost:8000
    depends_on:
      - api
    ports:
      - "3000:3000"

  worker:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/skillsdb
      JWT_SECRET: change-me-please
      ADMIN_USERNAME: admin
      ADMIN_PASSWORD: admin1234!
      AWESOME_LIST_RAW_URL: https://raw.githubusercontent.com/kepano/obsidian-skills/main/README.md
      ANTHROPIC_SKILLS_REPO: anthropics/skills
      GITHUB_TOKEN: ""
      INGEST_MAX_REPOS_PER_RUN: 50
      PARSER_MAX_RAW_SKILLS_PER_RUN: 200
    depends_on:
      - db
    command: ["bash", "-lc", "alembic upgrade head && python -m app.seed && python -m app.workers.run_all"]

volumes:
  pgdata:

5) “정말 마지막” 실행 방법
5.1 로컬 실행 (완전 한 방)
docker compose up --build


그리고 접속:

Web: http://localhost:3000

API: http://localhost:8000/docs

Admin UI: http://localhost:3000/admin/login

Admin 로그인 기본값:

username: admin
password: admin1234!


운영 흐름:

worker가 raw 수집/파싱/랭킹 생성

Admin → Raw Queue에서 항목 클릭

Preview/Candidates 확인

Approve(새로 등록 or 병합)

Public 사이트에서 바로 노출

6) “이후 단계가 없는 이유” (체크리스트)

 자동 ingest

 자동 parse (SKILL.md)

 운영자 승인/병합

 중복 후보 제공

 popularity 집계

 top10 스냅샷

 Public UI + Admin UI

 Docker compose one-shot