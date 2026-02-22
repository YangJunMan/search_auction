import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from selenium.webdriver.support.ui import WebDriverWait
from src.core.config import Config
from src.core.driver import create_driver
from src.utils.file_handler import save_json
from src.automation.login import LoginHandler
from src.automation.navigation import Navigator
from src.automation.search import SearchHandler
from src.scraping.parser import DataParser
from src.scraping.collector import DataCollector
from src.utils.recommendation import ensure_kakao_key_from_config, run_recommendations_from_config

# --- 로깅 설정 ---
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"crawler_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def close_driver(driver) -> None:
    if driver:
        driver.quit()
        logger.info("브라우저를 종료했습니다.")


def save_results(results: List[Dict], output_dir: Path, filename: str = "search_results") -> Optional[Path]:
    """결과 리스트를 JSON 파일로 저장 (utils.save_json 사용)"""
    if not results:
        logger.warning("저장할 결과가 없습니다.")
        return None
    filepath = save_json(results, output_dir, filename_prefix=filename)
    logger.info(f"총 {len(results)}개의 항목을 {filepath}에 저장했습니다.")
    return filepath


def main():
    """크롤러 메인 실행 함수"""
    cfg = Config.load('config.json')

    # Kakao 키 설정: CLI/환경변수 우선, 없으면 config.json에서 읽어 주입
    ensure_kakao_key_from_config(cfg.data)
    driver = create_driver(
        headless=bool(cfg.get("headless", False)),
        user_agents=cfg.get("user_agents", []),
        accept_languages=cfg.get("accept_languages", []),
    )
    try:
        driver.set_page_load_timeout(30)
    except Exception:
        pass
    wait = WebDriverWait(driver, 15)

    try:
        # 1. 로그인
        creds = {"username": cfg.get("username"), "password": cfg.get("password")}
        login = LoginHandler(driver=driver, wait=wait, element_timeout=15)
        login.login(cfg.get("login_url"), creds, cfg.get("locators"))

        # 2. 검색 페이지로 이동
        search_page_container_locator = cfg.get_locator(["id", "search_condition"])
        navigator = Navigator(driver=driver, wait=wait, element_timeout=15)
        navigator.navigate_to_page(cfg.get("search_url"), search_page_container_locator)

        # 3. 검색 수행: search_options 우선, 없으면 저장 검색 사용
        scraped_items: List[Dict] = []
        search_options: Optional[Dict] = cfg.get("search_options")
        search = SearchHandler(driver=driver, wait=wait, element_timeout=15)
        if search_options:
            logger.info("config.search_options 기반으로 검색을 진행합니다.")
            search.apply_search_options(search_options)
        else:
            logger.info("저장된 검색 조건을 사용하여 검색을 진행합니다.")
            if not search.click_saved_search(cfg.get("saved_search_name")):
                raise Exception("저장된 검색 조건 클릭 실패")

        parser = DataParser(driver=driver, wait=wait)
        collector = DataCollector(driver=driver, wait=wait, parser=parser)
        scraped_items = collector.collect_all_pages()

        # 5. 결과 저장 (원본) - 실행마다 고유 하위 폴더 생성
        output_root = Path(cfg.get("output_dir"))
        run_output_dir = output_root / timestamp
        run_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"이번 실행 출력 폴더: {run_output_dir}")
        saved_path = save_results(scraped_items, run_output_dir)

        # 6. 역 주변 추천 산출 및 HTML 생성 (오케스트레이션을 모듈로 위임)
        run_recommendations_from_config(
            config_dict=cfg.data,
            items=scraped_items,
            saved_path=saved_path,
            output_dir=run_output_dir,
            logger=logger,
        )

    except Exception as e:
        logger.exception(f"크롤링 작업 중 심각한 오류 발생: {e}")
    finally:
        close_driver(driver)


if __name__ == "__main__":
    main()