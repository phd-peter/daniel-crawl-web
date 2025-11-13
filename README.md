# 다니엘기도회 뉴스 자동 수집 시스템

Christian Today 다니엘기도회 뉴스 자동 감지 및 저장 웹 애플리케이션

## 🏗️ 아키텍처

이 프로젝트는 **백엔드(Backend) + 프론트엔드(Frontend)** 분리 구조로 구성되어 있습니다:

- **Backend (Render)**: FastAPI 기반 REST API 서버
- **Frontend (Vercel)**: 정적 HTML/CSS/JS 클라이언트

## 🌟 기능

- **자동 뉴스 감지**: Christian Today 다니엘기도회 섹션에서 새로운 기사를 자동으로 감지
- **데이터베이스 저장**: SQLite를 사용하여 기사 URL과 제목을 저장
- **AI 요약 생성**: OpenAI GPT를 활용한 기사 요약, 키워드 추출, 성경 구절 추천
- **웹 인터페이스**: 깔끔하고 반응형 웹 UI로 저장된 기사 목록 표시
- **수동 확인**: 버튼 클릭으로 새로운 기사를 즉시 확인
- **REST API**: JSON API로 기사 데이터 접근 가능
- **분리 배포**: 백엔드와 프론트엔드를 독립적으로 배포 및 확장

## 📁 프로젝트 구조

```
daniel-crawl-web/
├── backend/              # Render 배포용 (API 서버)
│   ├── api/
│   │   └── index.py      # FastAPI API 서버
│   ├── db.py             # SQLite 데이터베이스
│   ├── scraper.py        # 웹 스크래핑 모듈
│   ├── requirements.txt  # Python 의존성
│   └── render.yaml       # Render 배포 설정
├── frontend/             # Vercel 배포용 (클라이언트)
│   ├── index.html        # 메인 페이지
│   ├── style.css         # 스타일시트
│   ├── script.js         # 클라이언트 로직
│   └── vercel.json       # Vercel 배포 설정
└── README.md             # 이 파일
```

## 🚀 배포 방법

### 1단계: 백엔드 배포 (Render)

