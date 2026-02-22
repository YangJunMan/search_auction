from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def save_json(items: List[Dict], output_dir: Path, filename_prefix: str = "search_results") -> Path:
	if not items:
		raise ValueError("No items to save")
	output_dir.mkdir(exist_ok=True)
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	path = output_dir / f"{filename_prefix}_{timestamp}.json"
	with path.open('w', encoding='utf-8') as f:
		json.dump(items, f, ensure_ascii=False, indent=4)
	return path
