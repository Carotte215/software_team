#!/usr/bin/env bash
# 无 systemd 时用 PID 文件重启后端（仅 user 账号，无需 root）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=service-common.sh
source "$SCRIPT_DIR/service-common.sh"
service_common_init
APP_ROOT="${APP_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
ensure_run_as_app_user

mkdir -p "$LOG_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if [[ -f "$PID_FILE" ]]; then
  old_pid=$(cat "$PID_FILE" 2>/dev/null || true)
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "==> 停止旧进程 PID $old_pid"
    kill "$old_pid" 2>/dev/null || true
    sleep 2
    kill -0 "$old_pid" 2>/dev/null && kill -9 "$old_pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
fi

echo "==> 启动 uvicorn（后台，日志 $LOG_DIR/student-service.log）"
cd "$APP_ROOT"
export PYTHONPATH="$APP_ROOT/backend"
nohup "$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 \
  >>"$LOG_DIR/student-service.log" 2>&1 &
echo $! > "$PID_FILE"
sleep 2
if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "==> 已启动 PID $(cat "$PID_FILE")"
else
  echo "ERROR: 启动失败，请查看 $LOG_DIR/student-service.log"
  exit 1
fi
