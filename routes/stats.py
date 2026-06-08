# =========================
# routes/stats.py
# 집계/통계 GET 엔드포인트
# =========================
import logging
import time
import requests
from datetime import datetime
from flask import Blueprint, jsonify
from db import get_conn
from external.sheets import read_sheet_rows

logger = logging.getLogger(__name__)
bp = Blueprint("stats", __name__)


from config import SEMANTIC_SCHOLAR_API_KEY

def _fetch_citation_count_semantic(title: str) -> int | None:
    """1순위: Semantic Scholar API (API Key 사용)"""
    for attempt in range(3):
        try:
            resp = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": title, "fields": "title,citationCount", "limit": 1},
                headers={"x-api-key": SEMANTIC_SCHOLAR_API_KEY},
                timeout=8,
            )
            if resp.status_code == 429:
                wait = 5 * (attempt + 1)
                logger.warning(f"[Semantic Scholar] Rate limited. Waiting {wait}s ({attempt+1}/3)")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            if data.get("data"):
                return data["data"][0].get("citationCount")
            return None
        except Exception as e:
            logger.error(f"[Semantic Scholar] Failed for '{title}': {e}")
            return None
    return None


def _fetch_citation_count_openalex(title: str) -> int | None:
    """2순위: OpenAlex API (인증 불필요)"""
    try:
        resp = requests.get(
            "https://api.openalex.org/works",
            params={"search": title, "per_page": 1, "select": "title,cited_by_count"},
            headers={"User-Agent": "mailto:geonhee8604@gmail.com"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            return results[0].get("cited_by_count")
        return None
    except Exception as e:
        logger.error(f"[OpenAlex] Failed for '{title}': {e}")
        return None


def _fetch_citation_count(title: str) -> int | None:
    """
    인용수 조회 Fallback 체인:
      1순위: Semantic Scholar (API Key)
      2순위: OpenAlex (인증 불필요)
      3순위: None (DB 저장값 사용)
    """
    # 1순위: Semantic Scholar
    if SEMANTIC_SCHOLAR_API_KEY:
        result = _fetch_citation_count_semantic(title)
        if result is not None:
            logger.info(f"[Semantic Scholar] '{title[:30]}...' → {result}")
            return result
        logger.warning(f"[Semantic Scholar] Failed. Falling back to OpenAlex.")

    # 2순위: OpenAlex
    result = _fetch_citation_count_openalex(title)
    if result is not None:
        logger.info(f"[OpenAlex] '{title[:30]}...' → {result}")
        return result
    logger.warning(f"[OpenAlex] Failed. Falling back to DB value.")

    # 3순위: None → DB 저장값 사용
    return None


def _citation_to_difficulty(citation_count: int | None, original: str) -> str:
    """
    인용수 기반 난이도 보정.
      >= 5000 → hard / >= 1000 → medium / < 1000 → easy / None → 원래 값 유지
    """
    if citation_count is None:
        return original
    if citation_count >= 5000:
        return "hard"
    if citation_count >= 1000:
        return "medium"
    return "easy"


# [10] 기수별 합격률 랭킹 (Google Sheets 기반)
@bp.route("/admin/stats/season-pass-rate", methods=["GET"])
def stats_season_pass_rate():
    """
    Google Sheets의 'Season {id}' 시트에서 기수별 데이터를 읽어
    합격률·전공별 분포·평균점수를 집계하고 합격률 기준 랭킹을 반환합니다.
    시트 데이터가 없는 기수는 DB에서 fallback 집계합니다.
    """
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT season_id, season_name FROM recruitment_seasons ORDER BY season_id"
            )
            seasons = cur.fetchall()

        if not seasons:
            return jsonify({"message": "No seasons found"}), 200

        season_stats = []

        for season in seasons:
            season_id   = season["season_id"]
            season_name = season["season_name"]

            rows = read_sheet_rows(f"Season {season_id}")

            # ── Sheets 데이터 없으면 DB fallback ──────────────────────
            if not rows:
                conn2 = get_conn()
                with conn2.cursor() as cur2:
                    cur2.execute(
                        """
                        SELECT final_status, COUNT(*) AS cnt
                        FROM applicants
                        WHERE season_id = %s AND deleted_at IS NULL
                        GROUP BY final_status
                        """,
                        (season_id,),
                    )
                    db_rows = cur2.fetchall()
                conn2.close()

                status_counts = {r["final_status"]: r["cnt"] for r in db_rows}
                total   = sum(status_counts.values())
                passed  = status_counts.get("합격", 0)
                failed  = status_counts.get("불합격", 0)
                pending = status_counts.get("진행중", 0) + status_counts.get("대기", 0)

                season_stats.append({
                    "season_id":          season_id,
                    "season_name":        season_name,
                    "total":              total,
                    "passed":             passed,
                    "failed":             failed,
                    "pending":            pending,
                    "pass_rate":          round(passed / total * 100, 2) if total else 0,
                    "avg_score":          None,
                    "major_distribution": {},
                    "source":             "database_fallback",
                })
                continue

            # ── Sheets 데이터 집계 ────────────────────────────────────
            total   = len(rows)
            passed  = sum(1 for r in rows if r.get("상태") == "합격")
            failed  = sum(1 for r in rows if r.get("상태") == "불합격")
            pending = sum(1 for r in rows if r.get("상태") in {"진행중", "대기"})

            major_distribution: dict[str, int] = {}
            for r in rows:
                if r.get("상태") == "합격":
                    major = r.get("전공", "미상")
                    major_distribution[major] = major_distribution.get(major, 0) + 1

            scores = []
            for r in rows:
                try:
                    s = r.get("평균점수", "")
                    if s not in ("", None):
                        scores.append(float(s))
                except (ValueError, TypeError):
                    pass
            avg_score = round(sum(scores) / len(scores), 2) if scores else None

            season_stats.append({
                "season_id":          season_id,
                "season_name":        season_name,
                "total":              total,
                "passed":             passed,
                "failed":             failed,
                "pending":            pending,
                "pass_rate":          round(passed / total * 100, 2) if total else 0,
                "avg_score":          avg_score,
                "major_distribution": major_distribution,
                "source":             "google_sheets",
            })

        # 합격률 기준 내림차순 랭킹 정렬
        season_stats.sort(key=lambda x: x["pass_rate"], reverse=True)
        for i, s in enumerate(season_stats, start=1):
            s["rank"] = i

        return jsonify({
            "generated_at":   datetime.now().isoformat(timespec="seconds"),
            "total_seasons":  len(season_stats),
            "season_ranking": season_stats,
        }), 200

    except Exception as e:
        logger.error(f"Error in stats_season_pass_rate: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()


# [11] 논문 인용수 기반 난이도 보정 랭킹 (Semantic Scholar → OpenAlex → DB 순 Fallback)
@bp.route("/admin/stats/papers/<int:season_id>", methods=["GET"])
def stats_papers_with_citations(season_id):
    """
    DB 논문 목록을 기반으로 인용수를 조회해 난이도를 보정하고 랭킹을 반환합니다.

    인용수 조회 Fallback 체인:
      1순위: Semantic Scholar API (API Key 사용, 정확도 높음)
      2순위: OpenAlex API (인증 불필요, fallback)
      3순위: DB 저장값 사용 (API 전체 실패 시)
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

            cur.execute(
                """
                SELECT
                    p.paper_id, p.title, p.authors, p.category,
                    p.difficulty        AS original_difficulty,
                    p.citation_count,
                    a.name              AS assigned_to
                FROM papers p
                LEFT JOIN paper_assignments pa ON p.paper_id = pa.paper_id
                LEFT JOIN applicants a         ON pa.applicant_id = a.applicant_id
                WHERE p.season_id = %s
                ORDER BY p.paper_id
                """,
                (season_id,),
            )
            papers = cur.fetchall()

        if not papers:
            return jsonify({"message": "No papers found for this season"}), 200

        paper_stats = []
        for paper in papers:
            citation_count      = _fetch_citation_count(paper["title"])
            adjusted_difficulty = _citation_to_difficulty(citation_count, paper["original_difficulty"])
            time.sleep(1) # Semantic Scholar 1 req/sec Rate Limit 준수
            
            paper_stats.append({
                "paper_id":            paper["paper_id"],
                "title":               paper["title"],
                "authors":             paper["authors"],
                "category":            paper["category"],
                "original_difficulty": paper["original_difficulty"],
                "citation_count":      citation_count,
                "adjusted_difficulty": adjusted_difficulty,
                "difficulty_changed":  adjusted_difficulty != paper["original_difficulty"],
                "assigned_to":         paper["assigned_to"],
            })

        # 인용수 기준 내림차순 랭킹 (None은 맨 뒤)
        paper_stats.sort(
            key=lambda x: x["citation_count"] if x["citation_count"] is not None else -1,
            reverse=True,
        )
        for i, p in enumerate(paper_stats, start=1):
            p["rank"] = i

        changed_count = sum(1 for p in paper_stats if p["difficulty_changed"])

        return jsonify({
            "season_id":           season_id,
            "season_name":         season["season_name"],
            "generated_at":        datetime.now().isoformat(timespec="seconds"),
            "total_papers":        len(paper_stats),
            "difficulty_adjusted": changed_count,
            "paper_ranking":       paper_stats,
        }), 200

    except Exception as e:
        logger.error(f"Error in stats_papers_with_citations (season={season_id}): {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()
