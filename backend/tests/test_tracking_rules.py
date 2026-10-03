"""Focused tracking checks; no claim that a real CQL server was exercised."""
import os
import sys
import unittest
import importlib.util
import io
from collections import namedtuple
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from cassandra.util import uuid_from_time
from cassandra.util import Date as CQLDate
from fastapi import HTTPException
from pydantic import ValidationError

os.environ.setdefault("SECRET_KEY", "test-only-signing-key-not-for-deployment-123456")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import db
from app.schemas import GPSIngest
from app.services import calculate_trip_distance, check_geofence, haversine_km, row_to_dict
from app.routes_tracking import ingest_gps, get_vehicle_history

class Rows(list):
    def one(self):
        return self[0] if self else None

class TrackingTests(unittest.TestCase):
    def payload(self):
        timestamp = datetime.now(timezone.utc) - timedelta(seconds=30)
        timestamp = timestamp.replace(microsecond=timestamp.microsecond // 1000 * 1000)
        return {"vehicle_id":"V","event_id":uuid_from_time(timestamp),
                "timestamp":timestamp,"lat":10.77,"lng":106.70,"speed":40,"heading":90}

    def test_rejects_invalid_coordinates_speed_heading_timezone_and_company(self):
        payload = self.payload()
        invalid = [
            {"lat":91}, {"lng":-181}, {"speed":-1}, {"heading":360},
            {"lat":float("nan")}, {"timestamp":datetime.now()},
            {"company_id":"FORGED"},
        ]
        for change in invalid:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                GPSIngest(**(payload | change))

    def test_haversine_reference_and_antipodal_point(self):
        self.assertAlmostEqual(haversine_km(0,0,0,1), 111.195, places=2)
        self.assertTrue(20000 < haversine_km(0,0,0,180) < 20020)

    def test_cql_dates_and_naive_timestamps_have_unambiguous_api_values(self):
        row = namedtuple("Point","event_time event_date")(datetime(2026,9,28,12),CQLDate("2026-09-28"))
        values = row_to_dict(row)
        self.assertEqual(values["event_time"].isoformat(),"2026-09-28T12:00:00+00:00")
        self.assertEqual(values["event_date"],"2026-09-28")

    def test_distance_sorts_and_rejects_zero_time_and_outlier(self):
        start = datetime(2026,9,28,tzinfo=timezone.utc)
        points = [(10,106,start), (30,120,start + timedelta(seconds=1)),
                  (10,106.01,start + timedelta(minutes=2)),
                  (10,106.5,start + timedelta(minutes=2))]
        km, rejected = calculate_trip_distance(list(reversed(points)))
        self.assertGreater(km, 1)
        self.assertLess(km, 1.2)
        self.assertEqual(rejected, 2)

    def test_geofence_db_failure_is_not_silently_allowed(self):
        with patch.object(db, "execute", side_effect=HTTPException(503, "offline")):
            with self.assertRaises(HTTPException) as result:
                check_geofence("V",10,106)
        self.assertEqual(result.exception.status_code,503)

    def test_geofence_boundary_is_inside(self):
        fence = SimpleNamespace(enabled=True,min_lat=10,max_lat=11,min_lng=106,max_lng=107)
        with patch.object(db,"execute",return_value=Rows([fence])):
            self.assertTrue(check_geofence("V",10,107))
            self.assertFalse(check_geofence("V",12,107))

    def test_late_event_does_not_overwrite_latest(self):
        req = GPSIngest(**self.payload())
        calls = []
        vehicle = SimpleNamespace(vehicle_id="V",company_id="C",status="RUNNING",speed_limit=80)
        latest = SimpleNamespace(event_time=req.timestamp + timedelta(seconds=10),trip_id=None)
        def execute(sql, params=()):
            calls.append(sql)
            if sql.startswith("SELECT * FROM vehicles_by_id"):
                return Rows([vehicle])
            if sql.startswith("SELECT * FROM latest_locations"):
                return Rows([latest])
            return Rows()
        with patch.object(db,"execute",side_effect=execute):
            result = ingest_gps(req,{"company_id":"C"})
        self.assertFalse(result["latest_updated"])
        self.assertFalse(any(sql.startswith("UPDATE latest_locations") for sql in calls))
        self.assertTrue(any(sql.startswith("INSERT INTO location_events") for sql in calls))

    def test_reused_event_id_cannot_change_timestamp(self):
        payload = self.payload()
        payload["timestamp"] += timedelta(seconds=1)
        req = GPSIngest(**payload)
        vehicle = SimpleNamespace(company_id="C",status="RUNNING")
        with patch.object(db,"execute",return_value=Rows([vehicle])):
            with self.assertRaises(HTTPException) as error:
                ingest_gps(req,{"company_id":"C"})
        self.assertEqual(error.exception.status_code,422)

    def test_lwt_conflict_does_not_claim_latest_update_or_raise_alert(self):
        req = GPSIngest(**(self.payload() | {"speed": 90}))
        vehicle = SimpleNamespace(vehicle_id="V",company_id="C",status="RUNNING",speed_limit=80)
        latest = SimpleNamespace(event_time=req.timestamp - timedelta(seconds=10),trip_id=None)
        def execute(sql, params=()):
            if sql.startswith("SELECT * FROM vehicles_by_id"):
                return Rows([vehicle])
            if sql.startswith("SELECT * FROM latest_locations"):
                return Rows([latest])
            if sql.startswith("UPDATE latest_locations"):
                return Rows([SimpleNamespace(applied=False)])
            return Rows()
        with patch.object(db,"execute",side_effect=execute), patch("app.routes_tracking.create_alert") as alerts:
            result = ingest_gps(req,{"company_id":"C"})
        self.assertFalse(result["latest_updated"])
        alerts.assert_not_called()

    def test_vehicle_from_other_company_is_rejected(self):
        vehicle = SimpleNamespace(company_id="OTHER",status="RUNNING")
        with patch.object(db,"execute",return_value=Rows([vehicle])):
            with self.assertRaises(HTTPException) as error:
                ingest_gps(GPSIngest(**self.payload()),{"company_id":"C"})
        self.assertEqual(error.exception.status_code,404)

    def test_history_reads_both_day_partitions(self):
        start = datetime(2026,9,27,23,59,tzinfo=timezone.utc)
        end = start + timedelta(minutes=2)
        days=[]
        def execute(sql, params=()):
            if "vehicles_by_id" in sql:
                return Rows([SimpleNamespace(company_id="C")])
            days.append(params[1])
            return Rows()
        with patch.object(db,"execute",side_effect=execute):
            result=get_vehicle_history("V",None,start,end,500,0,{"company_id":"C"})
        self.assertEqual(days,[start.date(),end.date()])
        self.assertEqual(result["points"],[])

    def test_seed_keys_are_repeatable_and_month_partitions_follow_trip_dates(self):
        source = Path(__file__).resolve().parents[2] / "database" / "seed.py"
        spec = importlib.util.spec_from_file_location("fleet_seed_test", source)
        seed = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed)
        writes = []
        session = Mock()
        session.execute.side_effect = lambda sql, params: writes.append((" ".join(sql.split()), params))
        cluster = Mock()
        with patch.object(seed,"get_session",return_value=(cluster,session)), \
             patch.dict(os.environ,{"SEED_DATE":"2026-10-01"}), redirect_stdout(io.StringIO()):
            self.assertTrue(seed.seed_data())
            self.assertTrue(seed.seed_data())
        gps = [params for sql,params in writes if "INSERT INTO location_events_by_vehicle_day" in sql]
        self.assertEqual(len(gps),6400)
        self.assertEqual(len({params[:4] for params in gps}),3200)
        months = [params for sql,params in writes if "INSERT INTO trips_by_driver_month" in sql]
        self.assertEqual({params[1] for params in months},{"2026-09","2026-10"})
        self.assertTrue(all(params[1] == params[2].strftime("%Y-%m") for params in months))
        latest = [params for sql,params in writes if "INSERT INTO latest_locations_by_company" in sql]
        self.assertTrue(all(params[7] is not None for params in latest))
        self.assertEqual(cluster.shutdown.call_count,2)

if __name__ == "__main__":
    unittest.main()
