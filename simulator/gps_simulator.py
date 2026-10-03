"""Authenticated GPS simulator; requests never supply company_id or trip_id."""
import math
import os
import random
import time
from datetime import datetime, timezone
import requests
from cassandra.util import uuid_from_time

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
INTERVAL_SECONDS = float(os.getenv("SIMULATOR_INTERVAL_SECONDS", "4"))
USERNAME = os.getenv("SIMULATOR_USERNAME", "vu_dispatcher")
PASSWORD = os.getenv("SIMULATOR_PASSWORD", "Password123@")  # Public local-demo credential.

def login(client):
    response = client.post(BACKEND_URL + "/api/auth/login", json={"username": USERNAME, "password": PASSWORD}, timeout=10)
    response.raise_for_status()
    client.headers["Authorization"] = "Bearer " + response.json()["access_token"]

def step_vehicle(vehicle):
    speed = 88.5 if vehicle["id"] == "VEH_003" else random.uniform(30, 55)
    heading = vehicle["heading"]
    distance = speed * INTERVAL_SECONDS / 3600
    vehicle["lat"] += distance * math.cos(math.radians(heading)) / 111.32
    vehicle["lng"] += distance * math.sin(math.radians(heading)) / (111.32 * math.cos(math.radians(vehicle["lat"])))
    if vehicle["id"] == "VEH_007":
        vehicle["lat"], vehicle["lng"] = 10.95, 106.90
    timestamp = datetime.now(timezone.utc)
    timestamp = timestamp.replace(microsecond=timestamp.microsecond // 1000 * 1000)
    return {"vehicle_id": vehicle["id"], "event_id": str(uuid_from_time(timestamp)),
            "lat": round(vehicle["lat"], 6), "lng": round(vehicle["lng"], 6),
            "speed": round(speed, 1), "heading": heading, "timestamp": timestamp.isoformat()}

def run_simulation():
    if not 3 <= INTERVAL_SECONDS <= 5:
        raise SystemExit("SIMULATOR_INTERVAL_SECONDS must be between 3 and 5")
    with requests.Session() as client:
        login(client)
        fleet = client.get(BACKEND_URL + "/api/fleet/vehicles", params={"status": "RUNNING"}, timeout=10)
        fleet.raise_for_status()
        vehicles = [{"id": row["vehicle_id"], "lat": 10.7769 + index * .001,
                     "lng": 106.7009, "heading": 90.0} for index, row in enumerate(fleet.json())]
        if not vehicles:
            raise SystemExit("No RUNNING vehicles; seed or start a trip before simulation")
        while True:
            for vehicle in vehicles:
                payload = step_vehicle(vehicle)
                try:
                    response = client.post(BACKEND_URL + "/api/tracking/ingest", json=payload, timeout=10)
                    if response.status_code == 401:
                        login(client)
                        response = client.post(BACKEND_URL + "/api/tracking/ingest", json=payload, timeout=10)
                    response.raise_for_status()
                    print(vehicle["id"], response.json(), flush=True)
                except requests.RequestException as error:
                    print(f"GPS failed for {vehicle['id']}: {error}", flush=True)
            time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    run_simulation()
