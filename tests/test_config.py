import unittest
from src.core.config import Config


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = Config.load("non_existent_config.json")
        self.assertEqual(cfg.get("login_url"), "https://www.my-auction.co.kr/member/login.php")
        self.assertFalse(cfg.get("headless"))
        self.assertEqual(cfg.get("output_dir"), "output")

    def test_get_locator(self):
        cfg = Config({})
        by, value = cfg.get_locator(["id", "search_btn"])
        self.assertEqual(value, "search_btn")


if __name__ == "__main__":
    unittest.main()
