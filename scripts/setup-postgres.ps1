# 初始化 PostgreSQL 本地库（Windows）
# 用法（需知道 postgres 超级用户密码，或临时改 pg_hba 为 trust 后重启服务）：
#   .\scripts\setup-postgres.ps1 -PostgresPassword "你的postgres密码"
#
# 若 student_service 用户已存在但密码不对，本脚本会用超级用户重置为 student_service

param(
    [string]$PostgresPassword = "",
    [string]$Psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$SqlFile = Join-Path $PSScriptRoot "init-postgres.sql"

if (-not (Test-Path $Psql)) {
    Write-Error "未找到 psql：$Psql，请修改 -Psql 参数"
}

if ($PostgresPassword) {
    $env:PGPASSWORD = $PostgresPassword
}

& $Psql -U postgres -h 127.0.0.1 -d postgres -v ON_ERROR_STOP=1 -f $SqlFile
& $Psql -U postgres -h 127.0.0.1 -d student_service -v ON_ERROR_STOP=1 -c "GRANT ALL ON SCHEMA public TO student_service;"

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Copy-Item (Join-Path $Root "backend\.env.example") (Join-Path $Root ".env")
    Write-Host "已创建 .env（请确认 DATABASE_URL）"
}

Write-Host "PostgreSQL 就绪。下一步："
Write-Host "  `$env:PYTHONPATH='backend'; python -m app.seed"
Write-Host "  .\scripts\dev-backend.ps1"
