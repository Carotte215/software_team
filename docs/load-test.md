# 简易压测说明（课程验收）

可使用 Apache Bench 对只读接口做抽样：

```bash
ab -n 200 -c 20 http://10.10.0.21/api/knowledge
ab -n 100 -c 10 http://10.10.0.21/health
```

目标：1200 人规模下常规查询 P95 < 2s（课程演示级抽样即可）。

需带 Token 的接口请先登录获取 JWT，再用 `curl -H "Authorization: Bearer <token>"` 单点验证。
