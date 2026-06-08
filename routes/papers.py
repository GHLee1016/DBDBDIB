# =========================
# routes/papers.py
# 논문 일괄 배정 / 배정 조회  (12기 주제: 데이터베이스)
# =========================
import logging
from flask import Blueprint, jsonify
from db import get_conn
from config import MAJOR_TO_CATEGORY
from external.slack import notify_slack
from external.sendgrid import send_result_email
from external.sheets import sync_to_google_sheets

logger = logging.getLogger(__name__)
bp = Blueprint("papers", __name__)


@bp.route("/admin/recruiting/season/<int:season_id>/assign-papers", methods=["POST"])
def assign_papers(season_id):
    """
    해당 시즌 합격자 전원에게 전공 기반으로 논문을 일괄 배정합니다.

    동작 방식:
      1. 미배정 합격자 조회
      2. 전공 → MAJOR_TO_CATEGORY로 카테고리 결정
      3. 해당 카테고리의 미배정 논문 1편 선택
         (카테고리 소진 시 다른 카테고리에서 fallback)
      4. paper_assignments INSERT

    트랜잭션:
      전체 성공 or 전체 rollback (부분 배정 상태 방지)

    외부 API (트랜잭션 밖):
      - Slack   : 배정 완료 요약
      - SendGrid: 합격자 개인별 논문 배정 안내 이메일
      - Google Sheets: 배정 결과 시트 갱신
    """
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT season_name FROM recruitment_seasons WHERE season_id = %s", (season_id,)
            )
            season = cur.fetchone()
            if not season:
                return jsonify({"error": "Season not found"}), 404

            # 미배정 합격자 조회
            cur.execute(
                """
                SELECT a.applicant_id, a.name, a.major, a.email
                FROM applicants a
                LEFT JOIN paper_assignments pa ON a.applicant_id = pa.applicant_id
                WHERE a.season_id = %s
                  AND a.final_status = '합격'
                  AND a.deleted_at IS NULL
                  AND pa.assignment_id IS NULL
                """,
                (season_id,),
            )
            applicants = cur.fetchall()

            if not applicants:
                return jsonify({
                    "message": "No eligible applicants to assign (already assigned or none passed)"
                }), 200

            assignments = []
            skipped     = []

            for applicant in applicants:
                applicant_id = applicant["applicant_id"]
                major        = applicant["major"]
                name         = applicant["name"]
                email        = applicant.get("email")
                category     = MAJOR_TO_CATEGORY.get(major, MAJOR_TO_CATEGORY["default"])

                # 전공 카테고리 논문 선택
                cur.execute(
                    """
                    SELECT p.paper_id, p.title, p.authors, p.difficulty
                    FROM papers p
                    LEFT JOIN paper_assignments pa ON p.paper_id = pa.paper_id
                    WHERE p.season_id = %s AND pa.paper_id IS NULL AND p.category = %s
                    LIMIT 1
                    """,
                    (season_id, category),
                )
                paper = cur.fetchone()

                # fallback: 카테고리 소진 시 전체에서 미배정 논문 선택
                if not paper:
                    cur.execute(
                        """
                        SELECT p.paper_id, p.title, p.authors, p.difficulty
                        FROM papers p
                        LEFT JOIN paper_assignments pa ON p.paper_id = pa.paper_id
                        WHERE p.season_id = %s AND pa.paper_id IS NULL
                        LIMIT 1
                        """,
                        (season_id,),
                    )
                    paper = cur.fetchone()

                if not paper:
                    skipped.append({
                        "applicant_id": applicant_id,
                        "name":         name,
                        "reason":       "No available papers",
                    })
                    continue

                cur.execute(
                    "INSERT INTO paper_assignments (paper_id, applicant_id) VALUES (%s, %s)",
                    (paper["paper_id"], applicant_id),
                )
                assignments.append({
                    "applicant_id":     applicant_id,
                    "name":             name,
                    "major":            major,
                    "email":            email,
                    "matched_category": category,
                    "paper_title":      paper["title"],
                    "paper_authors":    paper["authors"],
                    "difficulty":       paper["difficulty"],
                })

            conn.commit()  # 전체 성공 시에만 반영

        # ── 외부 API ────────────────────────────────────────────────────
        notify_slack(
            f"📚 논문 배정 완료 | {season['season_name']}\n"
            f"   배정 완료: {len(assignments)}명 | 미배정(논문 부족): {len(skipped)}명\n"
            + "\n".join([
                f"   • {a['name']} ({a['major']}) → {a['paper_title']}"
                for a in assignments
            ])
        )

        for a in assignments:
            if a.get("email"):
                send_result_email(
                    to_email=a["email"],
                    name=a["name"],
                    status="합격",
                    paper_title=a["paper_title"],
                )

        sync_to_google_sheets(season_id, assignments)

        return jsonify({
            "message":        f"Paper assignment complete for season {season_id} ({season['season_name']})",
            "assigned_count": len(assignments),
            "skipped_count":  len(skipped),
            "assignments":    assignments,
            "skipped":        skipped,
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error assigning papers for season {season_id}: {e}")
        return jsonify({"error": "Paper assignment failed", "details": str(e)}), 500
    finally:
        if conn:
            conn.close()


@bp.route("/admin/recruiting/season/<int:season_id>/paper-assignments", methods=["GET"])
def get_paper_assignments(season_id):
    """해당 시즌 합격자별 배정 논문 목록을 반환합니다."""
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.applicant_id, a.name, a.major,
                    p.title   AS paper_title,
                    p.authors AS paper_authors,
                    p.category, p.difficulty,
                    pa.assigned_at
                FROM paper_assignments pa
                JOIN applicants a ON pa.applicant_id = a.applicant_id
                JOIN papers p     ON pa.paper_id = p.paper_id
                WHERE a.season_id = %s
                ORDER BY a.applicant_id
                """,
                (season_id,),
            )
            rows = cur.fetchall()
            if not rows:
                return jsonify([]), 200
            return jsonify(rows), 200
    except Exception as e:
        logger.error(f"Error fetching paper assignments for season {season_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()
