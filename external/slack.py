# =========================
# external/slack.py
# Slack Webhook 알림 헬퍼
# =========================
import logging
import requests
from config import SLACK_WEBHOOK_URL

logger = logging.getLogger(__name__)


def notify_slack(message: str) -> None:
    """
    Slack Webhook으로 메시지를 전송합니다.
    실패해도 메인 로직에 영향을 주지 않습니다.
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set. Skipping Slack notification.")
        return
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=5)
        resp.raise_for_status()
        logger.info(f"Slack sent: {message[:60]}...")
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
