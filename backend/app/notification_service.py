import os
from twilio.rest import Client


def send_sms(phone_number: str, message: str) -> dict:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not account_sid or not auth_token or not from_number:
        raise ValueError("Twilio environment variables are not configured")

    client = Client(account_sid, auth_token)

    sms = client.messages.create(
        body=message,
        from_=from_number,
        to=phone_number,
    )

    return {
        "sid": sms.sid,
        "status": sms.status,
        "to": phone_number,
    }
