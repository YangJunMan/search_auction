from __future__ import annotations
from typing import Dict, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from src.automation.base import BaseAutomation


class SearchHandler(BaseAutomation):
	def click_saved_search(self, search_name: str) -> bool:
		def _click_attempt():
			my_searches_tab_locator = (By.XPATH, "//div[@id='sc_tab']//a[normalize-space()='내 검색조건']")
			self.wait.until(EC.element_to_be_clickable(my_searches_tab_locator)).click()
			saved_search_locator = (By.XPATH, f"//div[@id='sc_list']//a[normalize-space()='{search_name}']")
			button = self.wait.until(EC.presence_of_element_located(saved_search_locator))
			onclick_script = button.get_attribute("onclick")
			if not onclick_script:
				raise Exception("saved search onclick not found")
			self.driver.execute_script(onclick_script)
			self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tbl_auction_list")))
			return True
		return bool(self.retry_on_failure(_click_attempt))

	def apply_search_options(self, options: Dict) -> bool:
		def _apply():
			self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#search_form, #searchForm")))
			def set_value_by_name(name: str, value: str):
				el = self.driver.find_element(By.NAME, name)
				if el.tag_name.lower() == 'select':
					Select(el).select_by_value(str(value))
					return
				self.driver.execute_script("arguments[0].value = arguments[1];", el, str(value))
			def set_checkboxes(group_name: str, values: List[str]):
				for cb in self.driver.find_elements(By.CSS_SELECTOR, f"input[name='{group_name}'][type='checkbox']"):
					if cb.is_selected():
						self.driver.execute_script("arguments[0].click();", cb)
				for val in values:
					for el in self.driver.find_elements(By.CSS_SELECTOR, f"input[name='{group_name}'][type='checkbox'][value='{val}']"):
						if not el.is_selected():
							self.driver.execute_script("arguments[0].click();", el)
			for group in ["usage_code", "spe", "gm"]:
				if group in options and isinstance(options[group], list):
					set_checkboxes(group, [str(v) for v in options[group]])
			for k, v in options.items():
				if k in ["usage_code", "spe", "gm"]:
					continue
				set_value_by_name(k, str(v))
			search_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#search_btn button")))
			self.driver.execute_script("arguments[0].click();", search_btn)
			self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.tbl_auction_list")))
			return True
		return bool(self.retry_on_failure(_apply))
