$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if ((Read-Host "Type RESET to replace fleet_tracker with seed data") -cne "RESET") { Write-Host "Cancelled"; return }
docker compose --profile demo stop simulator backend
if ($LASTEXITCODE -ne 0) { throw "Stop writers failed" }
& "$PSScriptRoot/backup.ps1"
docker compose exec -T scylla cqlsh -e "DROP KEYSPACE IF EXISTS fleet_tracker;"
if ($LASTEXITCODE -ne 0) { throw "Reset failed" }
& "$PSScriptRoot/init_demo.ps1"
