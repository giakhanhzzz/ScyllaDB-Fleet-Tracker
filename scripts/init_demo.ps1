$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path -LiteralPath ".env")) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $key = [System.BitConverter]::ToString($bytes).Replace("-", "").ToLowerInvariant()
    (Get-Content -LiteralPath ".env.example" -Raw).Replace("SECRET_KEY=", "SECRET_KEY=$key") | Set-Content -LiteralPath ".env" -Encoding utf8
}
docker compose --profile demo build backend simulator
if ($LASTEXITCODE -ne 0) { throw "Build backend failed" }
docker compose up -d --wait scylla
if ($LASTEXITCODE -ne 0) { throw "Scylla startup failed" }
docker compose --profile demo stop simulator backend
if ($LASTEXITCODE -ne 0) { throw "Stop writers before seed failed" }
docker compose --profile demo run --rm --no-deps backend python scripts/wait_for_scylla.py
if ($LASTEXITCODE -ne 0) { throw "CQL smoke test failed" }
docker compose cp database/schema.cql scylla:/tmp/fleet-schema.cql
if ($LASTEXITCODE -ne 0) { throw "Schema copy failed" }
docker compose exec -T scylla cqlsh -f /tmp/fleet-schema.cql
if ($LASTEXITCODE -ne 0) { throw "Schema execution failed" }
docker compose --profile demo run --rm --no-deps backend python database/seed.py
if ($LASTEXITCODE -ne 0) { throw "Seed failed; demo not initialized" }
docker compose --profile demo up -d --wait backend
if ($LASTEXITCODE -ne 0) { throw "Backend startup failed" }
Write-Host "Backend: http://localhost:8000/docs. Simulator starts only when explicitly requested."
