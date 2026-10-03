"""P1 CQL smoke test; GUI and backup-machine checks are separate."""
import argparse
import os
import time
from cassandra.cluster import Cluster

def verify_scylla_connection(host="localhost", port=9042, max_retries=30, retry_delay=2):
    for attempt in range(1, max_retries + 1):
        cluster = None
        try:
            cluster = Cluster(contact_points=[host], port=port, connect_timeout=3, control_connection_timeout=3)
            row = cluster.connect().execute("SELECT cluster_name,release_version,data_center FROM system.local").one()
            if not row:
                raise RuntimeError("system.local returned no row")
            print(f"PASS CQL: cluster={row.cluster_name}, release={row.release_version}, dc={row.data_center}")
            print("P1 GUI and backup-machine checks are still required.")
            return True
        except Exception as error:
            print(f"CQL attempt {attempt}/{max_retries}: {type(error).__name__}")
        finally:
            if cluster is not None:
                cluster.shutdown()
        if attempt < max_retries:
            time.sleep(retry_delay)
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("SCYLLA_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SCYLLA_PORT", "9042")))
    parser.add_argument("--retries", type=int, default=30)
    args = parser.parse_args()
    raise SystemExit(0 if verify_scylla_connection(args.host, args.port, args.retries) else 1)
