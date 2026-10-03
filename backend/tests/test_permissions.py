"""Unit/API regression checks with a fake DB, not Scylla integration evidence."""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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
