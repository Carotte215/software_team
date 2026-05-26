$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
Write-Host "Installing backend dependencies..."
python -m pip install -r backend/requirements.txt
Write-Host "Installing frontend dependencies..."
Set-Location web
npm install
Write-Host "Done. Next: python -m app.seed (from backend dir with PYTHONPATH=backend), then scripts/dev-backend.ps1 and scripts/dev-web.ps1"
