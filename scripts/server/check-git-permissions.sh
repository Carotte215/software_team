#!/usr/bin/env bash
# 诊断 .git 权限（无 root 环境）；若属主为 root 需虚拟机管理员一次性 chown
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/student_service/software_team}"
cd "$APP_ROOT"

echo "当前用户：$(whoami) ($(id))"
echo "检查 $APP_ROOT/.git ..."

if [[ ! -d .git ]]; then
  echo "ERROR: 不是 git 仓库"
  exit 1
fi

ls -la .git/FETCH_HEAD .git/index 2>/dev/null || true

if [[ -w .git ]] && [[ -w .git/FETCH_HEAD 2>/dev/null || ! -e .git/FETCH_HEAD ]]; then
  echo "OK: .git 可写，可直接 bash scripts/server/update-app.sh"
  exit 0
fi

echo ""
echo "ERROR: .git 不可写，常见原因：曾用 sudo 运行 git/pull/update。"
echo ""
echo "若虚拟机管理员可登录（或有 root），请执行一次："
echo "  chown -R $(whoami):$(id -gn) $APP_ROOT"
echo ""
echo "修复后请永远使用："
echo "  bash scripts/server/update-app.sh"
echo "不要使用 sudo。"
exit 1
