from __future__ import annotations
import csv
from pathlib import Path
from typing import List, Dict, Optional
from src.utils.gallery import build_gallery_html


def _sanitize_cell_value(val: object) -> str:
	text = "" if val is None else str(val)
	# Prevent CSV Formula Injection
	if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
		return f"'{text}"
	return text


def write_csv(path: Path | str, items: List[Dict], columns: List[str]) -> Path:
	"""Write items to a CSV file encoded in UTF-8 with BOM (utf-8-sig) for Excel compatibility."""
	out_path = Path(path)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	with out_path.open("w", encoding="utf-8-sig", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(columns)
		for item in items:
			row = [_sanitize_cell_value(item.get(col, "")) for col in columns]
			writer.writerow(row)
	return out_path


def build_html_from_csv(
	csv_rel_path: str,
	title: str,
	subtitle: str,
	output_html_path: Path | str,
	items: Optional[List[Dict]] = None,
) -> Path:
	"""Build interactive gallery HTML from either supplied items or reading the CSV file."""
	out_path = Path(output_html_path)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	if items is None:
		csv_file = out_path.parent / csv_rel_path
		items = []
		if csv_file.exists():
			with csv_file.open("r", encoding="utf-8-sig", newline="") as f:
				reader = csv.DictReader(f)
				for row in reader:
					# Clean leading quote prefix if sanitized
					cleaned_row = {}
					for k, v in row.items():
						cleaned_row[k] = v[1:] if v and v.startswith("'") else v
					items.append(cleaned_row)
	build_gallery_html(items, title, subtitle, out_path)
	return out_path
