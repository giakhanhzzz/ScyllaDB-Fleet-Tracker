# ==============================================================================
# ScyllaDB Fleet Tracker - Khởi tạo toàn bộ môi trường Demo
# ==============================================================================

Write-Host ">>> 1. Khoi dong ScyllaDB bang Docker Compose..." -ForegroundColor Cyan
docker compose up -d

Write-Host ">>> 2. Doi ScyllaDB san sang ket noi (port 9042)..." -ForegroundColor Yellow
python scripts/wait_for_scylla.py

Write-Host ">>> 3. Nap Schema CQL (15 Tables)..." -ForegroundColor Cyan
docker exec -i scylla-node cqlsh < database/schema.cql

Write-Host ">>> 4. Nap du lieu mau Seed (Users, Vehicles, Drivers, Trips, 3000+ GPS)..." -ForegroundColor Cyan
python database/seed.py

Write-Host ">>> [HOAN TAT] He thong da khoi tao thanh cong! San sang demo!" -ForegroundColor Green
