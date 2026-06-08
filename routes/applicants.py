# =========================
# routes/applicants.py
# 지원자 목록 조회 / 평균 점수 조회 / 논문 재배정
# =========================
import logging
from flask import Blueprint, jsonify, request
from db import get_conn

logger = logging.getLogger(__name__)
bp = Blueprint("applicants", __name__)


@bp.route("/admin/applicants", methods=["GET"])
def list_applicants():
    """시즌별 전체 지원자 목록을 반환합니다."""
    season_id = request.args.get("season_id", type=int)
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            query = """
                SELECT
                    a.applicant_id,
                    a.name,
                    a.major,
                    a.email,
                    a.final_status,
                    a.season_id,
                    ROUND(AVG(e.score), 2) AS avg_score,
                    COUNT(e.eval_id)       AS total_evals,
                    p.title                AS paper_title,
                    p.difficulty           AS paper_difficulty
                FROM applicants a
                LEFT JOIN evaluations e        ON a.applicant_id = e.applicant_id
                LEFT JOIN paper_assignments pa ON a.applicant_id = pa.applicant_id
                LEFT JOIN papers p             ON pa.paper_id = p.paper_id
                WHERE a.deleted_at IS NULL
            """
            params = []
            if season_id:
                query += " AND a.season_id = %s"
                params.append(season_id)
            query += " GROUP BY a.applicant_id, p.title, p.difficulty ORDER BY a.name"
            cur.execute(query, params)
            rows = cur.fetchall()
            return jsonify(rows if rows else []), 200
    except Exception as e:
        logger.error(f"Error listing applicants: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()


@bp.route("/admin/applicants/<int:app_id>/stats", methods=["GET"])
def get_applicant_stats(app_id):
    """지원자의 평균 점수와 평가 횟수를 반환합니다."""
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.name,
                       ROUND(AVG(e.score), 2) AS avg_score,
                       COUNT(e.eval_id)        AS total_evals
                FROM applicants a
                LEFT JOIN evaluations e ON a.applicant_id = e.applicant_id
                WHERE a.applicant_id = %s
                GROUP BY a.name
                """,
                (app_id,),
            )
            row = cur.fetchone()
            if not row or row["name"] is None:
                return jsonify({"error": "Applicant not found"}), 404
            return jsonify(row), 200
    except Exception as e:
        logger.error(f"Error fetching stats for applicant {app_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()


@bp.route("/admin/applicants/<int:app_id>/reassign-paper", methods=["PATCH"])
def reassign_paper(app_id):
    """
    특정 합격자의 논문을 재배정합니다.
    paper_id를 body에 전달하면 직접 지정, 없으면 전공 기반 자동 배정합니다.

    트랜잭션:
      DELETE 기존 배정 → INSERT 새 배정

    외부 API (트랜잭션 밖):
      - Slack: 재배정 내용 알림
    """
    # 순환 import 방지를 위해 함수 내부에서 import
    from flask import request
    from config import MAJOR_TO_CATEGORY
    from external.slack import notify_slack

    data     = request.get_json() or {}
    paper_id = data.get("paper_id")
    conn     = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, major, season_id, final_status FROM applicants WHERE applicant_id = %s",
                (app_id,),
            )
            applicant = cur.fetchone()
            if not applicant:
                return jsonify({"error": "Applicant not found"}), 404
            if applicant["final_status"] != "합격":
                return jsonify({"error": "Only passed applicants can be assigned papers"}), 400

            season_id = applicant["season_id"]
            major     = applicant["major"]

            # 작업 1: 기존 배정 삭제
            cur.execute("DELETE FROM paper_assignments WHERE applicant_id = %s", (app_id,))

            # 작업 2: 새 논문 선택
            if paper_id:
                cur.execute(
                    """
                    SELECT paper_id, title, authors, category, difficulty
                    FROM papers WHERE paper_id = %s AND season_id = %s
                    """,
                    (paper_id, season_id),
                )
                new_paper = cur.fetchone()
                if not new_paper:
                    conn.rollback()
                    return jsonify({"error": "Paper not found in this season"}), 404
            else:
                category = MAJOR_TO_CATEGORY.get(major, MAJOR_TO_CATEGORY["default"])
                cur.execute(
                    """
                    SELECT p.paper_id, p.title, p.authors, p.category, p.difficulty
                    FROM papers p
                    LEFT JOIN paper_assignments pa ON p.paper_id = pa.paper_id
                    WHERE p.season_id = %s AND pa.paper_id IS NULL AND p.category = %s
                    LIMIT 1
                    """,
                    (season_id, category),
                )
                new_paper = cur.fetchone()
                if not new_paper:
                    conn.rollback()
                    return jsonify({"error": "No available papers for this major's category"}), 404

            # 작업 3: 새 배정 INSERT
            cur.execute(
                "INSERT INTO paper_assignments (paper_id, applicant_id) VALUES (%s, %s)",
                (new_paper["paper_id"], app_id),
            )
            conn.commit()

        # ── 외부 API ────────────────────────────────────────────────────
        notify_slack(
            f"🔄 논문 재배정 | {applicant['name']} ({major})\n"
            f"   새 논문: {new_paper['title']} [{new_paper['difficulty']}]"
        )

        return jsonify({
            "message":    f"Paper reassigned successfully for applicant {app_id}",
            "applicant":  applicant["name"],
            "major":      major,
            "new_paper":  new_paper["title"],
            "authors":    new_paper["authors"],
            "category":   new_paper["category"],
            "difficulty": new_paper["difficulty"],
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error reassigning paper for applicant {app_id}: {e}")
        return jsonify({"error": "Reassignment failed", "details": str(e)}), 500
    finally:
        if conn:
            conn.close()
