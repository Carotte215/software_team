$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\web")
npm run dev -- --host 127.0.0.1 --port 5177
