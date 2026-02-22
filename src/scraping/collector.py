from __future__ import annotations
from typing import List, Dict, Optional
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .parser import DataParser


class DataCollector:
	def __init__(self, driver: WebDriver, wait: WebDriverWait, parser: DataParser):
		self.driver = driver
		self.wait = wait
		self.parser = parser

	def collect_all_pages(self, max_pages: Optional[int] = None) -> List[Dict]:
		collected: List[Dict] = []
		visited_urls = set()
		page_counter = 0
		last_page: Optional[int] = None

		def get_current_page() -> int:
			# DOM에서 현재 페이지 읽기 (#youtube_number a[href="#none"])
			try:
				active = self.driver.find_element(By.CSS_SELECTOR, "#youtube_number a[href='#none']")
				text = (active.text or "").strip()
				return int(text)
			except Exception:
				# URL 파라미터에서 읽기
				u = urlparse(self.driver.current_url)
				qs = parse_qs(u.query)
				return int(qs.get("page", ["1"])[0])

		def get_last_page() -> Optional[int]:
			# 끝 페이지 버튼의 href에서 page 추출
			try:
				end_link = self.driver.find_element(By.CSS_SELECTOR, "#youtube_number a.ytb_end")
				href = end_link.get_attribute("href")
				u = urlparse(href)
				qs = parse_qs(u.query)
				return int(qs.get("page", [None])[0]) if qs.get("page") else None
			except Exception:
				return None

		def wait_for_page(target_page: int, timeout_sec: float = 5.0) -> bool:
			end_time = time.time() + timeout_sec
			while time.time() < end_time:
				try:
					if get_current_page() == target_page:
						return True
				except Exception:
					pass
				time.sleep(0.25)
			return False

		def click_numeric_page(target_page: int) -> bool:
			"""현재 보이는 페이지네이션에서 숫자 페이지를 클릭. 없으면 ytb_next를 클릭해 그룹 이동을 시도."""
			attempts = 0
			while attempts < 10:
				attempts += 1
				# 1) 숫자 링크 시도
				links = self.driver.find_elements(By.CSS_SELECTOR, "#youtube_number a")
				for a in links:
					label = (a.text or "").strip()
					if label == str(target_page) and a.get_attribute("href") != "#none":
						self.driver.execute_script("arguments[0].click();", a)
						self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.tbl_auction_list")))
						return wait_for_page(target_page, timeout_sec=5.0)
				# 2) 다음 그룹 이동
				next_group = self.driver.find_elements(By.CSS_SELECTOR, "#youtube_number a.ytb_next")
				if not next_group:
					return False
				self.driver.execute_script("arguments[0].click();", next_group[0])
				self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#youtube_number")))
				time.sleep(0.2)
			# 실패
			return False

		while True:
			page_counter += 1
			collected.extend(self.parser.parse_current_page())
			if max_pages and page_counter >= max_pages:
				break

			if last_page is None:
				last_page = get_last_page()

			# 다음 페이지 번호 계산
			try:
				current_page = get_current_page()
			except Exception:
				current_page = page_counter
			next_page = current_page + 1
			if last_page and next_page > last_page:
				break


			# 1) 페이지네이션 영역에서 숫자 링크 클릭 우선 시도 (필요시 그룹 이동 포함)
			clicked = click_numeric_page(next_page)

			# 2) 숫자 링크가 없으면 URL의 page 파라미터 증가 시도 (폴백)
			if not clicked:
				u = urlparse(self.driver.current_url)
				qs = parse_qs(u.query)
				qs["page"] = [str(next_page)]
				next_url = urlunparse((u.scheme, u.netloc, u.path, u.params, urlencode(qs, doseq=True), u.fragment))
				if next_url in visited_urls:
					break
				visited_urls.add(next_url)
				time.sleep(0.15 + (next_page % 3) * 0.1)
				self.driver.get(next_url)
				self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.tbl_auction_list")))

		return collected
