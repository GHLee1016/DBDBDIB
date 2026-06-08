# =========================
# external/calendar.py
# Google Calendar 이벤트 등록 헬퍼
# =========================
import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import GOOGLE_CREDS_FILE, GOOGLE_CALENDAR_ID

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_credentials():
    """
    환경변수 GOOGLE_CREDS_JSON(JSON 문자열) 우선,
    없으면 GOOGLE_CREDS_FILE(파일 경로) 사용.
    로컬 개발은 파일, Vercel은 환경변수.
    """
    creds_json = os.environ.get("GOOGLE_CREDS_JSON")
    if creds_json:
        info = json.loads(creds_json)
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    if os.path.exists(GOOGLE_CREDS_FILE):
        return service_account.Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=SCOPES)
    return None


def create_calendar_event(applicant_name: str, eval_type: str, interview_datetime: str) -> None:
    """
    면접 일정을 Google Calendar에 등록합니다.
    interview_datetime: 'YYYY-MM-DDTHH:MM:SS' 형식
    이벤트 길이는 1시간으로 고정합니다.
    """
    try:
        creds = _get_credentials()
        if not creds:
            logger.warning("Google credentials not found. Skipping Calendar.")
            return
        service = build("calendar", "v3", credentials=creds)
        start_dt = datetime.fromisoformat(interview_datetime)
        end_dt   = start_dt + timedelta(hours=1)

        event = {
            "summary":     f"[디비디비딥 12기] {eval_type} - {applicant_name}",
            "description": f"지원자: {applicant_name}\n전형: {eval_type}",
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Seoul"},
            "end":   {"dateTime": end_dt.isoformat(),   "timeZone": "Asia/Seoul"},
        }
        service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=event).execute()
        logger.info(f"Calendar event created: [{eval_type}] {applicant_name} @ {interview_datetime}")
    except Exception as e:
        logger.error(f"Calendar event creation failed: {e}")
