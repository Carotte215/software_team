"""通知多渠道分发：当前测试版本仅默认启用站内真实投递。"""

from __future__ import annotations

import re
import smtplib
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Message, Notice, SmsSimulation, Student
from app.services.common import uid


def mask_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) < 7:
        return phone or ""
    return f"{digits[:3]}****{digits[-4:]}"


def student_email(student: Student) -> str:
    if student.email and "@" in student.email:
        return student.email.strip()
    sid = student.student_id.strip()
    if sid:
        return f"{sid}@student.local"
    return ""


def smtp_enabled() -> bool:
    s = get_settings()
    return bool(s.smtp_host and s.smtp_from)


def send_email(to_addr: str, subject: str, body: str) -> tuple[bool, str]:
    if not to_addr:
        return False, "无邮箱地址"
    s = get_settings()
    if not smtp_enabled():
        return False, "SMTP 未配置"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = s.smtp_from
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=10) as server:
            if s.smtp_tls:
                server.starttls()
            if s.smtp_user:
                server.login(s.smtp_user, s.smtp_password)
            server.sendmail(s.smtp_from, [to_addr], msg.as_string())
        return True, "发送请求成功"
    except Exception as exc:
        return False, str(exc)


def dispatch_notice(
    db: Session,
    notice: Notice,
    batch_id: str,
    targets: list[Student],
    *,
    enable_email: bool = False,
    enable_sms_sim: bool = False,
) -> list[dict]:
    stats = {
        "站内": {"sendOk": 0, "sendFail": 0, "deliverOk": 0, "deliverFail": 0, "read": 0, "observability": "可读"},
    }
    if enable_email:
        stats["邮件"] = {"sendOk": 0, "sendFail": 0, "deliverOk": 0, "deliverFail": 0, "read": 0, "observability": "不可观测" if not smtp_enabled() else "可读"}
    if enable_sms_sim:
        stats["短信"] = {"sendOk": 0, "sendFail": 0, "deliverOk": 0, "deliverFail": 0, "read": 0, "observability": "发送记录"}

    for student in targets:
        channel_states: list[dict] = []

        # 站内信 — 真实投递
        db.add(
            Message(
                id=uid("msg"),
                student_id=student.student_id,
                notice_id=notice.id,
                title=notice.title,
                summary=notice.summary,
                batch_id=batch_id,
                channels=[{"name": "站内", "state": "送达成功", "detail": "站内信已生成"}],
            ),
        )
        stats["站内"]["sendOk"] += 1
        stats["站内"]["deliverOk"] += 1
        channel_states.append({"name": "站内", "state": "送达成功", "detail": "站内信已生成"})

        # 邮件 — 配置了 SMTP 则真实发送
        if enable_email:
            ok, detail = send_email(
                student_email(student),
                notice.title,
                f"{notice.summary}\n\n{notice.content}",
            )
            if ok:
                stats["邮件"]["sendOk"] += 1
                if smtp_enabled():
                    stats["邮件"]["deliverOk"] += 1
                channel_states.append({"name": "邮件", "state": "发送请求成功", "detail": detail})
            else:
                stats["邮件"]["sendFail"] += 1
                channel_states.append({"name": "邮件", "state": "发送失败", "detail": detail})

        # 短信 — 仅模拟记录（需求允许）
        if enable_sms_sim and student.phone:
            text = f"[学院通知]{notice.title}"
            db.add(
                SmsSimulation(
                    id=uid("sms"),
                    batch_id=batch_id,
                    student_id=student.student_id,
                    phone_masked=mask_phone(student.phone),
                    text=text,
                ),
            )
            stats["短信"]["sendOk"] += 1
            channel_states.append({"name": "短信", "state": "模拟记录", "detail": f"目标群 {mask_phone(student.phone)}"})

    return [{"name": name, **values} for name, values in stats.items()]


def empty_scheduled_channels(count: int) -> list[dict]:
    return [
        {"name": "站内", "sendOk": 0, "sendFail": 0, "deliverOk": 0, "deliverFail": 0, "read": 0, "target": count, "observability": "待发送"},
    ]
