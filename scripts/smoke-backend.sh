#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
BASE_URL="${BASE_URL:-}"

if [[ -n "$BASE_URL" ]]; then
  python3 - <<PY
import json, os, sys, urllib.error, urllib.request

base = os.environ.get("BASE_URL", "").rstrip("/")
password = os.environ.get("SMOKE_PASSWORD", "Stu@201581")
teacher_password = os.environ.get("SMOKE_TEACHER_PASSWORD", "Stu@200999")

def call(method, path, body=None, headers=None):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", **(headers or {})},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.status, res.read().decode()

for path in ("/health", "/api/runtime"):
    status, _ = call("GET", path)
    print("GET", path, status)
    if status >= 400:
        sys.exit(1)

status, raw = call("POST", "/api/auth/login", {"studentId": "2024201581", "password": password})
print("POST", "/api/auth/login", status)
if status >= 400:
    sys.exit(raw)
token = json.loads(raw)["token"]
status, raw = call("GET", "/api/session", headers={"Authorization": f"Bearer {token}"})
print("GET", "/api/session bearer", status)
if status >= 400:
    sys.exit(raw)
status, raw = call("POST", "/api/auth/refresh", headers={"Authorization": f"Bearer {token}"})
print("POST", "/api/auth/refresh", status)
if status >= 400:
    sys.exit(raw)
status, raw = call("POST", "/api/auth/login", {"studentId": "2022200999", "password": teacher_password})
print("POST", "/api/auth/login teacher", status)
if status >= 400:
    sys.exit(raw)
t_token = json.loads(raw)["token"]
for path in ("/api/workbench/applications/export", "/api/audit/logs/export"):
    status, raw = call("GET", path, headers={"Authorization": f"Bearer {t_token}"})
    print("GET", path, status)
    if status >= 400:
        sys.exit(raw)
PY
  exit 0
fi

PYTHONPATH=backend python3 - <<'PY'
import os

os.environ.setdefault("AUTH_MODE", "header")
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    for method, path in [("GET", "/health"), ("GET", "/api/runtime"), ("GET", "/api/knowledge")]:
        res = client.request(method, path)
        print(method, path, res.status_code)
        if res.status_code >= 400:
            raise SystemExit(res.text)

    login = client.post("/api/auth/login", json={"studentId": "2024201581", "password": "Stu@201581"})
    print("POST", "/api/auth/login", login.status_code)
    if login.status_code >= 400:
        raise SystemExit(login.text)
    token = login.json()["token"]
    session = client.get("/api/session", headers={"Authorization": f"Bearer {token}"})
    print("GET", "/api/session bearer", session.status_code)
    if session.status_code >= 400:
        raise SystemExit(session.text)

    refresh = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {token}"})
    print("POST", "/api/auth/refresh", refresh.status_code)
    if refresh.status_code >= 400:
        raise SystemExit(refresh.text)

    teacher = client.post("/api/auth/login", json={"studentId": "2022200999", "password": os.environ.get("SMOKE_TEACHER_PASSWORD", "Stu@200999")})
    print("POST", "/api/auth/login teacher", teacher.status_code)
    if teacher.status_code >= 400:
        raise SystemExit(teacher.text)
    t_token = teacher.json()["token"]
    for method, path in [
        ("GET", "/api/knowledge/export"),
        ("GET", "/api/workbench/applications/export"),
        ("GET", "/api/audit/logs/export"),
        ("GET", "/api/workbench/party/progress"),
    ]:
        res = client.request(method, path, headers={"Authorization": f"Bearer {t_token}"})
        print(method, path, res.status_code)
        if res.status_code >= 400:
            raise SystemExit(res.text)
PY
