import requests
import json
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

def send_email_notification(subject: str, html_content: str):
    try:
        data = {
            "sender": {
                "name": "Smart Assistant",
                "email": settings.EMAIL_USER or "no-reply@gmail.com"
            },
            "to": [{
                "name": "CEO",
                "email": settings.NOTIFY_EMAIL or settings.EMAIL_USER
            }],
            "subject": subject,
            "htmlContent": html_content
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "api-key": settings.BREVO_API_KEY
        }

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers=headers,
            data=json.dumps(data)
        )

        if response.status_code == 201:
            logger.info("Email notification sent.")
        else:
            logger.error(f"Email send failed: {response.status_code} - {response.text}")

    except Exception as e:
        logger.exception("Error while sending email.")
