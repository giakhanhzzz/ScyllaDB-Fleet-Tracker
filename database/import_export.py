"""Local administration only: cqlsh COPY for the 15 approved tables."""
import argparse
import csv
import subprocess
from pathlib import Path

TABLES = (
    "users_by_username", "users_by_company", "vehicles_by_id", "vehicles_by_status",
    "drivers_by_id", "drivers_by_company", "trips_by_id", "trips_by_company_day",
    "trips_by_driver_month", "geofences_by_vehicle", "location_events_by_vehicle_day",
    "latest_locations_by_company", "vehicle_activity_by_hour", "alerts_by_company_day", "alerts_by_id",
)

def run(*args):
    return subprocess.run(args, check=True, text=True, encoding="utf-8", capture_output=True)

def count_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)

def transfer(mode, table, path):
    if table not in TABLES or mode not in ("export", "import"):
        raise ValueError("Invalid table or operation")
    path = Path(path).resolve()
    remote = f"/tmp/fleet-{table}.csv"
    if mode == "export":
        path.parent.mkdir(parents=True, exist_ok=True)
        run("docker", "compose", "exec", "-T", "scylla", "cqlsh", "-e",
            f"COPY fleet_tracker.{table} TO '{remote}' WITH HEADER = TRUE;")
        run("docker", "compose", "cp", f"scylla:{remote}", str(path))
    else:
        if not path.is_file():
            raise FileNotFoundError(path)
        run("docker", "compose", "cp", str(path), f"scylla:{remote}")
        result = run("docker", "compose", "exec", "-T", "scylla", "cqlsh", "-e",
                     f"COPY fleet_tracker.{table} FROM '{remote}' WITH HEADER = TRUE;")
        # cqlsh COPY may print row errors without a nonzero process exit.
        if "Failed to import" in result.stdout + result.stderr:
            raise RuntimeError(result.stdout + result.stderr)
    print(f"{mode}: {table}: {count_csv(path)} CSV rows")
    return count_csv(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("export", "import"))
    parser.add_argument("table", choices=TABLES)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    transfer(args.mode, args.table, args.path)
