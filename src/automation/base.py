from __future__ import annotations
from typing import Callable, Any, List, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import random, time


class BaseAutomation:
	def __init__(self, driver: WebDriver, wait: WebDriverWait, element_timeout: int = 15, max_retries: int = 3, retry_delay: float = 2.0):
		self.driver = driver
		self.wait = wait
		self.element_timeout = element_timeout
		self.max_retries = max_retries
		self.retry_delay = retry_delay

	def retry_on_failure(self, func: Callable, *args, **kwargs) -> Any:
		last_e: Exception | None = None
		for _ in range(self.max_retries):
			try:
				return func(*args, **kwargs)
			except Exception as e:
				last_e = e
				# 지수 백오프 + 지터
				delay = self.retry_delay * (1.5) + random.uniform(0, self.retry_delay)
				time.sleep(delay)
		if last_e:
			raise last_e
		return None

	@staticmethod
	def get_locator(locator_info: List[str]) -> Tuple[By, str]:
		by_map = {
			"id": By.ID,
			"name": By.NAME,
			"css": By.CSS_SELECTOR,
			"xpath": By.XPATH,
			"class": By.CLASS_NAME,
			"tag": By.TAG_NAME,
		}
		by, value = locator_info[0].lower(), locator_info[1]
		return by_map[by], value
