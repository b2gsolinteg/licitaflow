import unittest

from src.db_runtime import translate_sql


class PostgresDateTranslationTests(unittest.TestCase):
    def test_translates_positive_literal_datetime_offset(self):
        sql = translate_sql(
            "UPDATE access_requests "
            "SET invitation_expires_at=datetime('now', '+7 days') "
            "WHERE id=?"
        )

        self.assertNotIn("datetime(", sql.lower())
        self.assertIn("CURRENT_TIMESTAMP + INTERVAL '+7 days'", sql)
        self.assertIn("id=%s", sql)

    def test_translates_negative_literal_datetime_offset(self):
        sql = translate_sql(
            "SELECT * FROM sessions "
            "WHERE expires_at > datetime('now', '-24 hours')"
        )

        self.assertNotIn("datetime(", sql.lower())
        self.assertIn("CURRENT_TIMESTAMP + INTERVAL '-24 hours'", sql)


if __name__ == "__main__":
    unittest.main()
