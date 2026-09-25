import sqlite3
import unittest

from users import connect, get_profile


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.execute("INSERT INTO users (id, email) VALUES (1, 'a@example.invalid')")

    def test_each_user_has_at_most_one_profile(self):
        self.db.execute("INSERT INTO profiles (user_id, display_name) VALUES (1, 'A')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO profiles (user_id, display_name) VALUES (1, 'B')")

    def test_get_profile_returns_none_when_missing(self):
        self.assertIsNone(get_profile(self.db, 1))


if __name__ == "__main__":
    unittest.main()
