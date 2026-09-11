import base64
import os
import httpx


def email_payload(recipient: str, pdf_bytes: bytes) -> dict:
    # Deliberately much smaller than the provider's total encoded-email limit.
    if len(pdf_bytes) > 8 * 1024 * 1024:
        raise ValueError("Report attachment too large")
    return {
        "from": os.environ["EMAIL_FROM"],
        "to": [recipient],
        "subject": "Your personalized practice package",
        "text": "Your reviewed practice package is attached. Contact your educator with any questions.",
        "attachments": [{"filename": "personalized-practice.pdf",
                         "content": base64.b64encode(pdf_bytes).decode("ascii")}],
    }


async def send_frozen_payload(payload: dict, idempotency_key: str) -> str:
    if not 1 <= len(idempotency_key) <= 256:
        raise ValueError("Invalid idempotency key length")
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        response = await client.post(
            os.environ["RESEND_API_BASE"] + "/emails",
            headers={"Authorization": "Bearer " + os.environ["RESEND_API_KEY"],
                     "Idempotency-Key": idempotency_key}, json=payload,
        )
        response.raise_for_status()
        return response.json()["id"]
