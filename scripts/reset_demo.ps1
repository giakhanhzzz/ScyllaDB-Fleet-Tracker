# ==============================================================================
# ScyllaDB Fleet Tracker - Reset Môi Trường Demo Sạch Sẽ
# ==============================================================================

Write-Host ">>> Xoa sach du lieu bang va nap lai tu dau..." -ForegroundColor Yellow
docker exec -i scylla-node cqlsh -e "DROP KEYSPACE IF EXISTS fleet_tracker;"
docker exec -i scylla-node cqlsh < database/schema.cql
python database/seed.py
Write-Host ">>> [SUCCESS] Da reset demo ve trang thai ban dau!" -ForegroundColor Green
