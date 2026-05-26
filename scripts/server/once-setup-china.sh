#!/usr/bin/env bash
# 云服务器「一次性」环境配置（中国大陆镜像 + 持久缓存）
# 用法：sudo bash scripts/server/once-setup-china.sh
# 可选环境变量：APP_ROOT BASE REPO_URL

set -euo pipefail

BASE="${BASE:-/opt/student_service}"
APP_ROOT="${APP_ROOT:-$BASE/software_team}"
REPO_URL="${REPO_URL:-https://github.com/zhuqizhe122/software_team.git}"
VENV_DIR="${VENV_DIR:-$BASE/venv}"
UPLOAD_DIR="${UPLOAD_DIR:-$BASE/uploads}"
ENV_FILE="${ENV_FILE:-$BASE/.env}"
PIP_CACHE="${PIP_CACHE:-$BASE/.cache/pip}"
NPM_CACHE="${NPM_CACHE:-$BASE/.npm-cache}"
MARKER="$BASE/.setup_done"

echo "==> 基础目录：$BASE"
mkdir -p "$BASE/backups" "$UPLOAD_DIR" "$PIP_CACHE" "$NPM_CACHE"
chmod 755 "$BASE"

if [[ ! -d "$APP_ROOT/.git" ]]; then
  echo "==> 克隆仓库到 $APP_ROOT"
  git clone "$REPO_URL" "$APP_ROOT"
else
  echo "==> 仓库已存在：$APP_ROOT"
fi

cd "$APP_ROOT"

# ---- Python venv（只创建一次，以后更新不重建）----
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

# ---- Node 镜像与缓存（全局一次，以后 npm install 复用缓存）----
if command -v npm >/dev/null 2>&1; then
  npm config set registry https://registry.npmmirror.com
  npm config set cache "$NPM_CACHE"
  echo "npm 缓存目录：$NPM_CACHE"
else
  echo "WARN: 未找到 npm，请安装 Node.js 18+ 后重新运行本脚本"
fi

# ---- .env 模板（不覆盖已有）----
if [[ ! -f "$ENV_FILE" ]]; then
  cp backend/.env.example "$ENV_FILE"
  echo "==> 已生成 $ENV_FILE ，请编辑 DATABASE_URL / AUTH_SECRET 等"
fi

# ---- systemd 服务（可选）----
UNIT_DST="/etc/systemd/system/student-service.service"
if [[ -w /etc/systemd/system || $(id -u) -eq 0 ]]; then
  sed \
    -e "s|@BASE@|$BASE|g" \
    -e "s|@APP_ROOT@|$APP_ROOT|g" \
    -e "s|@VENV_DIR@|$VENV_DIR|g" \
    -e "s|@ENV_FILE@|$ENV_FILE|g" \
    scripts/server/student-service.service \
    > "$UNIT_DST"
  systemctl daemon-reload
  systemctl enable student-service
  echo "==> 已安装 systemd 单元：student-service"
fi

date -Iseconds > "$MARKER"
echo ""
echo "=========================================="
echo "一次性配置完成。"
echo "下一步："
echo "  1) 编辑 $ENV_FILE"
echo "  2) 初始化数据库：cd $APP_ROOT && PYTHONPATH=backend python -m app.seed"
echo "  3) 构建前端：bash scripts/server/update-app.sh --build-only"
echo "  4) 启动：sudo systemctl start student-service"
echo "以后更新只需：bash scripts/server/update-app.sh"
echo "=========================================="
