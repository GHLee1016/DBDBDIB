# =========================
# routes/recruiting.py
# 결격자 조회 / 시즌 종료 / 데이터 파기 / 시연용 복원
# =========================
import logging
from enum import Enum
from flask import Blueprint, jsonify, request
from db import get_conn
from external.slack import notify_slack
from external.sendgrid import send_result_email
from external.sheets import sync_to_google_sheets

logger = logging.getLogger(__name__)
bp = Blueprint("recruiting", __name__)


class ApplicantStatus(Enum):
    PASSED = "합격"


# [1] 결격자 실시간 조회
@bp.route("/admin/recruiting/disqualified-list", methods=["GET"])
def get_disqualified_list():
    """결격 처리된 지원자 목록을 반환합니다. season_id 쿼리 파라미터로 필터링 가능."""
    season_id = request.args.get("season_id")
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            query  = """
                SELECT a.name, a.major, d.doc_type, d.issue_note AS reason
                FROM applicants a
                JOIN documents d ON a.applicant_id = d.applicant_id
                WHERE d.is_disqualified = TRUE
            """
            params = []
            if season_id:
                query += " AND a.season_id = %s"
                params.append(season_id)
            cur.execute(query, params)
            rows = cur.fetchall()
            if not rows:
                return jsonify({"message": "No disqualified applicants found"}), 200
            return jsonify(rows), 200
    except Exception as e:
        logger.error(f"Error fetching disqualified list: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()


# [2] 시즌 종료
@bp.route("/admin/recruiting/season/<int:season_id>/close", methods=["PATCH"])
def close_recruitment_season(season_id):
    """
    시즌을 종료합니다.

    트랜잭션:
      UPDATE recruitment_seasons → is_active = FALSE
        → UPDATE applicants: '진행중' → '대기' 일괄 변경

    외부 API (트랜잭션 밖):
      - Slack  : 시즌 종료 요약 (합격/불합격/대기 인원)
      - SendGrid: 합격·불합격자 전원 결과 이메일 발송
      - Google Sheets: 전체 지원자 현황 동기화
    """
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT season_name, is_active FROM recruitment_seasons WHERE season_id = %s",
                (season_id,),
            )
            result = cur.fetchone()
            if not result:
                return jsonify({"error": f"Season {season_id} not found."}), 404
            if not result["is_active"]:
                return jsonify({"message": "Season is already closed."}), 200

            season_name = result["season_name"]

            # 작업 1: 시즌 비활성화
            cur.execute(
                "UPDATE recruitment_seasons SET is_active = FALSE WHERE season_id = %s",
                (season_id,),
            )

            # 작업 2: '진행중' 지원자 → '대기' 일괄 변경
            cur.execute(
                """
                UPDATE applicants SET final_status = '대기'
                WHERE season_id = %s AND final_status = '진행중'
                """,
                (season_id,),
            )
            pending_count = cur.rowcount

            conn.commit()

            # 이메일·Sheets 동기화용 지원자 현황 조회
            cur.execute(
                """
                SELECT
                    a.applicant_id, a.name, a.major, a.email, a.final_status,
                    ROUND(AVG(e.score), 2)  AS avg_score,
                    COUNT(e.eval_id)        AS total_evals,
                    p.title                 AS paper_title,
                    p.category
                FROM applicants a
                LEFT JOIN evaluations e        ON a.applicant_id = e.applicant_id
                LEFT JOIN paper_assignments pa ON a.applicant_id = pa.applicant_id
                LEFT JOIN papers p             ON pa.paper_id = p.paper_id
                WHERE a.season_id = %s AND a.deleted_at IS NULL
                GROUP BY a.applicant_id, p.title, p.category
                ORDER BY a.applicant_id
                """,
                (season_id,),
            )
            all_applicants = cur.fetchall()

        # ── 외부 API ────────────────────────────────────────────────────
        passed_count = sum(1 for r in all_applicants if r["final_status"] == "합격")
        failed_count = sum(1 for r in all_applicants if r["final_status"] == "불합격")

        notify_slack(
            f"🏁 시즌 종료 | {season_name}\n"
            f"   합격: {passed_count}명 | 불합격: {failed_count}명 | 대기→재검토: {pending_count}명\n"
            f"   총 지원자: {len(all_applicants)}명"
        )

        for applicant in all_applicants:
            if applicant["final_status"] in {"합격", "불합격"}:
                send_result_email(
                    to_email=applicant.get("email"),
                    name=applicant["name"],
                    status=applicant["final_status"],
                    paper_title=applicant.get("paper_title"),
                )

        sync_to_google_sheets(season_id, all_applicants)

        return jsonify({
            "message":                    f"Season {season_id} has been closed successfully.",
            "status":                     "inactive",
            "pending_applicants_updated": pending_count,
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error closing season {season_id}: {e}")
        return jsonify({"error": "Failed to close season"}), 500
    finally:
        if conn:
            conn.close()


# [3] 불합격자 데이터 파기 (Soft Delete)
@bp.route("/admin/recruiting/season/<int:season_id>/cleanup", methods=["DELETE"])
def cleanup_unsuccessful_applicants(season_id):
    """
    종료된 시즌의 불합격자 데이터를 soft delete합니다.
    is_active=FALSE인 시즌만 가능합니다.

    외부 API (트랜잭션 밖):
      - Slack: 파기 건수 알림
    """
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT is_active FROM recruitment_seasons WHERE season_id = %s", (season_id,)
            )
            result = cur.fetchone()
            if not result:
                return jsonify({"error": "Season not found"}), 404
            if result["is_active"]:
                return jsonify({"error": "Cannot cleanup an active season"}), 400

            cur.execute(
                """
                UPDATE applicants SET deleted_at = CURRENT_TIMESTAMP
                WHERE season_id = %s
                  AND (final_status != %s OR final_status IS NULL)
                  AND deleted_at IS NULL
                """,
                (season_id, ApplicantStatus.PASSED.value),
            )
            deleted_count = cur.rowcount
            conn.commit()

        # ── 외부 API ────────────────────────────────────────────────────
        notify_slack(
            f"🗑️ 개인정보 파기 완료 | Season {season_id} | "
            f"삭제(soft delete): {deleted_count}명"
        )

        return jsonify({"message": "Cleanup successful", "deleted_count": deleted_count}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error cleaning up season {season_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()


# [4] 시연용 복원
@bp.route("/admin/recruiting/season/<int:season_id>/restore", methods=["PATCH"])
def restore_recruitment_season(season_id):
    """시연용: 종료된 시즌과 soft delete된 지원자 데이터를 복원합니다."""
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT is_active FROM recruitment_seasons WHERE season_id = %s", (season_id,)
            )
            result = cur.fetchone()
            if not result:
                return jsonify({"error": f"Season {season_id} not found."}), 404
            if result["is_active"]:
                return jsonify({"message": "Season is already active."}), 200

            cur.execute(
                "UPDATE recruitment_seasons SET is_active = TRUE WHERE season_id = %s", (season_id,)
            )
            cur.execute(
                "UPDATE applicants SET deleted_at = NULL WHERE season_id = %s AND deleted_at IS NOT NULL",
                (season_id,),
            )
            restored_count = cur.rowcount
            conn.commit()

            return jsonify({
                "message":             f"Season {season_id} and its data have been restored.",
                "restored_applicants": restored_count,
                "status":              "active",
            }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error restoring season {season_id}: {e}")
        return jsonify({"error": "Failed to restore season"}), 500
    finally:
        if conn:
            conn.close()
