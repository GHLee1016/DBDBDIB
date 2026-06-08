# =========================
# routes/documents.py
# 서류 상태 수정 + 지원자 상태 자동 변경
# =========================
import logging
from flask import Blueprint, jsonify, request
from db import get_conn, validate_choice
from config import ALLOWED_DOCUMENT_STATUSES
from external.slack import notify_slack

logger = logging.getLogger(__name__)
bp = Blueprint("documents", __name__)


@bp.route("/admin/documents", methods=["GET"])
def list_documents():
    """시즌별 전체 서류 목록을 반환합니다."""
    season_id = request.args.get("season_id", type=int)
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            query = """
                SELECT
                    d.doc_id,
                    d.doc_type,
                    d.status,
                    d.is_disqualified,
                    d.issue_note,
                    a.applicant_id,
                    a.name,
                    a.major,
                    a.final_status,
                    a.season_id
                FROM documents d
                JOIN applicants a ON d.applicant_id = a.applicant_id
                WHERE a.deleted_at IS NULL
            """
            params = []
            if season_id:
                query += " AND a.season_id = %s"
                params.append(season_id)
            query += " ORDER BY a.name, d.doc_type"
            cur.execute(query, params)
            rows = cur.fetchall()
            return jsonify(rows if rows else []), 200
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()


@bp.route("/admin/documents/<int:doc_id>", methods=["PATCH"])
def update_document_status(doc_id):
    """
    서류 상태를 수정하고 지원자 최종 상태를 자동으로 변경합니다.

    트랜잭션:
      UPDATE documents
        → 결격 등록(is_disqualified=True)  : UPDATE applicants → '불합격' (합격자 제외)
        → 결격 해제(is_disqualified=False) : UPDATE applicants → '진행중' (불합격자만)

    외부 API (트랜잭션 밖):
      - Slack: 결격 등록/해제 알림
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    if "status" not in data:
        return jsonify({"error": "status is required"}), 400
    if "is_disqualified" not in data:
        return jsonify({"error": "is_disqualified is required"}), 400

    err = validate_choice(data.get("status"), ALLOWED_DOCUMENT_STATUSES, "status")
    if err:
        return err
    if not isinstance(data.get("is_disqualified"), bool):
        return jsonify({"error": "is_disqualified must be a boolean"}), 400

    is_disqualified = data.get("is_disqualified")
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Slack 메시지용 이름 조회
            cur.execute(
                """
                SELECT a.name FROM applicants a
                JOIN documents d ON a.applicant_id = d.applicant_id
                WHERE d.doc_id = %s
                """,
                (doc_id,),
            )
            row            = cur.fetchone()
            applicant_name = row["name"] if row else f"doc#{doc_id}"

            # 작업 1: 서류 상태 업데이트
            cur.execute(
                """
                UPDATE documents SET status = %s, is_disqualified = %s, issue_note = %s
                WHERE doc_id = %s
                """,
                (data.get("status"), is_disqualified, data.get("issue_note"), doc_id),
            )
            if cur.rowcount == 0:
                conn.rollback()
                return jsonify({"error": "Document not found"}), 404

            # 작업 2-A: 결격 등록 → '불합격'
            if is_disqualified:
                cur.execute(
                    """
                    UPDATE applicants SET final_status = '불합격'
                    WHERE applicant_id = (SELECT applicant_id FROM documents WHERE doc_id = %s)
                      AND final_status != '합격'
                    """,
                    (doc_id,),
                )
                applicant_status_msg = "changed to '불합격' (disqualified)"

            # 작업 2-B: 결격 해제 → '진행중'
            else:
                cur.execute(
                    """
                    UPDATE applicants SET final_status = '진행중'
                    WHERE applicant_id = (SELECT applicant_id FROM documents WHERE doc_id = %s)
                      AND final_status = '불합격'
                    """,
                    (doc_id,),
                )
                applicant_status_msg = "changed to '진행중' (if it was '불합격')"

            conn.commit()

        # ── 외부 API ────────────────────────────────────────────────────
        if is_disqualified:
            notify_slack(
                f"🚫 결격 처리 | {applicant_name} | "
                f"사유: {data.get('issue_note', '-')} → 상태: 불합격"
            )
        else:
            notify_slack(
                f"✅ 결격 해제 | {applicant_name} | "
                f"비고: {data.get('issue_note', '-')} → 상태: 진행중"
            )

        return jsonify({
            "message":          "Document and applicant status updated",
            "applicant_status": applicant_status_msg,
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error updating document/applicant {doc_id}: {e}")
        return jsonify({"error": "Update failed", "details": str(e)}), 500
    finally:
        if conn:
            conn.close()
