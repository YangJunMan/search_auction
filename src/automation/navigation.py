from __future__ import annotations
from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from src.automation.base import BaseAutomation
import time, random


class Navigator(BaseAutomation):
	def navigate_to_page(self, url: str, wait_for_locator: Tuple[By, str]) -> bool:
		def _nav():
			# human-like delay
			time.sleep(random.uniform(0.2, 0.8))
			self.driver.get(url)
			self.wait.until(EC.presence_of_element_located(wait_for_locator))
			# small idle
			time.sleep(random.uniform(0.2, 0.6))
			return True
		return bool(self.retry_on_failure(_nav))
