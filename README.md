# 디비디비딥 12기 채용 관리 시스템

Flask REST API + Next.js 어드민 UI로 구성된 리크루팅 관리 시스템입니다.  
백엔드와 프론트엔드 모두 Vercel에 배포되며, DB는 Supabase PostgreSQL을 사용합니다.

## 기술 스택

- **백엔드**: Python / Flask, Supabase PostgreSQL (Connection Pooler)
- **프론트엔드**: Next.js 15 App Router, TypeScript, Tailwind CSS
- **배포**: Vercel (백엔드 + 프론트엔드 각각 별도 프로젝트)
- **외부 연동**: Slack, Resend (이메일), Google Calendar, Google Sheets, Semantic Scholar, OpenAlex

## 주요 기능

- 지원자 목록 조회 및 상태 관리 (합격 / 불합격 / 진행중 / 대기)
- 서류 상태 수정 및 결격 처리 / 해제
- 평가 등록 (서류 / 1차면접 / 최종면접)
- 합격자 논문 자동 배정 및 재배정 (전공 기반)
- 결격자 목록 조회
- 시즌 종료 / 데이터 파기(soft delete) / 복원
- 기수별 합격률 통계 (Google Sheets 연동)
- 논문 인용수 기반 난이도 자동 보정 (Semantic Scholar API)

## 프로젝트 구조

```
DBDBDIB/
├── api/
│   └── index.py          # Vercel Python 서버리스 진입점
├── routes/               # Flask Blueprint 라우트
│   ├── applicants.py     # 지원자 목록 / 통계
│   ├── documents.py      # 서류 목록 / 상태 수정
│   ├── evaluations.py    # 평가 등록
│   ├── papers.py         # 논문 배정
│   ├── recruiting.py     # 시즌 관리 / 결격자
│   ├── stats.py          # 통계
│   └── common.py         # DB 상태 확인
├── external/             # 외부 API 연동
│   ├── calendar.py       # Google Calendar
│   ├── sheets.py         # Google Sheets
│   ├── slack.py          # Slack Webhook
│   └── sendgrid.py       # Resend 이메일
├── frontend/             # Next.js 어드민 UI
│   ├── app/              # App Router 페이지
│   ├── components/       # 공통 컴포넌트
│   └── lib/api.ts        # API 클라이언트
├── app.py                # Flask 앱 + Blueprint 등록
├── config.py             # 환경변수 및 상수
├── db.py                 # DB 연결
├── requirements.txt      # Python 의존성
└── vercel.json           # 백엔드 Vercel 설정
```

## 로컬 개발

### 백엔드

```bash
pip install -r requirements.txt
# .env 파일에 환경변수 설정 (아래 참고)
python app.py
# → http://localhost:5000
```

### 프론트엔드

```bash
cd frontend
npm install
# frontend/.env.local에 FLASK_API_URL=http://localhost:5000 설정
npm run dev
# → http://localhost:3000
```

## 환경변수

### 백엔드 (`.env` 또는 Vercel Environment Variables)

| 키 | 설명 |
|---|---|
| `DATABASE_URL` | Supabase Connection Pooler (Transaction mode) URI |
| `SLACK_WEBHOOK_URL` | Slack App Webhook URL |
| `RESEND_API_KEY` | Resend API 키 |
| `RESEND_FROM_EMAIL` | 발신 이메일 주소 |
| `GOOGLE_CREDS_JSON` | `credentials.json` 내용 전체 (JSON 문자열) |
| `GOOGLE_SHEET_NAME` | Google Sheets 스프레드시트 이름 |
| `GOOGLE_CALENDAR_ID` | Google Calendar ID |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API 키 |

### 프론트엔드 (`frontend/.env.local` 또는 Vercel Environment Variables)

| 키 | 설명 |
|---|---|
| `FLASK_API_URL` | 배포된 백엔드 URL (예: `https://dbdbdib-api.vercel.app`) |

> **주의**: `credentials.json`과 `.env` 파일은 절대 git에 커밋하지 마세요.

## 배포

자세한 배포 절차는 [DEPLOY.md](./DEPLOY.md)를 참고하세요.

## 라이선스

MIT License — [LICENSE](./LICENSE) 참고
