# Vue Web 端适配说明

这是学院学生综合服务与党团管理平台的 Vue 3 + Vite Web 适配版。当前互测版本默认直连 FastAPI 后端，不再把浏览器本地 mock 作为主入口。

## 运行

首次运行安装依赖：

```bash
cd web
npm install
```

启动开发服务：

```bash
npm run dev
```

访问：

```text
http://127.0.0.1:5177/
```

构建与预览：

```bash
npm run build
npm run preview
```

## 模块边界

- `src/main.js`：Vue 应用入口。
- `src/App.vue`：应用外壳、登录会话、导航与视图分发。
- `src/views/`：各业务页面组件，按知识库、党团流程、申请审批、通知、荣誉、学业、画像、工作台拆分。
- `src/services/api.js`：面向页面的统一 API 门面，聚合各业务模块。
- `src/services/modules/`：按业务域拆分的 API 模块，例如 `students.js`、`knowledge.js`、`applications.js`、`partyTheory.js`。
- `src/api/client.js`：统一请求入口。默认连接真实后端 `/api`。
- `src/api/mockGateway.js`：仅保留开发兼容，不作为默认互测入口。
- `src/api/store.js`：本地兼容数据仓储，仅供保留的离线逻辑使用。
- `src/state/session.js`：当前登录学生与角色会话。
- `src/state/routes.js`：前端功能导航与 hash 路由配置。
- `src/data/seed.js`：演示种子数据与常量。

## 后端对接说明

页面组件通过 `src/services/api.js` 调用业务函数，不直接访问 localStorage，也不直接耦合 mock 数据结构。

新增前端接口时优先放入 `src/services/modules/<domain>.js`，再由 `src/services/api.js` 聚合导出。页面组件保持调用 `api.xxx()`，这样后续调整 URL 或补兼容逻辑时不需要改页面。

当前默认后端地址：

```js
localStorage.setItem("ss_web_api_base_url", "http://127.0.0.1:8000/api");
```

页面右上角显示真实登录表单。最小测试账号默认密码是：

```text
Stu@ + 学号后 6 位
```

登录成功后前端保存后端签发的 Bearer Token，并由统一请求层自动带到后续接口。若模板下载提示未上传，需先在管理工作台上传真实模板文件。