1. **Render 계정 생성 및 로그인**
   - [render.com](https://render.com)에서 계정 생성

2. **GitHub 저장소 연결**
   - 이 프로젝트를 GitHub에 푸시

3. **Render에서 새 웹 서비스 생성**
   - **Service**: "Web Service"
   - **Repository**: 당신의 GitHub 저장소
   - **Branch**: `main` (또는 사용하는 브랜치)
   - **Root Directory**: `backend`

4. **설정 구성**
   ```yaml
   # render.yaml 내용
   services:
     - type: web
       name: daniel-prayer-api
       runtime: python3
       buildCommand: pip install -r requirements.txt
       startCommand: uvicorn api.index:app --host 0.0.0.0 --port $PORT
   ```

5. **환경 변수 설정** (선택사항)
   - `PYTHON_VERSION`: `3.9`

6. **배포 완료 대기**
   - Render에서 자동으로 빌드 및 배포
   - `https://your-service-name.onrender.com` 형식의 URL 제공

### 2단계: 프론트엔드 배포 (Vercel)

1. **Vercel CLI 설치**
   ```bash
   npm install -g vercel
   ```

2. **Vercel 로그인**
   ```bash
   vercel login
   ```

3. **프론트엔드 폴더에서 배포**
   ```bash
   cd frontend
   vercel --prod
   ```

4. **배포 설정**
   - **Project Name**: 원하는 프로젝트 이름 입력
   - **Directory**: `./` (현재 디렉토리)

5. **환경 변수 설정**
   - 배포 후 Vercel 대시보드에서 환경 변수 추가:
   - `API_BASE_URL`: `https://your-render-service.onrender.com`

### 3단계: 프론트엔드 API URL 업데이트

`frontend/script.js` 파일에서 API_BASE_URL을 실제 Render URL로 변경:

```javascript
// 변경 전
const API_BASE_URL = 'http://localhost:8000';

// 변경 후
const API_BASE_URL = 'https://your-service-name.onrender.com';
```

변경 후 다시 Vercel에 재배포:
```bash
cd frontend
vercel --prod
```

## 🔧 로컬 개발 환경

### 백엔드 로컬 실행

1. **의존성 설치**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **서버 실행**
   ```bash
   python -m uvicorn api.index:app --reload --host 0.0.0.0 --port 8000
   ```

### 프론트엔드 로컬 실행

1. **간단한 HTTP 서버 실행**
   ```bash
   cd frontend
   # Python이 설치된 경우
   python -m http.server 3000

   # 또는 Node.js가 설치된 경우
   npx serve .
   ```

2. **브라우저에서 접속**
   ```
   http://localhost:3000
   ```

**참고**: 로컬에서 테스트할 때는 `frontend/script.js`의 `API_BASE_URL`을 `http://localhost:8000`으로 유지하세요.

## 🔧 API 엔드포인트

### REST API (Backend)
- `GET /check` - 새로운 기사 확인 및 저장
- `GET /latest?limit=10` - 최근 기사 목록 (JSON)
- `GET /stats` - 저장된 기사 통계
- `GET /health` - 서버 상태 확인
- `GET /summaries` - 요약된 기사 목록
- `POST /summarize` - 상위 기사들 요약 생성
- `GET /summary/{article_url}` - 특정 기사 요약 조회

### 응답 예시

**GET /check**
```json
{
  "success": true,
  "message": "3개의 새로운 기사를 발견했습니다.",
  "new_articles": [
    {
      "url": "https://www.christiantoday.co.kr/news/123456",
      "title": "다니엘기도회 11일차 소식"
    }
  ],
  "total_found": 15,
  "checked_at": "2025-11-13 21:30:00"
}
```

**GET /stats**
```json
{
  "total_articles": 25,
  "last_updated": "2025-11-13T21:30:00.000000",
  "source_url": "https://www.christiantoday.co.kr/sections/pd_19"
}
```

## 🛠️ 기술 스택

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Web Scraping**: BeautifulSoup4 + Requests
- **Frontend**: HTML + CSS + JavaScript (Vanilla)
- **Backend Deployment**: Render
- **Frontend Deployment**: Vercel

## ⚙️ 설정 및 커스터마이징

### 스크래핑 설정

`backend/scraper.py`에서 다음 항목들을 수정할 수 있습니다:

```python
URL = "https://www.christiantoday.co.kr/sections/pd_19"  # 대상 URL
HEADERS = {
    'User-Agent': '...'  # User-Agent 헤더
}
```

### 데이터베이스 설정

`backend/db.py`에서 데이터베이스 경로 및 테이블 구조를 수정할 수 있습니다:

```python
DB_PATH = "articles.db"  # 데이터베이스 파일 경로
```

## 🔄 자동화 설정

### Render Cron Jobs (권장)

Render 대시보드에서 정기적인 기사 확인을 설정할 수 있습니다:

1. Render 프로젝트 대시보드 접속
2. "Settings" → "Cron Jobs"
3. 새 크론 잡 추가:
   - Command: `curl https://your-service-name.onrender.com/check`
   - Schedule: `0 */6 * * *` (6시간마다)

### 외부 모니터링 서비스

UptimeRobot, Cron-job.org 등의 서비스를 사용하여 정기적으로 `/check` 엔드포인트를 호출할 수 있습니다.

## 🐛 문제 해결

### 일반적인 문제

1. **스크래핑 실패**
   - 대상 웹사이트의 구조가 변경되었을 수 있음
   - `backend/scraper.py`의 선택자(selector)를 확인하고 업데이트

2. **CORS 오류**
   - 프론트엔드에서 API 호출이 실패하는 경우
   - `frontend/script.js`의 `API_BASE_URL`이 올바른지 확인

3. **배포 실패**
   - Render/Vercel 설정 파일 확인
   - Python 버전 및 의존성 확인

### 로그 확인

```bash
# 백엔드 로컬 로그
cd backend
python -m uvicorn api.index:app --reload --log-level info

# 프론트엔드 브라우저 콘솔에서 JavaScript 오류 확인
```

## 📊 모니터링

- **건강 상태**: `GET /health` 엔드포인트로 서버 상태 확인
- **통계 정보**: `GET /stats` 엔드포인트로 저장된 기사 수 확인
- **최근 기사**: `GET /latest` 엔드포인트로 최근 활동 확인

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 제공됩니다.

## 🙏 감사의 말

- Christian Today의 다니엘기도회 콘텐츠 제공
- FastAPI, BeautifulSoup4 등의 오픈소스 라이브러리 개발자들

---

**문의사항**: 이슈 트래커를 통해 버그 리포트 또는 기능 요청을 남겨주세요.
