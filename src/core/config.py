from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Tuple
from selenium.webdriver.common.by import By


class Config:
	DEFAULTS: Dict[str, Any] = {
		"login_url": "https://www.my-auction.co.kr/member/login.php",
		"search_url": "https://www.my-auction.co.kr/auction/search.php",
		"username": "",
		"password": "",
		"saved_search_name": "",
		"headless": False,
		"debug": False,
		"debug_dir": "debug",
		"step_delay_sec": 0.0,
		"random_delay_range_ms": [800, 2200],
		"user_agents": [
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
			"Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
			"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
		],
		"accept_languages": ["ko-KR,ko;q=0.9", "en-US,en;q=0.8"],
		"locators": {
			"username_field": ["id", "id"],
			"password_field": ["id", "passwd"],
			"login_button": ["id", "btn_login"],
			"search_form": ["id", "searchForm"],
		},
		"output_dir": "output",
	}

	def __init__(self, data: Dict[str, Any]):
		self._data = data

	@classmethod
	def load(cls, config_file: str = "config.json") -> "Config":
		base = dict(cls.DEFAULTS)
		path = Path(config_file)
		if path.exists():
			with path.open("r", encoding="utf-8") as f:
				file_data = json.load(f)
				for k, v in file_data.items():
					if isinstance(v, dict) and k in base:
						base[k].update(v)
					else:
						base[k] = v
		return cls(base)

	def get(self, key: str, default: Any = None) -> Any:
		return self._data.get(key, default)

	def get_locator(self, pair: list[str]) -> Tuple[By, str]:
		by_map = {
			"id": By.ID,
			"name": By.NAME,
			"css": By.CSS_SELECTOR,
			"xpath": By.XPATH,
			"class": By.CLASS_NAME,
			"tag": By.TAG_NAME,
		}
		by, value = pair[0].lower(), pair[1]
		return by_map[by], value

	@property
	def data(self) -> Dict[str, Any]:
		return self._data
