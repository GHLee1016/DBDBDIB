# =========================
# db.py
# DB 연결 및 공통 검증 함수
# =========================
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import jsonify
from config import DB_URL


def get_conn():
    """데이터베이스 연결 객체를 반환합니다."""
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


def validate_choice(value, allowed_values, field_name):
    """허용된 값 목록에 속하는지 검증합니다. 실패 시 Flask 응답 튜플 반환."""
    if value not in allowed_values:
        return jsonify({
            "error": f"Invalid {field_name}",
            "allowed_values": sorted(allowed_values),
        }), 400
    return None
