# Vercel 배포 가이드

Vercel 프로젝트 2개를 같은 GitHub 레포에서 생성합니다.

---

## 1단계 — 백엔드 배포 (Flask API)

### Vercel 프로젝트 생성
- Import: GitHub 레포 선택
- Root Directory: **`/`** (기본값)
- Framework Preset: **Other**

### 환경변수 설정 (Vercel → Settings → Environment Variables)
| 키 | 값 |
|---|---|
| `DATABASE_URL` | Supabase → Settings → Database → Connection pooler (Transaction mode) URI |
| `SLACK_WEBHOOK_URL` | Slack App Webhook URL |
| `RESEND_API_KEY` | Resend API 키 |
| `RESEND_FROM_EMAIL` | 발신 이메일 주소 |
| `GOOGLE_CREDS_JSON` | `credentials.json` 파일 내용 전체를 한 줄로 붙여넣기 |
| `GOOGLE_SHEET_NAME` | Google Sheets 스프레드시트 이름 |
| `GOOGLE_CALENDAR_ID` | Google Calendar ID (보통 `primary`) |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API 키 |

### 배포 후 URL 확인
배포 완료 후 URL 기록: `https://[프로젝트명].vercel.app`

---

## 2단계 — 프론트엔드 배포 (Next.js)

### Vercel 프로젝트 생성
- Import: 같은 GitHub 레포 선택
- **Root Directory: `frontend`** ← 반드시 변경
- Framework Preset: **Next.js** (자동 감지)

### 환경변수 설정
| 키 | 값 |
|---|---|
| `FLASK_API_URL` | 1단계에서 배포된 백엔드 URL (예: `https://dbdbdib-api.vercel.app`) |

### 동작 방식
브라우저 → Next.js (`/api-flask/*`) → (rewrite) → Flask API

CORS 문제 없이 작동합니다.

---

## 로컬 개발

```bash
# 터미널 1 — Flask API
cd dbdbdib
pip install -r requirements.txt
python app.py
# → http://localhost:5000

# 터미널 2 — Next.js
cd dbdbdib/frontend
npm install
npm run dev
# → http://localhost:3000
```

`frontend/.env.local`의 `FLASK_API_URL`이 `http://localhost:5000`으로 설정되어 있어 자동 연결됩니다.

---

## GOOGLE_CREDS_JSON 설정 방법

```bash
# credentials.json 내용을 한 줄로 출력
cat credentials.json | tr -d '\n'
```

출력된 값을 Vercel 환경변수 `GOOGLE_CREDS_JSON`에 붙여넣기
