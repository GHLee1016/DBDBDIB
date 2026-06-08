# =========================
# routes/common.py
# 공통 라우트: DB 연결 상태 확인
# =========================
import logging
from flask import Blueprint, jsonify
from db import get_conn

logger = logging.getLogger(__name__)
bp = Blueprint("common", __name__)


@bp.route("/common/db-check", methods=["GET"])
def db_check():
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
        return jsonify({"status": "healthy", "database": "connected", "result": result}), 200
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return jsonify({"status": "unhealthy", "message": "Database connection failed"}), 500
    finally:
        if conn:
            conn.close()
