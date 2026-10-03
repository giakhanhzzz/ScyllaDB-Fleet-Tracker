import logging
from threading import Lock
from cassandra import DriverException
from cassandra.cluster import Cluster
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

class ScyllaDatabase:
    def __init__(self):
        self.cluster = None
        self.session = None
        self.prepared_statements = {}
        self._cache = {}
        self._prepare_lock = Lock()

    def connect(self):
        self.close()
        try:
            self.cluster = Cluster(contact_points=[settings.SCYLLA_HOST], port=settings.SCYLLA_PORT,
                                   connect_timeout=10, control_connection_timeout=10)
            self.session = self.cluster.connect(settings.SCYLLA_KEYSPACE)
            catalog = {
                "login": "SELECT username,password_hash,full_name,role,company_id,active FROM users_by_username WHERE username = ?",
                "latest_locations": "SELECT * FROM latest_locations_by_company WHERE company_id = ?",
                "history": "SELECT * FROM location_events_by_vehicle_day WHERE vehicle_id = ? AND event_date = ? AND event_time >= ? AND event_time <= ?",
                "alerts_by_day": "SELECT * FROM alerts_by_company_day WHERE company_id = ? AND alert_date = ?",
                "trips_by_driver_month": "SELECT * FROM trips_by_driver_month WHERE driver_id = ? AND year_month = ?",
            }
            self.prepared_statements = {name: self.session.prepare(cql) for name, cql in catalog.items()}
        except Exception:
            self.close()
            raise

    def require_ready(self):
        if self.session is None:
            raise HTTPException(503, "ScyllaDB chưa sẵn sàng; không có chế độ dữ liệu giả")

    def execute(self, statement, parameters=()):
        self.require_ready()
        try:
            if isinstance(statement, str) and parameters:
                cql = statement.replace("%s", "?")
                with self._prepare_lock:
                    if cql not in self._cache:
                        self._cache[cql] = self.session.prepare(cql)
                    statement = self._cache[cql]
            return self.session.execute(statement, parameters)
        except DriverException:
            logger.exception("ScyllaDB request failed")
            raise HTTPException(503, "Không thực hiện được truy vấn ScyllaDB")

    def close(self):
        if self.cluster:
            self.cluster.shutdown()
        self.cluster = None
        self.session = None
        self._cache.clear()
        self.prepared_statements.clear()

db = ScyllaDatabase()
