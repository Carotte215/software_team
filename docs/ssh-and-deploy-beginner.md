# 傻瓜式：从 Windows 连 SSH 到更新云服务器

适用：你只有 **IP 地址** 和 **SSH 密码**，服务器是 Linux（常见 Ubuntu / CentOS）。  
目标：把 GitHub 上最新代码更新到 `http://10.10.0.21/`（IP 换成你的）。

---

## 一、先搞懂三个词（30 秒）

| 词 | 是什么 | 类比 |
| --- | --- | --- |
| **SSH** | 远程登录服务器的通道 | 微信远程控制同学的电脑 |
| **终端 / 命令行** | 用文字发指令 | 不用鼠标，打字让电脑执行 |
| **服务器** | 24 小时开着的 Linux 电脑 | 放在机房的「全班共用的电脑」 |

你要做的事：**在自己电脑上打开 SSH → 登录服务器 → 复制粘贴几条命令 → 等它跑完**。

---

## 二、Windows 连接 SSH（推荐 PowerShell）

### 2.1 打开 PowerShell

1. 按 `Win + S`，搜索 **PowerShell** 或 **终端**
2. 打开 **Windows PowerShell**（普通窗口即可）

### 2.2 确认有 SSH 客户端

粘贴后回车：

```powershell
ssh -V
```

若显示 `OpenSSH_xxx` 则可用。  
若提示找不到命令：  
**设置 → 应用 → 可选功能 → 添加功能 → OpenSSH 客户端**。

### 2.3 连接服务器

把下面命令里的内容改成你的：

```powershell
ssh 用户名@服务器IP
```

**示例**（常见写法，问部署同学确认用户名）：

```powershell
ssh root@10.10.0.21
# 或
ssh ubuntu@10.10.0.21
```

回车后：

1. **第一次**会问 `Are you sure you want to continue connecting (yes/no)?`  
   → 输入 `yes` 回车  
2. 提示 `password:`  
   → **输入 SSH 密码**（屏幕上**不会显示任何字符**，这是正常的）  
   → 输完直接回车  

成功标志：提示符变成类似 `root@xxx:~#` 或 `ubuntu@xxx:~$`。

### 2.4 断开连接

```bash
exit
```

### 2.5 密码老错？

- 确认 Caps Lock 没开
- 密码从队友处**复制粘贴**（PowerShell 里右键可粘贴）
- 用户名不对（`root` / `ubuntu` / 自定义）— 问当初部署的人

### 2.6 备选：PuTTY（图形界面）

