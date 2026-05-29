# 组内本地开发更新说明

本文档只说明组员在自己电脑上的开发与更新流程，不涉及云端部署。

## 1. 先明确协作方式

- 平时开发以 GitHub 仓库为准
- 每个人都在自己电脑上拉代码、修改、测试、提交
- 不直接在别人的电脑或服务器代码目录里开发
- 提交前先同步主分支最新代码，减少冲突

## 2. 第一次拉项目

先克隆仓库：

```bash
git clone git@github.com:zhuqizhe122/software_team.git
cd software_team
```

如果是 Windows，推荐使用 PowerShell。

## 3. 第一次本地启动

### Windows

```powershell
.\scripts\setup-local.ps1
$env:PYTHONPATH="backend"
python -m app.seed
.\scripts\dev-backend.ps1
```

新开一个终端：

```powershell
.\scripts\dev-web.ps1
```

### Linux / macOS

```bash
pip install -r backend/requirements.txt
cd web && npm install && cd ..
PYTHONPATH=backend python -m app.seed
./scripts/dev-backend.sh
```

新开一个终端：

```bash
./scripts/dev-web.sh
```

启动后访问：

```text
前端：http://127.0.0.1:5177/
后端：http://127.0.0.1:8000/api
接口文档：http://127.0.0.1:8000/docs
```

## 4. 平时开始开发前

每次准备开始改代码前，先同步最新代码：

```bash
git checkout main
git pull origin main
```

如果你们组内使用自己的功能分支，也可以先切到自己的分支，再同步主分支。

## 5. 日常开发流程

推荐按这个顺序：

1. 先拉最新代码
2. 启动本地前后端
3. 修改代码
4. 本地自测
5. 查看变更
6. 提交到 Git
7. 推送到 GitHub

常用命令：

```bash
git status
git add .
git commit -m "你的提交说明"
git push origin main
```

如果你们组内约定使用分支开发，把最后一条改成推自己的分支即可。

## 6. 提交前至少做的检查

### 后端检查

```bash
python -m compileall backend/app
```

### 前端检查

```bash
cd web
npm run build
cd ..
```

### 接口冒烟检查

```bash
./scripts/smoke-backend.sh
```

如果是 Windows，可以优先保证：

- 本地前端能正常打开
- 登录正常
- 你改动的页面和接口没有报错

## 7. 拉取别人更新后的处理方式

如果别人已经 push 了新代码，你本地继续开发前先执行：

```bash
git checkout main
git pull origin main
```

如果你本地已经改过文件但还没提交：

- 先 `git status` 看看改了什么
- 自己确认这些改动是否要保留
- 再决定是先提交，还是先暂存后同步

## 8. 发生冲突时怎么理解

Git 冲突通常表示：

- 你改了某段代码
- 别人也改了同一段代码
- Git 不知道该保留谁

这时候不要乱删，先看冲突文件，确定最终保留哪部分逻辑，再重新提交。

## 9. 不建议的做法

- 不要直接把代码压缩包互相传来传去覆盖
- 不要在服务器上直接当开发环境改代码
- 不要把本地生成的数据、缓存、上传文件、过程材料随便提交到 GitHub
- 不要提交和本次功能无关的大量格式化改动
- 不要在没拉最新代码时直接开始改

## 10. 当前仓库里已经忽略的本地内容

以下内容默认不应提交：

- Python 缓存、虚拟环境
- `node_modules/`、构建产物
- 本地 `.env`
- 本地上传文件和演示数据
- 一些课程材料、压缩包、说明书导出文件
- 本地资料目录，如 `党团平台官方文件/`、`党团平台文件 2/`

## 11. 一版最简流程

如果只记最核心的流程，记下面这些就够了：

```bash
git pull origin main
```

改代码并本地测试后：

```bash
git status
git add .
git commit -m "update: xxx"
git push origin main
```

这就是组员在自己电脑上最基础的开发更新流程。
