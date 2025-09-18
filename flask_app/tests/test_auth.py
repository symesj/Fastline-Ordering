import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "flask_app"))

TEST_USERNAME = "test-user"
TEST_PASSWORD = "secret-pass"
os.environ["AUTH_USERNAME"] = TEST_USERNAME
os.environ["AUTH_PASSWORD"] = TEST_PASSWORD
os.environ["FLASK_SECRET_KEY"] = "unit-test-secret"

from flask_app.app import app  # noqa: E402  (import after env configuration)


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.login_payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
        self.email_payload = {
            "to": "user@example.com",
            "subject": "Unit Test",
            "html_body": "<p>Hello</p>",
            "fromUser": "sender@example.com",
            "attachments": [],
        }

    def test_login_success_sets_session_cookie(self):
        response = self.client.post("/api/auth/login", json=self.login_payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("ok"))
        cookie_header = response.headers.get("Set-Cookie", "")
        self.assertIn("session=", cookie_header)

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": TEST_USERNAME, "password": "wrong"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.get_json().get("error", ""))

    def test_login_requires_json_body(self):
        response = self.client.post("/api/auth/login", data="not-json", content_type="text/plain")
        self.assertEqual(response.status_code, 400)

    def test_protected_route_respects_session_and_logout(self):
        with patch("flask_app.app.send_email_via_graph", return_value="msg-id") as mocked_send:
            forbidden = self.client.post("/send-email", json=self.email_payload)
            self.assertEqual(forbidden.status_code, 403)
            self.assertEqual(mocked_send.call_count, 0)

            login = self.client.post("/api/auth/login", json=self.login_payload)
            self.assertEqual(login.status_code, 200)

            allowed = self.client.post("/send-email", json=self.email_payload)
            self.assertEqual(allowed.status_code, 200)
            self.assertEqual(mocked_send.call_count, 1)

            logout = self.client.post("/api/auth/logout")
            self.assertEqual(logout.status_code, 200)

            again_forbidden = self.client.post("/send-email", json=self.email_payload)
            self.assertEqual(again_forbidden.status_code, 403)
            self.assertEqual(mocked_send.call_count, 1)


if __name__ == "__main__":
    unittest.main()