1. 下载 [PuTTY](https://www.putty.org/)  
2. Host Name 填 IP，Port `22`，Connection type 选 SSH  
3. Open → 输入用户名和密码  

---

## 三、登录后：找到项目在哪

粘贴：

```bash
find /opt /home /var/www -maxdepth 4 -name software_team -type d 2>/dev/null
```

若输出类似 `/opt/student_service/software_team`，后面命令都用这个路径。

```bash
export APP_ROOT=/opt/student_service/software_team
cd "$APP_ROOT"
pwd
git log -1 --oneline
```

能看到 `60d7686` 之类说明是 Git 项目。

**若 find 找不到**：问队友项目目录，或首次部署见下文「五、首次部署」。

---

## 四、日常更新（推荐：一条脚本）

项目已提供 **带国内镜像 + 缓存** 的更新脚本，**依赖没改时不会重复下大包**。

### 4.1 更新步骤（复制整段）

```bash
export APP_ROOT=/opt/student_service/software_team   # 改成你的路径
cd "$APP_ROOT"

# 拉取含脚本的最新代码（若脚本报不存在，先 git pull 一次）
git pull origin main

# 执行安全更新：自动备份 + pull + 按需 pip/npm + 构建 + 重启
sudo bash scripts/server/update-app.sh
```

### 4.2 脚本帮你做了什么

| 步骤 | 说明 |
| --- | --- |
| 备份 | 当前 Git 版本、.env、uploads、数据库、旧前端 |
| `git pull` | 从 GitHub 拉代码 |
| `pip install` | **仅当** `requirements.txt` 变化时才执行 |
| `npm install` | **仅当** `package-lock.json` 变化时才执行 |
| `npm run build` | 每次都会（很快，几秒～几十秒） |
| 重启服务 | `systemctl restart student-service` |

### 4.3 验证

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1/health
```

浏览器打开 `http://你的IP/`，用学号 + `Stu@学号后6位` 登录。

### 4.4 改坏了怎么回滚

见 [cloud-update-safe.md](./cloud-update-safe.md)，或：

```bash
export BACKUP=/opt/student_service/backups/这里填备份文件夹名
export OLD=$(cat "$BACKUP/git_commit.txt")
cd /opt/student_service/software_team
git checkout "$OLD"
sudo bash scripts/server/update-app.sh --no-backup
```

---

## 五、首次部署（服务器上还没有项目）

> 若队友已经部署过，**跳过本节**，只做第四节。

登录 SSH 后：

```bash
# 安装基础工具（Ubuntu/Debian）
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nodejs npm postgresql-client

# 克隆 + 一次性配置（镜像、venv 缓存、npm 缓存、systemd）
sudo mkdir -p /opt/student_service
cd /opt/student_service
sudo git clone https://github.com/zhuqizhe122/software_team.git
cd software_team
sudo bash scripts/server/once-setup-china.sh
```

编辑环境变量（**必做**）：

```bash
sudo nano /opt/student_service/.env
```

至少改这几项（按服务器实际情况）：

```ini
AUTH_MODE=token
AUTH_SECRET=随便一长串随机字母数字
DATABASE_URL=postgresql+psycopg://student_service:你的密码@127.0.0.1:5432/student_service
CORS_ORIGINS=http://10.10.0.21
UPLOAD_DIR=/opt/student_service/uploads
ENABLE_SCHEDULER=true
AUTO_CREATE_TABLES=true
```

`nano` 用法：`Ctrl+O` 保存，`Ctrl+X` 退出。

初始化数据库（**仅首次**）：

```bash
cd /opt/student_service/software_team
source /opt/student_service/venv/bin/activate
PYTHONPATH=backend python -m app.seed
```

构建并启动：

```bash
sudo bash scripts/server/update-app.sh --build-only
sudo systemctl start student-service
sudo systemctl status student-service
```

Nginx 若队友已配好通常不用动；首次需参考 [deploy-cloud.md](./deploy-cloud.md)。

---

## 六、为什么不会每次都下「大包」（原理简述）

| 机制 | 位置 | 作用 |
| --- | --- | --- |
| **Python venv** | `/opt/student_service/venv` | 虚拟环境只建一次，更新不删 |
| **pip 缓存** | `/opt/student_service/.cache/pip` | 下过的 wheel 本地复用 |
| **清华 pip 源** | 一次性脚本已配置 | 国内下载快 |
| **npm 缓存** | `/opt/student_service/.npm-cache` | 下过的包本地复用 |
| **npmmirror 源** | 一次性脚本已配置 | 原淘宝镜像，国内快 |
| **哈希比对** | `.requirements.txt.hash` 等 | 依赖文件没变就跳过 install |

**每次更新仍会 `npm run build`**（重新打包 JS/CSS），但通常比 `npm install` 快得多。

---

## 七、中国大陆 GitHub 拉不动时

在服务器上（一次性）：

```bash
git config --global url."https://ghproxy.net/https://github.com".insteadOf https://github.com
```

然后再 `git pull`。  
若仍失败，让能访问 GitHub 的同学在你电脑上 push 后，你在服务器多试几次，或改用 Gitee 镜像（需自行同步仓库）。

---

## 八、常见问题

**Q：输入密码没反应？**  
A：正常，继续输完按回车。

**Q：`Permission denied`？**  
A：密码错或用户名错。

**Q：`git pull` 要用户名密码？**  
A：仓库是 public 一般不需要；若 private 需配置 GitHub Token 或 SSH Key。

**Q：`systemctl: command not found`？**  
A：可能是精简系统，用手动启动：  
`source /opt/student_service/venv/bin/activate && cd /opt/student_service/software_team && PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000`

**Q：能更新但页面没变？**  
A：浏览器 `Ctrl+F5` 强刷；确认 `web/dist` 已重建。

**Q：不敢动怕搞坏？**  
A：先跑 `update-app.sh`（自带备份），有问题用第四节 4.4 回滚。

---

## 九、你要记住的最短流程

```
Windows PowerShell → ssh 用户@IP → 输入密码
→ cd /opt/student_service/software_team
→ sudo bash scripts/server/update-app.sh
→ 浏览器打开 IP 测试
```

更详细的回滚见 [cloud-update-safe.md](./cloud-update-safe.md)。
