import unittest
import tempfile
from pathlib import Path
from src.utils.gallery import build_gallery_html


class TestGallery(unittest.TestCase):
    def test_safe_escaping_against_script_injection(self):
        malicious_items = [
            {
                "사건번호": "</script><script>alert('xss')</script>",
                "소재지": "인천 부평구",
                "용도": "아파트",
                "감정가": "200,000,000",
                "최저가": "140,000,000",
                "매각기일": "2026-11-20",
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "gallery.html"
            build_gallery_html(
                malicious_items,
                title="<script>alert(1)</script>경매",
                subtitle="부제목",
                output_html_path=out_file,
            )
            self.assertTrue(out_file.exists())
            html = out_file.read_text(encoding="utf-8")
            # Raw unescaped <script> tag from title must not exist
            self.assertNotIn("<title><script>alert(1)</script>", html)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
            # Raw </script> inside JSON in inline script must be safely escaped
            self.assertNotIn("</script><script>alert('xss')", html)
            self.assertIn("<\\/script>", html)


if __name__ == "__main__":
    unittest.main()
