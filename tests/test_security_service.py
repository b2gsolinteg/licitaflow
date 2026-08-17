import os
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("LICITANEXO_DB_BACKEND", "sqlite")

from src.security_rc25 import RateLimitError, SecurityService, SessionExpiredError


class SecurityServiceTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.path = Path(handle.name)
        self.security = SecurityService(self.path, self.path.parent)

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_session_roundtrip_and_revocation(self):
        token = self.security.create_session("c1", "u1")
        self.assertTrue(self.security.validate_session(token))
        self.security.revoke_session(token)
        with self.assertRaises(SessionExpiredError):
            self.security.validate_session(token)

    def test_successful_attempt_clears_failure_bucket(self):
        self.security.register_attempt(
            "login", "user@example.com", "127.0.0.1", success=False
        )
        self.security.register_attempt(
            "login", "user@example.com", "127.0.0.1", success=True
        )
        self.assertTrue(
            self.security.precheck("login", "user@example.com", "127.0.0.1")
        )

    def test_login_is_blocked_after_maximum_failures(self):
        for _ in range(self.security.LOGIN_MAX_FAILURES - 1):
            self.security.register_attempt(
                "login", "blocked@example.com", "10.0.0.1", success=False
            )
        with self.assertRaises(RateLimitError):
            self.security.register_attempt(
                "login", "blocked@example.com", "10.0.0.1", success=False
            )
        with self.assertRaises(RateLimitError):
            self.security.precheck("login", "blocked@example.com", "10.0.0.1")

    def test_metrics_count_active_session_and_failures(self):
        self.security.create_session("c1", "u1")
        self.security.register_attempt(
            "login", "metrics@example.com", "127.0.0.2", success=False
        )
        metrics = self.security.metrics()
        self.assertGreaterEqual(metrics["active_sessions"], 1)
        self.assertGreaterEqual(metrics["failed_24h"], 1)


if __name__ == "__main__":
    unittest.main()
