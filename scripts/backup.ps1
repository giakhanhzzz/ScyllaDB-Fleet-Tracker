# ==============================================================================
# ScyllaDB Fleet Tracker - Backup Database Script
# ==============================================================================

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "docs/backups/$timestamp"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

Write-Host ">>> Sao luu Keyspace Schema..." -ForegroundColor Cyan
docker exec -i scylla-node cqlsh -e "DESCRIBE KEYSPACE fleet_tracker;" > "$backupDir/schema_backup.cql"

Write-Host ">>> Xuat du lieu cac bang sang CSV (COPY TO)..." -ForegroundColor Cyan
python database/import_export.py export vehicles_by_id
python database/import_export.py export drivers_by_id

Write-Host ">>> [SUCCESS] Sao luu du lieu hoan tat tai: $backupDir" -ForegroundColor Green
