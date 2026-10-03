param([Parameter(Mandatory=$true)][string]$BackupDir)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$backupPath = (Resolve-Path -LiteralPath $BackupDir -ErrorAction Stop).Path
$manifest = Get-Content -LiteralPath (Join-Path $backupPath "manifest.json") -Raw | ConvertFrom-Json
$tables = @("users_by_username","users_by_company","vehicles_by_id","vehicles_by_status","drivers_by_id","drivers_by_company","trips_by_id","trips_by_company_day","trips_by_driver_month","geofences_by_vehicle","location_events_by_vehicle_day","latest_locations_by_company","vehicle_activity_by_hour","alerts_by_company_day","alerts_by_id")
foreach ($table in $tables) {
    $file = Join-Path $backupPath "$table.csv"
    if (-not (Test-Path -LiteralPath $file)) { throw "Missing backup table: $table" }
    if (@(Import-Csv -LiteralPath $file).Count -ne $manifest.tables.$table) { throw "CSV count mismatch: $table" }
}
if ((Read-Host "Type RESTORE to replace fleet_tracker data from $backupPath") -cne "RESTORE") { Write-Host "Cancelled"; return }
docker compose --profile demo stop simulator backend
if ($LASTEXITCODE -ne 0) { throw "Stop writers failed" }
# Logical restore requires the same 15-table schema to exist already.
# Save the current data before any truncate. Abort if this backup fails.
& "$PSScriptRoot/backup.ps1"
foreach ($table in $tables) {
    docker compose exec -T scylla cqlsh -e "TRUNCATE fleet_tracker.$table;"
    if ($LASTEXITCODE -ne 0) { throw "Truncate failed: $table" }
    python database/import_export.py import $table (Join-Path $backupPath "$table.csv")
    if ($LASTEXITCODE -ne 0) { throw "Restore failed: $table; writers remain stopped" }
}
$verifyDir = Join-Path "docs/backups" ("verify_" + (Get-Date -Format "yyyyMMdd_HHmmss_fff"))
& "$PSScriptRoot/backup.ps1" -BackupDir $verifyDir
$restored = Get-Content -LiteralPath (Join-Path $verifyDir "manifest.json") -Raw | ConvertFrom-Json
foreach ($table in $tables) {
    if ($restored.tables.$table -ne $manifest.tables.$table) { throw "Restored row count mismatch: $table; writers remain stopped" }
}
docker compose --profile demo up -d --wait backend
if ($LASTEXITCODE -ne 0) { throw "Backend restart failed" }
Write-Host "Restore verified for 15 tables; restart simulator explicitly if required."
