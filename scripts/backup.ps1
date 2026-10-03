param([string]$BackupDir)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$runningServices = @(docker compose --profile demo ps --status running --services)
if ($LASTEXITCODE -ne 0) { throw "Cannot inspect writers" }
if (@($runningServices | Where-Object { $_ -in @("backend", "simulator") }).Count) {
    throw "Stop backend and simulator before backup; do not write through a GUI during COPY"
}
if (-not $BackupDir) { $BackupDir = Join-Path "docs/backups" (Get-Date -Format "yyyyMMdd_HHmmss_fff") }
$backupPath = [System.IO.Path]::GetFullPath($BackupDir)
if (Test-Path -LiteralPath $backupPath) { throw "Backup directory already exists; refusing overwrite" }
New-Item -ItemType Directory -Path $backupPath -ErrorAction Stop | Out-Null
docker compose exec -T scylla sh -c 'cqlsh -e "DESCRIBE KEYSPACE fleet_tracker;" > /tmp/fleet-backup-schema.cql'
if ($LASTEXITCODE -ne 0) { throw "Schema backup failed" }
docker compose cp scylla:/tmp/fleet-backup-schema.cql (Join-Path $backupPath "schema.cql")
if ($LASTEXITCODE -ne 0) { throw "Schema download failed" }
$tables = @("users_by_username","users_by_company","vehicles_by_id","vehicles_by_status","drivers_by_id","drivers_by_company","trips_by_id","trips_by_company_day","trips_by_driver_month","geofences_by_vehicle","location_events_by_vehicle_day","latest_locations_by_company","vehicle_activity_by_hour","alerts_by_company_day","alerts_by_id")
$counts = @{}
foreach ($table in $tables) {
    $csvPath = Join-Path $backupPath "$table.csv"
    python database/import_export.py export $table $csvPath
    if ($LASTEXITCODE -ne 0) { throw "Export failed: $table" }
    $counts[$table] = @(Import-Csv -LiteralPath $csvPath).Count
}
$manifest = @{created_at=(Get-Date).ToUniversalTime().ToString("o"); tables=$counts; consistency="Backend/simulator stopped; external writers must also stop"; ttl="Logical COPY restore restarts table TTL"}
$manifest | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $backupPath "manifest.json") -Encoding utf8
Write-Host "Backup completed: $backupPath"
