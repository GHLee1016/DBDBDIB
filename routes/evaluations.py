# =========================
# routes/evaluations.py
# 평가 점수 입력
# =========================
import logging
from flask import Blueprint, jsonify, request
from db import get_conn, validate_choice
from config import ALLOWED_EVAL_TYPES, SCORE_THRESHOLD
from external.slack import notify_slack
from external.calendar import create_calendar_event

logger = logging.getLogger(__name__)
bp = Blueprint("evaluations", __name__)


@bp.route("/admin/evaluations", methods=["POST"])
def create_evaluation():
    """
    평가 점수를 입력합니다.

    트랜잭션:
      INSERT evaluations
        → AVG 계산
        → 평균 >= SCORE_THRESHOLD이면 UPDATE applicants '진행중' → '대기'

    외부 API (트랜잭션 밖):
      - Slack: 점수 입력 및 상태 변경 알림
      - Google Calendar: 1차면접/최종면접이고 interview_datetime 제공 시 이벤트 생성
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON required"}), 400

    score = data.get("score")
    if score is None or not (0 <= score <= 100):
        return jsonify({"error": "Score must be between 0 and 100"}), 400
    if not data.get("applicant_id") or not data.get("evaluator_id"):
        return jsonify({"error": "applicant_id and evaluator_id are required"}), 400

    eval_type = data.get("eval_type")
    if eval_type is not None:
        err = validate_choice(eval_type, ALLOWED_EVAL_TYPES, "eval_type")
        if err:
            return err

    applicant_id       = data.get("applicant_id")
    interview_datetime = data.get("interview_datetime")  # 'YYYY-MM-DDTHH:MM:SS', 선택

    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Slack/Calendar 메시지용 이름 조회
            cur.execute("SELECT name FROM applicants WHERE applicant_id = %s", (applicant_id,))
            row            = cur.fetchone()
            applicant_name = row["name"] if row else str(applicant_id)

            # 작업 1: 평가 점수 INSERT
            cur.execute(
                """
                INSERT INTO evaluations (applicant_id, evaluator_id, score, eval_type, comment)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (applicant_id, data.get("evaluator_id"), score, eval_type, data.get("comment")),
            )

            # 작업 2: 평균 점수 계산
            cur.execute(
                "SELECT ROUND(AVG(score), 2) AS avg_score FROM evaluations WHERE applicant_id = %s",
                (applicant_id,),
            )
            avg_row   = cur.fetchone()
            avg_score = float(avg_row["avg_score"]) if avg_row and avg_row["avg_score"] is not None else 0

            # 작업 3: 기준 이상이면 '진행중' → '대기' 자동 변경
            status_changed = False
            if avg_score >= SCORE_THRESHOLD:
                cur.execute(
                    """
                    UPDATE applicants SET final_status = '대기'
                    WHERE applicant_id = %s AND final_status = '진행중'
                    """,
                    (applicant_id,),
                )
                status_changed = cur.rowcount > 0

            conn.commit()

        # ── 외부 API ────────────────────────────────────────────────────
        slack_msg = (
            f"📝 평가 입력 | {applicant_name} | {eval_type} | "
            f"점수: {score}점 | 현재 평균: {avg_score}점"
        )
        if status_changed:
            slack_msg += f"\n🔄 상태 변경: 진행중 → 대기 (평균 {avg_score}점, 기준 {SCORE_THRESHOLD}점)"
        notify_slack(slack_msg)

        if eval_type in {"1차면접", "최종면접"} and interview_datetime:
            create_calendar_event(applicant_name, eval_type, interview_datetime)

        response = {"message": "Evaluation recorded successfully", "avg_score": avg_score}
        if status_changed:
            response["applicant_status"] = "changed to '대기' (avg score >= threshold)"
        return jsonify(response), 201

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error creating evaluation: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 400
    finally:
        if conn:
            conn.close()
