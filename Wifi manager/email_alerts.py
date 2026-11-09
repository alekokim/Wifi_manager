import os
import requests

from dotenv import load_dotenv


load_dotenv()


def send_email_alert(subject, message):

    script_url = os.getenv(
        "GOOGLE_SCRIPT_URL"
    )

    receiver_email = os.getenv(
        "ALERT_EMAIL_TO"
    )

    if not script_url:

        print(
            "ERROR: GOOGLE_SCRIPT_URL is missing."
        )

        return False

    if not receiver_email:

        print(
            "ERROR: ALERT_EMAIL_TO is missing."
        )

        return False

    data = {
        "email": receiver_email,
        "subject": subject,
        "message": message
    }

    try:

        response = requests.post(
            script_url,
            json=data,
            timeout=30
        )

        print(
            "Google response:",
            response.text
        )

        return response.ok

    except Exception as error:

        print(
            f"Unable to send email: {error}"
        )

        return False