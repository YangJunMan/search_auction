import unittest
from src.utils.geo import haversine_m
from src.utils.geo_ops import default_address_normalizer, compute_distances


class TestGeo(unittest.TestCase):
    def test_haversine_distance(self):
        # Distance between Seoul City Hall and Gwanghwamun is roughly 1km
        lat1, lon1 = 37.5665, 126.9780
        lat2, lon2 = 37.5759, 126.9768
        dist = haversine_m(lat1, lon1, lat2, lon2)
        self.assertTrue(900 < dist < 1200)

    def test_address_normalizer(self):
        raw = "인천광역시 부평구 부평동 123 (부평아파트) 101동 502호"
        normalized = default_address_normalizer(raw)
        self.assertNotIn("(", normalized)
        self.assertNotIn(")", normalized)
        self.assertNotIn("502호", normalized)

    def test_compute_distances(self):
        stations = {
            "부평역": (37.4895, 126.7248),
            "부천역": (37.4840, 126.7827),
        }
        items = [
            {"소재지": "부평역 앞", "lat": 37.4896, "lng": 126.7249},
            {"소재지": "좌표 없음", "lat": None, "lng": None},
        ]
        compute_distances(items, stations, radius_m=400)
        self.assertEqual(items[0]["최근접역"], "부평역")
        self.assertTrue(items[0]["추천"])
        self.assertTrue(items[0]["역까지거리_m"] < 100)

        self.assertIsNone(items[1]["최근접역"])
        self.assertFalse(items[1]["추천"])


if __name__ == "__main__":
    unittest.main()
