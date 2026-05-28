# 无 root 账号部署（仅 user 用户）

适用：`10.10.0.21` 等 **只有普通用户 `user`、无 root/sudo** 的虚拟机。

## 原则

| 操作 | 做法 |
|------|------|
| Git 拉代码 | **不要用 sudo**，用 `bash scripts/server/update-app.sh` |
| 后端进程 | 优先 `systemctl --user`；否则 `scripts/server/restart-backend.sh` |
| Nginx | 通常由镜像/管理员预装，**user 不改 80 端口配置** |
| 数据库备份 | 脚本读 `.env` 里 `DATABASE_URL` 执行 `pg_dump` |

## 一次性修复（若曾用 sudo 导致 .git 权限错乱）

若 `git fetch` 报 `Permission denied` 且 `.git` 属主为 root，需 **虚拟机管理员** 执行一次（user 无法自行 chown）：

```bash
chown -R user:user /opt/student_service
```

之后 **永远不要再 sudo 跑 update 脚本**。

## 日常更新（标准）

```bash
cd /opt/student_service/software_team
bash scripts/server/update-app.sh
```

脚本会：备份 → `git fetch` + `reset --hard origin/main`（避免 merge 冲突）→ migrate → 构建前端 → 重启后端。

## 手动同步代码（仅 git 步骤）

```bash
cd /opt/student_service/software_team
bash -c 'source scripts/server/service-common.sh && service_common_init && APP_ROOT=$PWD ensure_git_writable && git_sync_main'
```

## 重启后端

```bash
# 方式 1：用户 systemd（推荐）
systemctl --user restart student-service
systemctl --user status student-service

# 方式 2：无 systemd 单元
bash scripts/server/restart-backend.sh
```

## 查看日志

```bash
journalctl --user -u student-service -n 50 --no-pager
# 或
tail -n 50 /opt/student_service/logs/student-service.log
```

## 首次安装

```bash
bash scripts/server/once-setup-china.sh
# 编辑 /opt/student_service/.env
cd /opt/student_service/software_team
PYTHONPATH=backend python -m app.seed   # 仅首次
bash scripts/server/update-app.sh
systemctl --user start student-service   # 若尚未启动
```

## 与 root 版差异

- 不再使用 `sudo systemctl restart student-service`
- 不再使用 `sudo -u postgres pg_dump`
- `update-app.sh` 用 **hard reset** 替代 `git pull`，避免服务器本地脏改导致冲突

完整回滚与验收见 [cloud-update-safe.md](./cloud-update-safe.md)。
