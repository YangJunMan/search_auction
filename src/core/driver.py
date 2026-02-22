from __future__ import annotations
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import Optional, Tuple
import random


def pick_random_ua_and_lang(user_agents: list[str], accept_languages: list[str]) -> Tuple[str, str]:
	ua = random.choice(user_agents) if user_agents else ""
	lang = random.choice(accept_languages) if accept_languages else ""
	return ua, lang


def create_driver(headless: bool = False, user_agents: list[str] | None = None, accept_languages: list[str] | None = None) -> webdriver.Chrome:
	options = Options()
	options.add_argument('--no-sandbox')
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument('--disable-extensions')
	options.add_argument('--disable-popup-blocking')
	if headless:
		options.add_argument('--headless=new')

	ua, lang = pick_random_ua_and_lang(user_agents or [], accept_languages or [])
	if ua:
		options.add_argument(f'--user-agent={ua}')
	if lang:
		options.add_argument(f'--lang={lang}')

	# Selenium Manager handles driver
	driver = webdriver.Chrome(options=options)
	return driver
