#!/usr/bin/env python3
"""
ScyllaDB Fleet Tracker - GPS Simulator Process
Mô phỏng thiết bị GPS gắn trên xe gửi tọa độ định kỳ (3-5s):
- Sinh vị trí bình thường di chuyển trên các tuyến đường TP.HCM
- Sinh lỗi chủ đích: Quá tốc độ (Overspeed), Ra khỏi vùng địa lý (Geofence exit), Mất tín hiệu (GPS lost)
"""

import os
import time
import random
import requests
from datetime import datetime, timezone

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/tracking/ingest")
INTERVAL_SECONDS = float(os.getenv("SIMULATOR_INTERVAL_SECONDS", "3.0"))

# Danh sách xe và trạng thái mô phỏng
VEHICLES = [
    {"id": "VEH_001", "lat": 10.7769, "lng": 106.7009, "speed": 45.0, "heading": 90.0, "mode": "normal"},
    {"id": "VEH_002", "lat": 10.7820, "lng": 106.6950, "speed": 50.0, "heading": 180.0, "mode": "normal"},
    {"id": "VEH_003", "lat": 10.7650, "lng": 106.6820, "speed": 85.0, "heading": 45.0, "mode": "overspeed"}, # Lỗi vượt tốc độ
    {"id": "VEH_005", "lat": 10.8500, "lng": 106.7700, "speed": 40.0, "heading": 270.0, "mode": "normal"},
    {"id": "VEH_007", "lat": 10.9500, "lng": 106.9000, "speed": 35.0, "heading": 0.0, "mode": "geofence_exit"}, # Ngoài geofence
]

def step_vehicle(v):
    if v["mode"] == "lost":
        return None # Giả lập mất tín hiệu GPS

    # Di chuyển nhẹ tọa độ
    delta = 0.0003
    if v["heading"] == 90.0:
        v["lng"] += delta
    elif v["heading"] == 180.0:
        v["lat"] -= delta
    elif v["heading"] == 270.0:
        v["lng"] -= delta
    else:
        v["lat"] += delta

    if v["mode"] == "overspeed":
        v["speed"] = round(random.uniform(82.0, 95.0), 1)
    else:
        v["speed"] = round(random.uniform(30.0, 60.0), 1)

    return {
        "vehicle_id": v["id"],
        "lat": round(v["lat"], 6),
        "lng": round(v["lng"], 6),
        "speed": v["speed"],
        "heading": v["heading"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trip_id": "TRIP_202609_001",
        "company_id": "COMP_HCM_01"
    }

def run_simulation():
    print("=" * 60)
    print(" [GPS SIMULATOR] BẮT ĐẦU PHÁT TÍN HIỆU GPS ĐỘI XE")
    print(f" Target: {BACKEND_URL} | Interval: {INTERVAL_SECONDS}s")
    print("=" * 60)

    step = 1
    while True:
        print(f"\n--- [Chu kỳ {step}] Gửi GPS {datetime.now().strftime('%H:%M:%S')} ---")
        for v in VEHICLES:
            payload = step_vehicle(v)
            if payload:
                try:
                    res = requests.post(BACKEND_URL, json=payload, timeout=2.0)
                    print(f"  [{v['id']}] ({v['mode']}) -> {payload['lat']},{payload['lng']} | Speed: {payload['speed']} km/h (Status: {res.status_code})")
                except Exception as e:
                    print(f"  [{v['id']}] Gửi lỗi: {e}")
            else:
                print(f"  [{v['id']}] [MẤT TÍN HIỆU] Xe đang offline...")

        step += 1
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    run_simulation()
