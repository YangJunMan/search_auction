# 크롤러 코드 최적화 및 모듈화 설계

## 현재 구조 분석 (crawler.py - 368 lines)

### 주요 구성 요소
1. **설정 관리** (25-57행)
   - `load_app_config()`: 설정 파일 로딩 및 기본값 병합

2. **WebsiteCrawler 클래스** (60-344행)
   - 드라이버 초기화 (`_init_driver`)
   - 디버그 기능 (`_debug_capture`, `_delay`)
   - 기본 유틸리티 (`_retry_on_failure`, `_get_locator`)
   - 웹 액션 (`login`, `navigate_to_page`)
   - 검색 기능 (`click_saved_search`, `apply_search_options`)
   - 데이터 수집 (`scrape_all_items`, `scrape_all_pages`)

3. **유틸리티 함수** (347-358행)
   - `save_results()`: JSON 저장

4. **메인 실행** (361-406행)
   - `main()`: 전체 워크플로우 실행

## 문제점
- 단일 파일에 모든 기능이 집중 (368줄)
- 책임이 명확히 분리되지 않음
- 테스트 및 유지보수 어려움
- 재사용성 부족

## 최적화된 모듈 구조 설계

### 1. 핵심 모듈 분리

```
src/
├── core/
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   ├── driver.py          # 웹드라이버 관리
│   └── debug.py           # 디버그 및 로깅
├── automation/
│   ├── __init__.py
│   ├── base.py            # 기본 자동화 클래스
│   ├── login.py           # 로그인 처리
│   ├── search.py          # 검색 처리
│   └── navigation.py      # 페이지 이동
├── scraping/
│   ├── __init__.py
│   ├── parser.py          # 데이터 파싱
│   └── collector.py       # 페이지네이션 수집
├── utils/
│   ├── __init__.py
│   ├── file_handler.py    # 파일 저장/로딩
│   └── locators.py        # 셀렉터 관리
└── main.py                # 메인 실행 파일
```

### 2. 각 모듈 책임

#### core/config.py (~50줄)
- 설정 파일 로딩
- 기본값 관리
- 환경별 설정 지원

#### core/driver.py (~60줄)
- 웹드라이버 초기화
- 드라이버 옵션 관리
- 재시도 로직

#### core/debug.py (~40줄)
- 스크린샷 캡처
- HTML 저장
- 단계별 지연
- 로깅 설정

#### automation/base.py (~80줄)
- 기본 자동화 기능
- 요소 대기
- 공통 액션

#### automation/login.py (~30줄)
- 로그인 처리 전용

#### automation/search.py (~60줄)
- 저장 검색 실행
- 옵션 검색 (향후 확장용)

#### automation/navigation.py (~40줄)
- 페이지 이동
- URL 변경 감지

#### scraping/parser.py (~50줄)
- 테이블 데이터 파싱
- 항목 추출 로직

#### scraping/collector.py (~60줄)
- 페이지네이션 처리
- 전체 데이터 수집

#### utils/file_handler.py (~30줄)
- JSON 저장/로딩
- 결과 파일 관리

#### utils/locators.py (~20줄)
- 셀렉터 변환
- 로케이터 관리

#### main.py (~50줄)
- 워크플로우 조합
- 에러 처리

### 3. 모듈 간 의존성

```
main.py
├── core.config
├── core.driver
├── core.debug
├── automation.login
├── automation.search
├── automation.navigation
├── scraping.collector
└── utils.file_handler

automation.* → core.driver, core.debug
scraping.* → core.driver, core.debug
utils.* → core.config
```

### 4. 장점

1. **단일 책임 원칙**: 각 모듈이 명확한 역할
2. **재사용성**: 독립적인 모듈로 다른 프로젝트에서도 활용
3. **테스트 용이성**: 모듈별 단위 테스트 가능
4. **유지보수성**: 변경사항을 특정 모듈에만 적용
5. **확장성**: 새로운 검색 방식이나 사이트 추가 시 해당 모듈만 확장

### 5. 마이그레이션 전략

1. **1단계**: 설정 및 드라이버 모듈 분리
2. **2단계**: 자동화 기능별 모듈 분리
3. **3단계**: 스크래핑 로직 분리
4. **4단계**: 유틸리티 및 메인 정리
5. **5단계**: 테스트 코드 작성

### 6. 예상 파일 크기
- 가장 큰 모듈: automation/base.py (~80줄)
- 평균 모듈 크기: ~45줄
- 전체 코드량: 유지 (구조만 개선)
- 최대 단일 파일: 80줄 이하

이 구조로 리팩토링하면 코드의 가독성, 유지보수성, 재사용성이 크게 향상될 것입니다.
