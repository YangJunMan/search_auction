import unittest
import tempfile
import csv
from pathlib import Path
from src.utils.report import write_csv, build_html_from_csv


class TestReport(unittest.TestCase):
    def test_write_csv_sanitizes_formula_injection(self):
        items = [
            {"사건번호": "=cmd|' /C calc'!A0", "소재지": "인천 부평구", "최저가": "100000000"},
            {"사건번호": "2024타경12345", "소재지": "+위험수식", "최저가": "200000000"},
        ]
        columns = ["사건번호", "소재지", "최저가"]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "output.csv"
            write_csv(out_file, items, columns)
            self.assertTrue(out_file.exists())

            with out_file.open("r", encoding="utf-8-sig") as f:
                reader = list(csv.reader(f))
                self.assertEqual(reader[0], columns)
                # Ensure prefixed with single quote to prevent execution in spreadsheet software
                self.assertTrue(reader[1][0].startswith("'="))
                self.assertTrue(reader[2][1].startswith("'+"))

    def test_build_html_from_csv(self):
        items = [
            {"사건번호": "2024타경9999", "소재지": "서울 강남구", "용도": "아파트", "최저가": "5억"}
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            html_path = Path(tmpdir) / "test.html"
            write_csv(csv_path, items, ["사건번호", "소재지", "용도", "최저가"])

            build_html_from_csv(csv_path.name, "테스트 제목", "테스트 부제목", html_path, items=items)
            self.assertTrue(html_path.exists())
            content = html_path.read_text(encoding="utf-8")
            self.assertIn("테스트 제목", content)
            self.assertIn("2024타경9999", content)


if __name__ == "__main__":
    unittest.main()
