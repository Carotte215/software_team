"""办事申请表单敏感字段处理。"""

from app.models import Student
from app.services.crypto_fields import encrypt_text, mask_id_card


def sanitize_application_form(form: dict | None, student: Student | None = None) -> dict:
    payload = dict(form or {})
    id_card = str(payload.get("idCard", "")).strip()
    if id_card and not id_card.startswith("*"):
        payload["idCardEnc"] = encrypt_text(id_card)
        payload["idCard"] = mask_id_card(id_card)
        if student is not None and len(id_card) >= 15:
            student.id_card_encrypted = payload["idCardEnc"]
    return payload


def resolve_id_card(form: dict | None) -> str:
    payload = form or {}
    enc = str(payload.get("idCardEnc", "")).strip()
    if enc:
        from app.services.crypto_fields import decrypt_text

        return decrypt_text(enc)
    return str(payload.get("idCard", ""))
