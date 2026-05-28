#!/usr/bin/env bash
# 云服务器「一次性」环境配置（user 账号，无需 root/sudo）
# 用法：bash scripts/server/once-setup-china.sh
# 可选：BASE APP_ROOT REPO_URL

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=service-common.sh
source "$SCRIPT_DIR/service-common.sh"
service_common_init

BASE="${BASE:-/opt/student_service}"
APP_ROOT="${APP_ROOT:-$BASE/software_team}"
REPO_URL="${REPO_URL:-https://github.com/zhuqizhe122/software_team.git}"
VENV_DIR="${VENV_DIR:-$BASE/venv}"
MARKER="$BASE/.setup_done"

ensure_run_as_app_user

echo "==> 基础目录：$BASE（用户 $(whoami)）"
mkdir -p "$BASE/backups" "$UPLOAD_DIR" "$PIP_CACHE" "$NPM_CACHE" "$LOG_DIR"

if [[ ! -d "$APP_ROOT/.git" ]]; then
  echo "==> 克隆仓库到 $APP_ROOT"
  git clone "$REPO_URL" "$APP_ROOT"
else
  echo "==> 仓库已存在：$APP_ROOT"
fi

cd "$APP_ROOT"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "==> 创建 Python 虚拟环境：$VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

export PIP_CACHE_DIR="$PIP_CACHE"
python -m pip install -U pip setuptools wheel
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
pip install -r backend/requirements.txt

if command -v npm >/dev/null 2>&1; then
  npm config set registry https://registry.npmmirror.com
  npm config set cache "$NPM_CACHE"
else
  echo "WARN: 未找到 npm，请安装 Node.js 18+ 后重新运行"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  cp backend/.env.example "$ENV_FILE"
  echo "==> 已生成 $ENV_FILE ，请编辑 DATABASE_URL / AUTH_SECRET 等"
fi

# ---- 用户级 systemd（推荐，无需 root）----
USER_UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_UNIT_DIR"
sed \
  -e "s|@BASE@|$BASE|g" \
  -e "s|@APP_ROOT@|$APP_ROOT|g" \
  -e "s|@VENV_DIR@|$VENV_DIR|g" \
  -e "s|@ENV_FILE@|$ENV_FILE|g" \
  "$SCRIPT_DIR/student-service.user.service" \
  > "$USER_UNIT_DIR/student-service.service"

if command -v systemctl >/dev/null 2>&1; then
  systemctl --user daemon-reload
  systemctl --user enable student-service 2>/dev/null || true
  echo "==> 已安装用户级 systemd：student-service"
  if command -v loginctl >/dev/null 2>&1; then
    loginctl enable-linger "$(whoami)" 2>/dev/null && \
      echo "==> 已 enable-linger，登出后服务仍运行" || \
      echo "WARN: enable-linger 失败（无权限时可改用 restart-backend.sh 或请管理员执行一次 loginctl enable-linger $USER）"
  fi
else
  echo "WARN: 无 systemctl，更新后将使用 scripts/server/restart-backend.sh 管理进程"
fi

chmod +x "$SCRIPT_DIR/update-app.sh" "$SCRIPT_DIR/restart-backend.sh" 2>/dev/null || true

date -Iseconds > "$MARKER"
echo ""
echo "=========================================="
echo "一次性配置完成（user 账号模式）。"
echo "下一步："
echo "  1) 编辑 $ENV_FILE"
echo "  2) 初始化：cd $APP_ROOT && PYTHONPATH=backend python -m app.seed"
echo "  3) 构建并启动：bash scripts/server/update-app.sh"
echo "     或仅构建：bash scripts/server/update-app.sh --build-only"
echo "     然后：systemctl --user start student-service"
echo "以后更新：bash scripts/server/update-app.sh"
echo "=========================================="
