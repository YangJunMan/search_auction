from __future__ import annotations
from typing import Dict
from selenium.webdriver.support import expected_conditions as EC
from src.automation.base import BaseAutomation


class LoginHandler(BaseAutomation):
	def login(self, url: str, creds: Dict, locators: Dict) -> bool:
		def _attempt():
			self.driver.get(url)
			user_loc = self.get_locator(locators['username_field'])
			pass_loc = self.get_locator(locators['password_field'])
			btn_loc = self.get_locator(locators['login_button'])
			self.wait.until(EC.presence_of_element_located(user_loc)).send_keys(creds['username'])
			self.wait.until(EC.presence_of_element_located(pass_loc)).send_keys(creds['password'])
			self.wait.until(EC.element_to_be_clickable(btn_loc)).click()
			self.wait.until(EC.url_changes(url))
			return True
		return bool(self.retry_on_failure(_attempt))
