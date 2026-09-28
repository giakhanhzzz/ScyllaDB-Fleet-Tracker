# ==============================================================================
# ScyllaDB Fleet Tracker - Restore Database Script
# ==============================================================================

param(
    [string]$backupDir = "docs/backups"
)

Write-Host ">>> Canh bao: Thao tac phuc hoi se ghi de du lieu he thong!" -ForegroundColor Red
$confirm = Read-Host "Ban co chac chan muon phuc hoi? (Y/N)"

if ($confirm -eq "Y" -or $confirm -eq "y") {
    Write-Host ">>> Tai lai Schema..." -ForegroundColor Cyan
    docker exec -i scylla-node cqlsh < database/schema.cql

    Write-Host ">>> Nap lai du lieu mau tu Seed..." -ForegroundColor Cyan
    python database/seed.py

    Write-Host ">>> [SUCCESS] Phuc hoi thanh cong!" -ForegroundColor Green
} else {
    Write-Host ">>> Huy thao tac phuc hoi." -ForegroundColor Yellow
}
