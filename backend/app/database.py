from cassandra.cluster import Cluster
from app.config import settings

class ScyllaDatabase:
    def __init__(self):
        self.cluster = None
        self.session = None
        self.prepared_statements = {}

    def connect(self):
        try:
            self.cluster = Cluster(
                contact_points=[settings.SCYLLA_HOST],
                port=settings.SCYLLA_PORT,
                connect_timeout=10
            )
            self.session = self.cluster.connect(settings.SCYLLA_KEYSPACE)
            self._prepare_statements()
            print("[INFO] Kết nối ScyllaDB Session thành công!")
        except Exception as e:
            print(f"[WARN] Chưa kết nối được ScyllaDB: {e}")

    def _prepare_statements(self):
        # Q1: Login
        self.prepared_statements["login"] = self.session.prepare(
            "SELECT username, password_hash, full_name, role, company_id, active FROM users_by_username WHERE username = ?"
        )
        # Q8: Latest locations
        self.prepared_statements["latest_locations"] = self.session.prepare(
            "SELECT vehicle_id, event_time, lat, lng, speed, heading, trip_id, status FROM latest_locations_by_company WHERE company_id = ?"
        )
        # Q9: Location history
        self.prepared_statements["history"] = self.session.prepare(
            "SELECT event_time, event_id, lat, lng, speed, heading, trip_id FROM location_events_by_vehicle_day "
            "WHERE vehicle_id = ? AND event_date = ? AND event_time >= ? AND event_time <= ?"
        )
        # Q11: Alerts by day
        self.prepared_statements["alerts_by_day"] = self.session.prepare(
            "SELECT created_at, alert_id, vehicle_id, trip_id, alert_type, severity, status, details FROM alerts_by_company_day "
            "WHERE company_id = ? AND alert_date = ?"
        )
        # Q14: Trips by driver month
        self.prepared_statements["trips_by_driver_month"] = self.session.prepare(
            "SELECT trip_id, start_time, status, distance_km FROM trips_by_driver_month WHERE driver_id = ? AND year_month = ?"
        )

    def close(self):
        if self.cluster:
            self.cluster.shutdown()

db = ScyllaDatabase()
