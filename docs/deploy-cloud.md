# 云服务器部署说明

目标环境：`http://10.10.0.21/`（内网）。Web 为唯一交付端，小程序代码已冻结。

## 1. 目录结构（建议）

```text
/opt/student_service/
  software_team/          # Git 仓库
  venv/                   # Python 虚拟环境
  uploads/                # 持久化上传目录（挂载卷）
  .env                    # 后端环境变量（勿提交 Git）
```

## 2. 后端

```bash
cd /opt/student_service/software_team
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r backend/requirements.txt

cp backend/.env.example ../.env
# 编辑 ../.env，至少修改：
# AUTH_MODE=token
# AUTH_SECRET=<随机长字符串>
# DATABASE_URL=...
# CORS_ORIGINS=http://10.10.0.21
# UPLOAD_DIR=/opt/student_service/uploads
# ENABLE_SCHEDULER=true

PYTHONPATH=backend python3 -m app.seed   # 首次灌种子数据
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Kingbase 探针

```bash
PYTHONPATH=backend python3 scripts/probe-kingbase.py "kingbase+psycopg://user:pass@host:5432/dbname"
```

若连接成功，将 `DATABASE_URL` 改为 Kingbase 连接串；若失败，可继续使用 PostgreSQL，并在答辩材料中说明「Kingbase 环境待学院侧开通」。

## 3. 前端

```bash
cd web
npm install
VITE_API_BASE=/api npm run build
# 产物在 web/dist，由 Nginx 托管
```

生产构建默认 **Remote 模式**，API 基址为 `/api`（同源反代，无需 CORS 配置浏览器侧）。

## 4. Nginx 示例

```nginx
server {
    listen 80;
    server_name 10.10.0.21;

    root /opt/student_service/software_team/web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

## 5. 登录说明

- 认证方式：**学号 + 个人密码 + 角色**，JWT Token（`Authorization: Bearer`）。
- 种子数据初始密码规则：`Stu@` + 学号后 6 位（例：学号 `2024201581` → `Stu@201581`）。
- 管理老师可在工作台 **重置学生密码**。
- 导入学生时 CSV/XLSX 可带「初始密码」列。

## 6. 冒烟检查

```bash
BASE_URL=http://10.10.0.21 ./scripts/smoke-backend.sh
```

## 7. 定时任务

后端内置 APScheduler（可通过 `ENABLE_SCHEDULER=false` 关闭）：

- 每 5 分钟：派发到期定时通知
- 每 6 小时：刷新党团阶段提醒任务

亦可使用 systemd timer 调用 `POST /api/workbench/notices/scheduled/dispatch`。
