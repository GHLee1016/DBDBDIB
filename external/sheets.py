# =========================
# external/sheets.py
# Google Sheets 읽기/쓰기 헬퍼
# =========================
import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_CREDS_FILE, GOOGLE_SHEET_NAME

logger = logging.getLogger(__name__)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def _get_credentials():
    """
    환경변수 GOOGLE_CREDS_JSON(JSON 문자열) 우선,
    없으면 GOOGLE_CREDS_FILE(파일 경로) 사용.
    로컬 개발은 파일, Vercel은 환경변수.
    """
    creds_json = os.environ.get("GOOGLE_CREDS_JSON")
    if creds_json:
        info = json.loads(creds_json)
        return ServiceAccountCredentials.from_json_keyfile_dict(info, SCOPE)
    if os.path.exists(GOOGLE_CREDS_FILE):
        return ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_FILE, SCOPE)
    return None


def _get_worksheet(sheet_title: str):
    """인증 후 워크시트 객체를 반환합니다. 없으면 새로 생성합니다."""
    creds = _get_credentials()
    if not creds:
        raise RuntimeError("Google credentials not available.")
    gc    = gspread.authorize(creds)
    sh    = gc.open(GOOGLE_SHEET_NAME)
    try:
        return sh.worksheet(sheet_title)
    except gspread.exceptions.WorksheetNotFound:
        return sh.add_worksheet(title=sheet_title, rows=200, cols=10)


def read_sheet_rows(sheet_title: str) -> list[dict]:
    """
    Google Sheets에서 특정 시트의 전체 행을 dict 리스트로 반환합니다.
    첫 번째 행을 헤더로 사용합니다. 실패 시 빈 리스트를 반환합니다.
    """
    try:
        ws = _get_worksheet(sheet_title)
        return ws.get_all_records()
    except Exception as e:
        logger.error(f"Sheets read failed (sheet='{sheet_title}'): {e}")
        return []


def sync_to_google_sheets(season_id: int, rows: list) -> None:
    """
    지원자/배정 현황을 Google Sheets에 동기화합니다.
    시트명: 'Season {season_id}'
    """
    try:
        ws = _get_worksheet(f"Season {season_id}")

        ws.clear()
        ws.append_row(["지원자ID", "이름", "전공", "상태", "평균점수", "평가횟수", "배정논문", "논문카테고리"])
        for r in rows:
            ws.append_row([
                r.get("applicant_id", ""),
                r.get("name", ""),
                r.get("major", ""),
                r.get("final_status", ""),
                str(r.get("avg_score", "")),
                r.get("total_evals", ""),
                r.get("paper_title", ""),
                r.get("category", ""),
            ])
        logger.info(f"Sheets synced: {len(rows)} rows → 'Season {season_id}'")
    except Exception as e:
        logger.error(f"Sheets sync failed (season={season_id}): {e}")
