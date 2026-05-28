# 云服务器安全更新指南（含回滚）

目标：`http://10.10.0.21/`。**无 root 账号** 时请先读 [deploy-user-account.md](./deploy-user-account.md)，全程用 `user` 执行 `bash scripts/server/update-app.sh`，**不要用 sudo**。

## 更新前：先备份（必做）

在服务器 SSH 登录后执行（路径按实际调整，常见为 `/opt/student_service/software_team`）：

```bash
export APP_ROOT=/opt/student_service/software_team
export BACKUP_ROOT=/opt/student_service/backups
export STAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_ROOT/$STAMP"
cd "$APP_ROOT"

# 1) 记录当前 Git 版本（回滚用）
git rev-parse HEAD > "$BACKUP_ROOT/$STAMP/git_commit.txt"

# 2) 备份环境变量（含数据库密码，勿泄露）
cp /opt/student_service/.env "$BACKUP_ROOT/$STAMP/.env" 2>/dev/null || \
  cp "$APP_ROOT/../.env" "$BACKUP_ROOT/$STAMP/.env" 2>/dev/null || true

# 3) 备份上传目录（用户附件）
cp -a /opt/student_service/uploads "$BACKUP_ROOT/$STAMP/uploads" 2>/dev/null || true

# 4) 备份数据库（从 .env DATABASE_URL 读取；无权限则跳过）
bash -c 'source scripts/server/service-common.sh && service_common_init && APP_ROOT='"$APP_ROOT"' pg_dump_backup '"$BACKUP_ROOT/$STAMP/student_service.sql"'"

# 5) 备份当前前端静态文件（可选）
cp -a "$APP_ROOT/web/dist" "$BACKUP_ROOT/$STAMP/web_dist" 2>/dev/null || true

echo "备份完成：$BACKUP_ROOT/$STAMP"
cat "$BACKUP_ROOT/$STAMP/git_commit.txt"
```

记下输出的 **commit 哈希** 和 **备份目录名**，出问题就靠它们恢复。

## 标准更新流程

```bash
export APP_ROOT=/opt/student_service/software_team
cd "$APP_ROOT"

# 一键更新（备份 + fetch/reset + 依赖 + migrate + build + 重启）
bash scripts/server/update-app.sh
```

脚本内部使用 `git reset --hard origin/main`，**不要用 sudo**，避免 `.git` 权限被 root 占用。

若需手动分步：

```bash
git fetch origin
git reset --hard origin/main
source /opt/student_service/venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend python -m app.db.migrate
cd web && VITE_API_BASE=/api npm run build && cd ..
systemctl --user restart student-service   # 或 bash scripts/server/restart-backend.sh
```

## 更新后验证

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1/health
BASE_URL=http://10.10.0.21 ./scripts/smoke-backend.sh
```

浏览器验证：

1. 打开 `http://10.10.0.21/`，右上角**不应**出现 Mock 切换（生产包固定 Remote）。
2. 学号 + `Stu@学号后6位` 登录，角色由后端自动绑定。
3. 工作台 → 导出 CSV、知识库、审批各点一次。

## 回滚方案（改坏了立刻做）

### A. 只回滚代码（最快，约 1 分钟）

```bash
export APP_ROOT=/opt/student_service/software_team
export OLD_COMMIT=<备份目录里 git_commit.txt 的内容>
cd "$APP_ROOT"
git fetch origin
git checkout "$OLD_COMMIT"

source /opt/student_service/venv/bin/activate
pip install -r backend/requirements.txt
cd web && npm install && VITE_API_BASE=/api npm run build && cd ..
systemctl --user restart student-service || bash scripts/server/restart-backend.sh
```

### B. 回滚前端静态文件（仅页面坏了）

```bash
export BACKUP=/opt/student_service/backups/<STAMP>
rm -rf /opt/student_service/software_team/web/dist
cp -a "$BACKUP/web_dist" /opt/student_service/software_team/web/dist
# Nginx 由管理员重载；user 账号通常无需操作
```

### C. 回滚数据库（迁移搞坏了才用）

```bash
export BACKUP=/opt/student_service/backups/<STAMP>
# 需数据库管理员权限；user 账号可能无法执行，联系运维
psql "$DATABASE_URL" < "$BACKUP/student_service.sql"
systemctl --user restart student-service || bash scripts/server/restart-backend.sh
```

### D. 回滚环境变量

```bash
cp /opt/student_service/backups/<STAMP>/.env /opt/student_service/.env
systemctl --user restart student-service || bash scripts/server/restart-backend.sh
```

## 注意事项

| 操作 | 风险 | 建议 |
| --- | --- | --- |
| `git pull` | 低 | 先备份 commit 哈希 |
| `pip install` | 低 | 与代码版本一起回滚 commit 即可 |
| `app.db.migrate` | 中 | 先 pg_dump；迁移一般只加列 |
| `app.seed` 全量重跑 | **高** | **更新时不要随便 seed**，会覆盖演示数据 |
| 改 Nginx | 中 | `nginx -t` 通过再 reload |
| 改 `.env` 里 DATABASE_URL | 高 | 单独备份 .env |

## 找不到 systemd 服务名时

```bash
systemctl --user list-units --type=service | grep -i student
systemctl list-units --type=service | grep -i student
ps aux | grep uvicorn
cat /opt/student_service/student-service.pid 2>/dev/null
```

常见启动命令（无 systemd 时）：

```bash
cd /opt/student_service/software_team
source /opt/student_service/venv/bin/activate
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 与队友协作

- 更新前在群里说一声「正在更新云服务器」。
- 备份目录保留至少 7 天。
- 若验收/demo 在即，优先用 **方案 A** 回滚，不要慌删库。

更多首次部署细节见 [deploy-cloud.md](./deploy-cloud.md)。
