import importlib
import os
import unittest

os.environ["ADMIN_USERNAME"] = "admin-user"
os.environ["ADMIN_PASSWORD"] = "top-secret"

service = importlib.import_module("ghl_sync_orders_flask_service")
service = importlib.reload(service)


class LoginTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = service.app.test_client()

    def test_login_success(self):
        response = self.client.post(
            "/login", json={"username": "admin-user", "password": "top-secret"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("token", data)
        self.assertTrue(data["token"])
        self.assertIn("expires_at", data)

    def test_login_failure(self):
        response = self.client.post(
            "/login", json={"username": "admin-user", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
