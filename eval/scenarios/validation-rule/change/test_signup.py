import unittest

from signup import validate_password


class PasswordValidationTests(unittest.TestCase):
    def test_eleven_characters_still_rejected(self):
        with self.assertRaises(ValueError):
            validate_password("a" * 11)

    def test_twelve_characters_accepted(self):
        validate_password("a" * 12)


if __name__ == "__main__":
    unittest.main()
