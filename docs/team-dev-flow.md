# 开发与更新命令速查

## 1. 基本信息

```text
GitHub 仓库：git@github.com:zhuqizhe122/software_team.git
线上地址：http://10.10.0.21/
服务器登录用户：user
服务器项目目录：/opt/student_service/software_team
服务器虚拟环境：/opt/student_service/venv
服务器环境变量：/opt/student_service/.env
```

## 2. 本地开发目录

项目拉下来后的根目录就是：

```text
software_team/
```

主要目录：

```text
web/       前端 Vue 3 + Vite
backend/   后端 FastAPI
scripts/   启动与辅助脚本
docs/      说明文档
```

## 3. 本地配置文件

后端会读取下面两个位置之一：

```text
项目根目录/.env
backend/.env
```

参考模板：

```text
backend/.env.example
```

本地最常用配置：

```text
DATABASE_URL=postgresql+psycopg://student_service:student_service@127.0.0.1:5432/student_service
CORS_ORIGINS=http://127.0.0.1:5177,http://localhost:5177,http://10.10.0.21
AUTH_MODE=token
AUTH_SECRET=自己填
UPLOAD_DIR=backend/storage/uploads
```

## 4. 第一次安装依赖

### Windows

在项目根目录执行：

```powershell
.\scripts\setup-local.ps1
```

### Linux / macOS

在项目根目录执行：

```bash
pip install -r backend/requirements.txt
cd web && npm install && cd ..
```

## 5. 第一次初始化数据

### Windows

```powershell
$env:PYTHONPATH="backend"
python -m app.seed
```

### Linux / macOS

```bash
PYTHONPATH=backend python -m app.seed
```

## 6. 本地启动命令

### 启动后端

Windows：

```powershell
.\scripts\dev-backend.ps1
```

Linux / macOS：

```bash
./scripts/dev-backend.sh
```

### 启动前端

Windows：

```powershell
.\scripts\dev-web.ps1
```

Linux / macOS：

```bash
./scripts/dev-web.sh
```

## 7. 本地访问地址

```text
前端：http://127.0.0.1:5177/
后端 API：http://127.0.0.1:8000/api
健康检查：http://127.0.0.1:8000/health
接口文档：http://127.0.0.1:8000/docs
```

## 8. 常用测试账号

默认密码规则：

```text
Stu@ + 学号后 6 位
```

```text
学生：2024201581 / Stu@201581
三级协同管理者：2023200444 / Stu@200444
管理老师：2022200999 / Stu@200999
学院领导：2024210888 / Stu@210888
```

## 9. 本地更新代码

先拉最新代码：

```bash
git checkout main
git pull origin main
```

改完后提交：

```bash
git status
git add .
git commit -m "你的提交说明"
git push origin main
```

## 10. 本地检查命令

后端语法检查：

```bash
python -m compileall backend/app
```

前端构建检查：

```bash
cd web
npm run build
cd ..
```

接口冒烟检查：

```bash
./scripts/smoke-backend.sh
```

## 11. 服务器更新流程

先 SSH 登录服务器：

```bash
ssh user@10.10.0.21
```

进入项目目录：

```bash
cd /opt/student_service/software_team
```

确认远端是 SSH：

```bash
git remote -v
```

正常更新：

```bash
bash scripts/server/update-app.sh
```

如果只是 GitHub 拉取出问题，可以分开执行：

```bash
git fetch origin
git reset --hard origin/main
bash scripts/server/update-app.sh --skip-git
```

## 12. 服务器更新后检查

后端健康检查：

```bash
curl -i http://127.0.0.1:8000/health
```

系统服务状态：

```bash
sudo systemctl status student-service
```

系统服务日志：

```bash
sudo journalctl -u student-service -n 50 --no-pager -l
```

## 13. 已忽略的本地内容

仓库已忽略这些内容，不需要提交：

```text
.env
node_modules/
dist/
build/
backend/storage/uploads/
党团平台官方文件/
党团平台文件 2/
```
