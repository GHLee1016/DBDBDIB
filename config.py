# =========================
# config.py
# 환경변수, 상수, 전공 매핑 정의
# =========================
import os
from dotenv import load_dotenv

load_dotenv()

# ── DB ───────────────────────────────────────────────────────────────────────
DB_URL = os.environ.get("DATABASE_URL")
SEMANTIC_SCHOLAR_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")

# ── Slack ────────────────────────────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# ── Resend (이메일) ───────────────────────────────────────────────────────────
# SendGrid에서 Resend로 전환
# 기존 SENDGRID_* 변수명은 external/sendgrid.py 내부에서 그대로 참조
SENDGRID_API_KEY    = os.environ.get("RESEND_API_KEY")      # .env에는 RESEND_API_KEY로 설정
SENDGRID_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "recruit@yourclub.com")

# ── Google 공통 ───────────────────────────────────────────────────────────────
GOOGLE_CREDS_FILE  = os.environ.get("GOOGLE_CREDS_FILE", "credentials.json")
GOOGLE_SHEET_NAME  = os.environ.get("GOOGLE_SHEET_NAME", "디비디비딥 리크루팅")
GOOGLE_CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")

# ── 비즈니스 상수 ──────────────────────────────────────────────────────────────
SCORE_THRESHOLD           = 80
ALLOWED_DOCUMENT_STATUSES = {"pending", "verified", "missing", "incomplete"}
ALLOWED_EVAL_TYPES        = {"서류", "1차면접", "최종면접"}

# ── 논문 배정용 전공 매핑 (12기 주제: 데이터베이스) ──────────────────────────────
MAJOR_TO_CATEGORY = {
    "컴퓨터공학":   "query_optimization",
    "소프트웨어학": "query_optimization",
    "전기전자공학": "distributed_systems",
    "산업공학":     "distributed_systems",
    "통계학과":     "data_mining",
    "수학과":       "data_mining",
    "응용수학":     "data_mining",
    "경영학과":     "transaction_concurrency",
    "경제학과":     "transaction_concurrency",
    "회계학과":     "transaction_concurrency",
    "default":      "database_survey",
}
