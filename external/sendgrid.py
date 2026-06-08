# =========================
# external/sendgrid.py  (Resend로 전환)
# 이메일 발송 헬퍼 - Resend API 사용
# pip install resend
# =========================
import logging
import resend
from config import SENDGRID_API_KEY, SENDGRID_FROM_EMAIL

# 환경변수명은 그대로 유지 (config.py 수정 최소화)
# SENDGRID_API_KEY → Resend API Key로 사용
# SENDGRID_FROM_EMAIL → 발신 이메일로 사용

logger = logging.getLogger(__name__)


def send_result_email(to_email: str, name: str, status: str, paper_title: str = None) -> None:
    """
    합격/불합격 결과 이메일을 발송합니다.
    합격자의 경우 배정된 논문 제목도 함께 안내합니다.
    """
    if not SENDGRID_API_KEY:
        logger.warning("RESEND_API_KEY not set. Skipping email.")
        return
    if not to_email:
        logger.warning(f"No email address for '{name}'. Skipping.")
        return
    try:
        resend.api_key = SENDGRID_API_KEY  # Resend는 api_key를 직접 설정

        if status == "합격":
            subject = "[디비디비딥] 🎉 12기 최종 합격을 축하드립니다!"
            html_content = f"""
            <h2>🎉 합격을 축하드립니다, {name}님!</h2>
            <p>디비디비딥 12기 데이터베이스 트랙에 최종 합격하셨습니다.</p>
            <br>
            <p>📄 <strong>배정 논문:</strong> {paper_title or '추후 안내 예정'}</p>
            <br>
            <p>오리엔테이션 일정은 별도로 안내드리겠습니다.</p>
            <br>
            <p>디비디비딥 운영진 드림</p>
            """
        else:
            subject = "[디비디비딥] 12기 지원 결과 안내"
            html_content = f"""
            <h2>안녕하세요, {name}님.</h2>
            <p>디비디비딥 12기에 지원해 주셔서 감사합니다.</p>
            <p>아쉽게도 이번에는 함께하지 못하게 되었습니다.</p>
            <br>
            <p>더 좋은 기회로 다시 만나길 바랍니다.</p>
            <br>
            <p>디비디비딥 운영진 드림</p>
            """

        resend.Emails.send({
            "from":    SENDGRID_FROM_EMAIL,
            "to":      [to_email],
            "subject": subject,
            "html":    html_content,
        })
        logger.info(f"Email sent via Resend → {to_email} ({name}, {status})")
    except Exception as e:
        logger.error(f"Resend email failed for '{name}': {e}")
