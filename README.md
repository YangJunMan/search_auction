# 내 집 찾기 (Search Auction)

부동산 경매 정보를 한눈에 편하게 살펴볼 수 있도록 만든 프로젝트입니다.

[웹사이트 열기](https://yangjunman-auction.vercel.app/)

---

## 주요 기능

1. **경매 매물 조회 (웹 서비스)**
   - 마이옥션 계정 연동 및 저장된 조건 기반 자동 검색
   - 지도를 통한 매물 위치 확인 (Leaflet + OpenStreetMap)
   - 카카오 로컬 API를 통한 지하철역 최근접 거리(m) 및 역세권(400m 이내) 추천
   - 엑셀/CSV 내보내기 지원

2. **오프라인 대량 수집 및 추천 크롤러 (Python CLI)**
   - Selenium으로 여러 페이지의 경매 정보 수집
   - 역세권 반경 필터링 및 카드형 반응형 갤러리 HTML 생성

---

## 계정 정보와 입력 처리

- **계정 정보**: 아이디와 비밀번호를 별도로 저장하지 않고, 검색 세션 쿠키를 AES-256-GCM으로 암호화해 브라우저 쿠키(HttpOnly, Secure, SameSite)에 보관합니다.
- **설정 파일 관리**: 개인 설정(`config.json`) 및 환경변수(`.env`)는 `.gitignore`를 통해 Git 추적에서 제외됩니다.
- **입력 처리**: 엑셀/CSV 내보내기에 수식 실행을 막는 필터를 적용하고, HTML 갤러리를 만들 때 특수문자를 이스케이프합니다.

---

## 실행 및 테스트

### 1. 웹 서비스 (Web)

```bash
cd web

# 의존성 설치
npm install

# 단위 테스트 실행
npm test
```

#### Vercel 배포 설정
- **Root Directory**: `web`
- **Environment Variables**:
  - `KAKAO_REST_API_KEY`: 카카오 로컬 REST API 키 (지오코딩 및 지하철역 탐색용)
  - `SESSION_SECRET`: 세션 암호화 키 (선택사항, 미지정 시 API 키에서 파생)

### 2. Python 크롤러 (Crawler)

```bash
# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 설정 파일 생성
cp config.example.json config.json
# config.json 에 계정 및 설정값 입력

# 단위 테스트 실행
python3 -m unittest discover tests

# 크롤러 실행
python crawler.py
```

---

## 프로젝트 구조

```
├── web/                     # Vercel Serverless 웹 애플리케이션
│   ├── api/search.js        # Puppeteer 브라우저 기반 검색 및 세션 핸들러
│   ├── lib/                 # 지오코딩, 세션 암호화, 페이지네이션 유틸리티
│   ├── index.html           # 반응형 사용자 UI
│   ├── script.js            # 프론트엔드 인터랙션 로직
│   └── tests/               # 웹 단위 테스트
├── src/                     # Python 크롤러 & 유틸리티 모듈
│   ├── automation/          # Selenium 자동화 핸들러 (로그인, 검색, 내비게이션)
│   ├── core/                # 드라이버 관리 및 설정
│   ├── scraping/            # HTML 파서 및 페이지 수집기
│   └── utils/               # 지오코딩, 거리 계산, CSV/갤러리 리포트 생성
├── tests/                   # Python 단위 테스트
├── crawler.py               # Python 크롤러 진입점
└── config.example.json      # 크롤러 설정 예시 템플릿
```
