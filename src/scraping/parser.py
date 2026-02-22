from __future__ import annotations
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DataParser:
	def __init__(self, driver: WebDriver, wait: WebDriverWait):
		self.driver = driver
		self.wait = wait

	def parse_current_page(self) -> List[Dict]:
		items: List[Dict] = []
		rows = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.tbl_auction_list tbody tr")))
		for row in rows:
			cells = row.find_elements(By.TAG_NAME, 'td')
			if len(cells) < 8:
				continue
			case_info = cells[2].text.strip().split('\n')
			location_info = cells[3].find_elements(By.TAG_NAME, 'li')
			# 면적 추출 (예: "건물 870.60평   토지 623.79평")
			area_text = ""
			try:
				if len(location_info) > 1:
					p_elems = location_info[1].find_elements(By.TAG_NAME, 'p')
					if p_elems:
						area_text = p_elems[0].text.strip()
			except Exception:
				area_text = ""
			# 특수권리 추출 (span.refer a들의 텍스트 합치기)
			special_rights = ""
			try:
				anchors = cells[3].find_elements(By.CSS_SELECTOR, "span.refer a")
				labels = [a.text.strip() for a in anchors if (a.text or '').strip()]
				special_rights = " ".join(labels)
			except Exception:
				special_rights = ""
			price_info = cells[4].text.strip().split('\n')
			current_status = cells[5].text.strip()
			data = {
				'용도': cells[2].find_element(By.TAG_NAME, 'strong').text.strip(),
				'사건번호': case_info[1] if len(case_info) > 1 else 'N/A',
				'소재지': location_info[0].text.strip() if location_info else 'N/A',
				'감정가': price_info[0] if price_info else 'N/A',
				'최저가': price_info[1] if len(price_info) > 1 else 'N/A',
				'매각기일': cells[6].text.strip().split('\n')[0],
				'면적': area_text,
				'특수권리': special_rights,
				'현재상태': current_status,
			}
			items.append(data)
		return items
