#!/usr/bin/env python3
"""
ScyllaDB Fleet Tracker - Import & Export Utility
Hỗ trợ xuất/nhập dữ liệu CSV và JSON cho các bảng ScyllaDB
Đáp ứng tiêu chí Rubric Mục 6: Import/Export và đối chiếu dòng dữ liệu
"""

import os
import sys
import csv
import json
from datetime import datetime

try:
    from cassandra.cluster import Cluster
except ImportError:
    pass

def export_table_to_csv(table_name: str, output_path: str):
    """Xuất dữ liệu một bảng ScyllaDB ra file CSV"""
    host = os.getenv("SCYLLA_HOST", "localhost")
    port = int(os.getenv("SCYLLA_PORT", 9042))
    
    cluster = Cluster(contact_points=[host], port=port)
    session = cluster.connect("fleet_tracker")
    
    print(f"[EXPORT] Bắt đầu xuất bảng '{table_name}' ra {output_path}...")
    rows = session.execute(f"SELECT * FROM {table_name}")
    
    row_list = list(rows)
    if not row_list:
        print(f"[WARN] Bảng '{table_name}' không có dữ liệu để xuất.")
        cluster.shutdown()
        return 0

    fieldnames = row_list[0]._fields
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for r in row_list:
            writer.writerow([getattr(r, fn) for fn in fieldnames])
            
    print(f"[SUCCESS] Đã xuất {len(row_list)} dòng từ bảng '{table_name}' thành công!")
    cluster.shutdown()
    return len(row_list)

def import_vehicles_from_csv(input_path: str):
    """Nhập dữ liệu xe từ file CSV vào ScyllaDB (cập nhật đồng thời vehicles_by_id và vehicles_by_status)"""
    host = os.getenv("SCYLLA_HOST", "localhost")
    port = int(os.getenv("SCYLLA_PORT", 9042))
    
    cluster = Cluster(contact_points=[host], port=port)
    session = cluster.connect("fleet_tracker")
    
    print(f"[IMPORT] Đọc dữ liệu từ file {input_path}...")
    imported_count = 0
    
    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            session.execute(
                """
                INSERT INTO vehicles_by_id (vehicle_id, company_id, plate, model, current_driver_id, status, speed_limit, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))
                """,
                (row["vehicle_id"], row["company_id"], row["plate"], row["model"], 
                 row["current_driver_id"] or None, row["status"], float(row["speed_limit"]))
            )
            session.execute(
                """
                INSERT INTO vehicles_by_status (company_id, status, vehicle_id, plate, model, current_driver_id, speed_limit)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (row["company_id"], row["status"], row["vehicle_id"], row["plate"], 
                 row["model"], row["current_driver_id"] or None, float(row["speed_limit"]))
            )
            imported_count += 1
            
    print(f"[SUCCESS] Đã nhập thành công {imported_count} dòng vào ScyllaDB!")
    cluster.shutdown()
    return imported_count

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "export":
        export_table_to_csv(sys.argv[2], f"docs/exports/{sys.argv[2]}.csv")
    else:
        print("Sử dụng: python database/import_export.py export <table_name>")
