"""Unit/API regression checks with a fake DB, not Scylla integration evidence."""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid1
from cassandra.query import BatchStatement

os.environ.setdefault("SECRET_KEY", "test-only-signing-key-not-for-deployment-123456")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import app
from app.database import db
from app.security import create_access_token, hash_password, verify_password

class Rows(list):
    def one(self):
        return self[0] if self else None

class PermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password("Password123@")

    def setUp(self):
        self.calls = []
        self.user = SimpleNamespace(username="viewer", password_hash=self.password_hash,
                                    full_name="Viewer", role="VIEWER", company_id="COMP_TEST", active=True)
        self.session_patch = patch.object(db, "session", object())
        self.statements_patch = patch.dict(db.prepared_statements, {"login": "LOGIN"})
        self.execute_patch = patch.object(db, "execute", side_effect=self.execute)
        self.session_patch.start()
        self.statements_patch.start()
        self.execute_patch.start()
        self.addCleanup(self.execute_patch.stop)
        self.addCleanup(self.statements_patch.stop)
        self.addCleanup(self.session_patch.stop)
        self.client = TestClient(app)
        self.token = create_access_token({"sub": "viewer", "role": "ADMIN", "company_id": "FAKE"})
        self.headers = {"Authorization": "Bearer " + self.token}

    def execute(self, statement, parameters=()):
        self.calls.append((statement, parameters))
        return Rows([self.user]) if statement == "LOGIN" else Rows()

    def test_wrong_password_is_rejected(self):
        result = self.client.post("/api/auth/login", json={"username": "viewer", "password": "wrong"})
        self.assertEqual(result.status_code, 401)

    def test_seed_password_logs_in(self):
        result = self.client.post("/api/auth/login", json={"username": "viewer", "password": "Password123@"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["role"], "VIEWER")

    def test_static_dashboard_is_served_without_shadowing_api(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("ScyllaDB Fleet Tracker", page.text)
        self.assertIn("/vendor/leaflet/leaflet.js", page.text)
        self.assertIn("id=\"user-form\"", page.text)
        self.assertIn("id=\"vehicle-form\"", page.text)
        self.assertIn("id=\"driver-form\"", page.text)
        self.assertIn("id=\"trip-form\"", page.text)
        self.assertEqual(self.client.get("/app.js").status_code, 200)
        self.assertEqual(self.client.get("/styles.css").status_code, 200)
        self.assertEqual(self.client.get("/vendor/leaflet/leaflet.js").status_code, 200)
        self.assertIn("ACKNOWLEDGED", self.client.get("/app.js").text)
        self.assertIn("RESOLVED", self.client.get("/app.js").text)
        self.assertEqual(self.client.get("/api/fleet/vehicles", headers=self.headers).status_code, 200)

    def test_db_unavailable_never_falls_back_to_demo_login(self):
        with patch.object(db, "session", None):
            result = self.client.post("/api/auth/login", json={"username": "khanh_admin", "password": "anything"})
        self.assertEqual(result.status_code, 503)

    def test_viewer_cannot_create_trip_even_with_admin_claim(self):
        result = self.client.post("/api/fleet/trips", headers=self.headers, json={
            "trip_id":"T","vehicle_id":"V","driver_id":"D","origin":"A","destination":"B"})
        self.assertEqual(result.status_code, 403)

    def test_viewer_cannot_ingest_gps(self):
        result = self.client.post("/api/tracking/ingest", headers=self.headers, json={})
        self.assertEqual(result.status_code, 403)

    def test_viewer_cannot_resolve_alert(self):
        result = self.client.post("/api/tracking/alerts/action", headers=self.headers,
                                  json={"alert_id": str(uuid1()), "status": "RESOLVED"})
        self.assertEqual(result.status_code, 403)

    def test_viewer_cannot_create_user(self):
        result = self.client.post("/api/users", headers=self.headers, json={
            "username":"new_viewer","password":"Password123@","full_name":"Người mới","role":"VIEWER"})
        self.assertEqual(result.status_code, 403)

    def test_viewer_cannot_create_vehicle_or_driver(self):
        self.assertEqual(self.client.post("/api/fleet/vehicles", headers=self.headers, json={}).status_code, 403)
        self.assertEqual(self.client.post("/api/fleet/drivers", headers=self.headers, json={}).status_code, 403)

    def test_viewer_cannot_modify_vehicle_or_driver(self):
        self.assertEqual(self.client.patch("/api/fleet/vehicles/V", headers=self.headers, json={}).status_code, 403)
        self.assertEqual(self.client.patch("/api/fleet/drivers/D", headers=self.headers, json={}).status_code, 403)

    def test_admin_creates_user_only_in_own_company(self):
        self.user.role = "ADMIN"
        previous = self.execute
        def execute(statement, parameters=()):
            if statement == "LOGIN" and parameters == ("new_viewer",):
                return Rows()
            return previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            result = self.client.post("/api/users", headers=self.headers, json={
                "username":"new_viewer","password":"Password123@","full_name":"Người mới","role":"VIEWER"})
        self.assertEqual(result.status_code, 201)
        batches = [statement for statement, _ in self.calls if isinstance(statement, BatchStatement)]
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]._statements_and_parameters), 2)
        self.assertTrue(all("COMP_TEST" in query for _, query, _ in batches[0]._statements_and_parameters))

    def test_admin_cannot_supply_foreign_company_when_creating_user(self):
        self.user.role = "ADMIN"
        result = self.client.post("/api/users", headers=self.headers, json={
            "username":"new_viewer","password":"Password123@","full_name":"Người mới",
            "role":"VIEWER","company_id":"OTHER"})
        self.assertEqual(result.status_code, 422)

    def test_admin_cannot_disable_self(self):
        self.user.role = "ADMIN"
        result = self.client.patch("/api/users/viewer", headers=self.headers, json={"active":False})
        self.assertEqual(result.status_code, 409)

    def test_admin_cannot_update_user_from_another_company(self):
        self.user.role = "ADMIN"
        other = SimpleNamespace(company_id="OTHER", username="another", role="VIEWER",active=True)
        previous = self.execute
        def execute(statement, parameters=()):
            return Rows([other]) if statement == "LOGIN" and parameters == ("another",) else previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            result = self.client.patch("/api/users/another", headers=self.headers, json={"active":False})
        self.assertEqual(result.status_code, 404)

    def test_admin_updates_both_user_projections(self):
        self.user.role = "ADMIN"
        target = SimpleNamespace(company_id="COMP_TEST", username="another", role="VIEWER",
                                 full_name="Người cũ", password_hash=self.password_hash, active=True)
        previous = self.execute
        def execute(statement, parameters=()):
            return Rows([target]) if statement == "LOGIN" and parameters == ("another",) else previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            result = self.client.patch("/api/users/another", headers=self.headers,
                                       json={"role":"DISPATCHER","active":False})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["role"], "DISPATCHER")
        batches = [statement for statement, _ in self.calls if isinstance(statement, BatchStatement)]
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]._statements_and_parameters), 2)

    def test_dispatcher_creates_vehicle_and_driver_in_own_company(self):
        self.user.role = "DISPATCHER"
        driver = self.client.post("/api/fleet/drivers", headers=self.headers, json={
            "driver_id":"D_NEW","full_name":"Tài xế mới","license_number":"B2-123","phone":"0900000000"})
        self.assertEqual(driver.status_code, 201)
        previous = self.execute
        def execute(statement, parameters=()):
            if isinstance(statement, str) and "FROM drivers_by_id" in statement:
                return Rows([SimpleNamespace(company_id="COMP_TEST", active=True)])
            return previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            vehicle = self.client.post("/api/fleet/vehicles", headers=self.headers, json={
                "vehicle_id":"V_NEW","plate":"51A-12345","model":"Van",
                "current_driver_id":"D_NEW","status":"RUNNING","speed_limit":70})
        self.assertEqual(vehicle.status_code, 201)
        batches = [statement for statement, _ in self.calls if isinstance(statement, BatchStatement)]
        self.assertEqual(len(batches), 2)
        self.assertEqual([len(batch._statements_and_parameters) for batch in batches], [2,3])
        self.assertTrue(all("COMP_TEST" in query for batch in batches
                            for _, query, _ in batch._statements_and_parameters[:2]))
        self.assertIn("geofences_by_vehicle", batches[1]._statements_and_parameters[2][1])

    def test_running_vehicle_needs_active_driver_from_company(self):
        self.user.role = "DISPATCHER"
        payload = {"vehicle_id":"V_NEW","plate":"51A-12345","model":"Van","status":"RUNNING"}
        self.assertEqual(self.client.post("/api/fleet/vehicles", headers=self.headers, json=payload).status_code, 422)
        other = SimpleNamespace(company_id="OTHER", active=True)
        previous = self.execute
        def execute(statement, parameters=()):
            if isinstance(statement, str) and "FROM drivers_by_id" in statement:
                return Rows([other])
            return previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            payload["current_driver_id"] = "OTHER_DRIVER"
            self.assertEqual(self.client.post("/api/fleet/vehicles", headers=self.headers, json=payload).status_code, 422)

    def test_vehicle_status_move_updates_both_projections(self):
        self.user.role = "DISPATCHER"
        current = SimpleNamespace(vehicle_id="V",company_id="COMP_TEST",plate="P",model="M",
                                  current_driver_id=None,status="IDLE",speed_limit=80)
        previous = self.execute
        def execute(statement, parameters=()):
            if isinstance(statement, str) and "FROM vehicles_by_id" in statement:
                return Rows([current])
            return previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            result = self.client.patch("/api/fleet/vehicles/V", headers=self.headers,
                                       json={"status":"MAINTENANCE"})
        self.assertEqual(result.status_code, 200)
        batches = [statement for statement, _ in self.calls if isinstance(statement, BatchStatement)]
        self.assertEqual(len(batches), 1)
        queries = [query for _, query, _ in batches[0]._statements_and_parameters]
        self.assertEqual(len(queries), 3)
        self.assertTrue(any(query.startswith("DELETE FROM vehicles_by_status") for query in queries))

    def test_driver_deactivation_rejects_assigned_vehicle(self):
        self.user.role = "DISPATCHER"
        current = SimpleNamespace(driver_id="D",company_id="COMP_TEST",full_name="Tài xế",
                                  license_number="B2",phone="090000",active=True)
        assigned = SimpleNamespace(vehicle_id="V", current_driver_id="D")
        previous = self.execute
        def execute(statement, parameters=()):
            if isinstance(statement, str) and "FROM drivers_by_id" in statement:
                return Rows([current])
            if isinstance(statement, str) and "FROM vehicles_by_status" in statement:
                return Rows([assigned])
            return previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            result = self.client.patch("/api/fleet/drivers/D", headers=self.headers,
                                       json={"active":False})
        self.assertEqual(result.status_code, 409)
        self.assertFalse(any(isinstance(statement, BatchStatement) for statement, _ in self.calls))

    def test_dispatcher_updates_both_driver_projections(self):
        self.user.role = "DISPATCHER"
        current = SimpleNamespace(driver_id="D",company_id="COMP_TEST",full_name="Tài xế",
                                  license_number="B2",phone="090000",active=True)
        previous = self.execute
        def execute(statement, parameters=()):
            if isinstance(statement, str) and "FROM drivers_by_id" in statement:
                return Rows([current])
            return previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            result = self.client.patch("/api/fleet/drivers/D", headers=self.headers,
                                       json={"full_name":"Tài xế mới"})
        self.assertEqual(result.status_code, 200)
        batches = [statement for statement, _ in self.calls if isinstance(statement, BatchStatement)]
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]._statements_and_parameters), 2)

    def test_dispatcher_creates_planned_trip_in_three_projections(self):
        self.user.role = "DISPATCHER"
        vehicle = SimpleNamespace(company_id="COMP_TEST", status="IDLE", current_driver_id="D")
        driver = SimpleNamespace(company_id="COMP_TEST", active=True)
        previous = self.execute
        def execute(statement, parameters=()):
            if isinstance(statement, str) and "FROM vehicles_by_id" in statement:
                return Rows([vehicle])
            if isinstance(statement, str) and "FROM drivers_by_id" in statement:
                return Rows([driver])
            return previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            result = self.client.post("/api/fleet/trips", headers=self.headers, json={
                "trip_id":"T_NEW","vehicle_id":"V","driver_id":"D",
                "origin":"Điểm A","destination":"Điểm B"})
        self.assertEqual(result.status_code, 201)
        batches = [statement for statement, _ in self.calls if isinstance(statement, BatchStatement)]
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]._statements_and_parameters), 3)
        self.assertTrue(all("COMP_TEST" in query for _, query, _ in batches[0]._statements_and_parameters))

    def test_trip_driver_must_be_assigned_to_vehicle(self):
        self.user.role = "DISPATCHER"
        vehicle = SimpleNamespace(company_id="COMP_TEST", status="IDLE", current_driver_id="D_OTHER")
        driver = SimpleNamespace(company_id="COMP_TEST", active=True)
        previous = self.execute
        def execute(statement, parameters=()):
            if isinstance(statement, str) and "FROM vehicles_by_id" in statement:
                return Rows([vehicle])
            if isinstance(statement, str) and "FROM drivers_by_id" in statement:
                return Rows([driver])
            return previous(statement, parameters)
        with patch.object(db, "execute", side_effect=execute):
            result = self.client.post("/api/fleet/trips", headers=self.headers, json={
                "trip_id":"T_NEW","vehicle_id":"V","driver_id":"D",
                "origin":"Điểm A","destination":"Điểm B"})
        self.assertEqual(result.status_code, 422)
        self.assertFalse(any(isinstance(statement, BatchStatement) for statement, _ in self.calls))

    def test_unauthenticated_gps_is_rejected(self):
        self.assertEqual(self.client.post("/api/tracking/ingest", json={}).status_code, 401)

    def test_disabled_account_token_is_rejected(self):
        self.user.active = False
        self.assertEqual(self.client.get("/api/auth/me", headers=self.headers).status_code, 401)

    def test_invalid_token_is_rejected(self):
        result = self.client.get("/api/auth/me", headers={"Authorization":"Bearer broken"})
        self.assertEqual(result.status_code, 401)

    def test_company_is_read_from_db_and_fleet_uses_partitions(self):
        result = self.client.get("/api/fleet/vehicles", headers=self.headers)
        self.assertEqual(result.status_code, 200)
        queries = [(sql, values) for sql, values in self.calls if sql != "LOGIN"]
        self.assertEqual(len(queries), 4)
        self.assertTrue(all(values[0] == "COMP_TEST" for _, values in queries))
        self.assertTrue(all("WHERE company_id" in sql and "vehicles_by_status" in sql for sql, _ in queries))

    def test_invalid_vehicle_status_is_422(self):
        self.assertEqual(self.client.get("/api/fleet/vehicles?status=invalid", headers=self.headers).status_code, 422)

    def test_invalid_trip_date_is_422(self):
        self.assertEqual(self.client.get("/api/fleet/trips?trip_date=invalid", headers=self.headers).status_code, 422)

    def test_password_hash_is_salted_and_rejects_legacy_sha256(self):
        another = hash_password("Password123@")
        self.assertNotEqual(another, self.password_hash)
        self.assertTrue(verify_password("Password123@", another))
        self.assertFalse(verify_password("wrong", another))
        self.assertFalse(verify_password("Password123@", "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"))

if __name__ == "__main__":
    unittest.main()
