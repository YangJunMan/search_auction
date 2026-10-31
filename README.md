# 내 집 찾기 (Search Auction)

부동산 경매 정보를 한눈에 편하게 살펴볼 수 있도록 만든 프로젝트입니다.

🌐 [내 집 찾기 웹사이트 바로가기](https://yangjunman-auction.vercel.app/)

---

## 🌟 주요 기능

1. **간편한 경매 매물 조회 (웹 서비스)**
   - 마이옥션 계정 연동 및 저장된 조건 기반 자동 검색
   - 지도를 통한 매물 위치 확인 (Leaflet + OpenStreetMap)
   - 카카오 로컬 API를 통한 지하철역 최근접 거리(m) 및 역세권(400m 이내) 추천
   - 엑셀/CSV 내보내기 지원

2. **오프라인 대량 수집 및 추천 크롤러 (Python CLI)**
   - Selenium 기반 안정적인 다중 페이지 경매 정보 수집
   - 역세권 반경 필터링 및 카드형 반응형 갤러리 HTML 생성

---

## 🔒 보안 및 개인정보 보호

- **자격 증명 미보관**: 사용자의 아이디 및 비밀번호는 서버에 일절 저장되지 않으며, 검색 세션 유지 시 upstream 세션 쿠키만 AES-256-GCM으로 암호화되어 브라우저 쿠키(HttpOnly, Secure, SameSite)로 안전하게 관리됩니다.
- **민감 파일 보호**: 개인 설정(`config.json`) 및 환경변수(`.env`)는 `.gitignore`를 통해 Git 추적에서 제외됩니다.
- **인젝션 방지**: 엑셀/CSV 내보내기 시 수식 인젝션 방지 필터링 및 HTML 갤러리 생성 시 XSS 방지 이스케이프 처리가 적용되어 있습니다.

---

## 🚀 실행 및 테스트

### 1. 웹 서비스 (Web)

```bash
cd web

# 의존성 설치
npm install

# 단위 테스트 실행 (17개 테스트)
npm test
```

#### Vercel 배포 설정
- **Root Directory**: `web`
- **Environment Variables**:
  - `KAKAO_REST_API_KEY`: 카카오 로컬 REST API 키 (지오코딩 및 지하철역 탐색용)
  - `SESSION_SECRET`: 세션 암호화 키 (선택사항, 미지정 시 API 키 기반 안전 파생)

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

## 📁 프로젝트 구조

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
