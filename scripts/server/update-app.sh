#!/usr/bin/env bash
# 日常安全更新（备份 + pull + 按需安装依赖 + 构建 + 重启）
# 用法：bash scripts/server/update-app.sh
#       bash scripts/server/update-app.sh --build-only   # 只构建前端
#       bash scripts/server/update-app.sh --no-backup    # 跳过备份（不推荐）

set -euo pipefail

BASE="${BASE:-/opt/student_service}"
APP_ROOT="${APP_ROOT:-$BASE/software_team}"
VENV_DIR="${VENV_DIR:-$BASE/venv}"
UPLOAD_DIR="${UPLOAD_DIR:-$BASE/uploads}"
ENV_FILE="${ENV_FILE:-$BASE/.env}"
PIP_CACHE="${PIP_CACHE:-$BASE/.cache/pip}"
NPM_CACHE="${NPM_CACHE:-$BASE/.npm-cache}"
BACKUP_ROOT="${BACKUP_ROOT:-$BASE/backups}"
STAMP=$(date +%Y%m%d_%H%M%S)
DO_BACKUP=1
BUILD_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --no-backup) DO_BACKUP=0 ;;
    --build-only) BUILD_ONLY=1 ;;
  esac
done

cd "$APP_ROOT"
export PIP_CACHE_DIR="$PIP_CACHE"
export npm_config_cache="$NPM_CACHE"
export npm_config_registry="${npm_config_registry:-https://registry.npmmirror.com}"

hash_file() {
  if command -v md5sum >/dev/null 2>&1; then md5sum "$1" | awk '{print $1}';
  elif command -v md5 >/dev/null 2>&1; then md5 -q "$1";
  else cksum "$1" | awk '{print $1}'; fi
}

need_pip=0
need_npm=0
REQ_HASH_FILE="$BASE/.requirements.txt.hash"
LOCK_HASH_FILE="$BASE/.package-lock.json.hash"

if [[ "$BUILD_ONLY" -eq 0 ]]; then
  if [[ "$DO_BACKUP" -eq 1 ]]; then
    echo "==> 备份到 $BACKUP_ROOT/$STAMP"
    mkdir -p "$BACKUP_ROOT/$STAMP"
    git rev-parse HEAD > "$BACKUP_ROOT/$STAMP/git_commit.txt"
    [[ -f "$ENV_FILE" ]] && cp "$ENV_FILE" "$BACKUP_ROOT/$STAMP/.env"
    [[ -d "$UPLOAD_DIR" ]] && cp -a "$UPLOAD_DIR" "$BACKUP_ROOT/$STAMP/uploads" 2>/dev/null || true
    [[ -d web/dist ]] && cp -a web/dist "$BACKUP_ROOT/$STAMP/web_dist" 2>/dev/null || true
    if command -v pg_dump >/dev/null 2>&1; then
      pg_dump student_service > "$BACKUP_ROOT/$STAMP/student_service.sql" 2>/dev/null || \
        sudo -u postgres pg_dump student_service > "$BACKUP_ROOT/$STAMP/student_service.sql" 2>/dev/null || \
        echo "WARN: pg_dump 失败，请手动备份数据库"
    fi
    echo "备份 commit: $(cat "$BACKUP_ROOT/$STAMP/git_commit.txt")"
  fi

  echo "==> 拉取最新代码"
  git fetch origin
  git pull origin main

  current_req=$(hash_file backend/requirements.txt)
  if [[ ! -f "$REQ_HASH_FILE" ]] || [[ "$(cat "$REQ_HASH_FILE")" != "$current_req" ]]; then
    need_pip=1
  fi
fi

current_lock=$(hash_file web/package-lock.json)
if [[ ! -f "$LOCK_HASH_FILE" ]] || [[ "$(cat "$LOCK_HASH_FILE")" != "$current_lock" ]]; then
  need_npm=1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if [[ "$need_pip" -eq 1 ]]; then
  echo "==> requirements.txt 有变化，更新 Python 依赖（使用 pip 缓存）"
  pip install -r backend/requirements.txt
  echo "$current_req" > "$REQ_HASH_FILE"
else
  echo "==> Python 依赖无变化，跳过 pip install"
fi

if [[ "$BUILD_ONLY" -eq 0 ]]; then
  echo "==> 数据库轻量迁移"
  PYTHONPATH=backend python -m app.db.migrate
fi

if [[ "$need_npm" -eq 1 ]]; then
  echo "==> package-lock.json 有变化，npm install（使用 npm 缓存）"
  cd web
  npm install
  cd ..
  echo "$current_lock" > "$LOCK_HASH_FILE"
else
  echo "==> 前端依赖无变化，跳过 npm install"
fi

echo "==> 构建前端"
cd web
VITE_API_BASE=/api npm run build
cd ..

if [[ "$BUILD_ONLY" -eq 0 ]]; then
  if systemctl is-active --quiet student-service 2>/dev/null; then
    echo "==> 重启 student-service"
    sudo systemctl restart student-service
    sudo systemctl status student-service --no-pager || true
  else
    echo "WARN: 未检测到 systemd 服务 student-service，请手动重启 uvicorn"
  fi

  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "==> 健康检查通过"
  else
    echo "WARN: /health 未响应，请检查日志：journalctl -u student-service -n 50"
  fi
fi

echo "==> 完成"
