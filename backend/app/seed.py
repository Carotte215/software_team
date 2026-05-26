from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.session import Base, SessionLocal, engine
from app.models import (
    AcademicPlan,
    AcademicProgress,
    Application,
    ApplicationTemplate,
    Honor,
    KnowledgeItem,
    Message,
    Notice,
    PartyProgress,
    PartyStage,
    PartyTimelineRule,
    Student,
    TemplateFile,
    TheoryQuestion,
)
from app.services.passwords import default_initial_password, hash_password
from app.services.seed_data import (
    APPLICATION_TEMPLATES,
    FLOW_STAGES,
    KNOWLEDGE,
    MODULES,
    NOTICES,
    STUDENTS,
    TEMPLATES,
    THEORY_QUESTIONS,
)


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalar(select(Student).limit(1)):
            print("Database already has data; skip seed.")
            return

        for item in FLOW_STAGES:
            db.merge(PartyStage(stage_key=item["key"], name=item["name"], desc=item["desc"], sort_order=item["order"]))

        plan_keys: set[str] = set()
        for sid, name, grade, major, class_name, nation, phone, political, tutor, hometown in STUDENTS:
            db.add(
                Student(
                    student_id=sid,
                    name=name,
                    grade=grade,
                    major=major,
                    class_name=class_name,
                    nation=nation,
                    phone=phone,
                    email=f"{sid}@student.local",
                    political_status=political,
                    tutor=tutor,
                    hometown=hometown,
                    password_hash=hash_password(default_initial_password(sid)),
                    extension={"volunteerHours": 24, "competitions": "程序设计竞赛"},
                ),
            )
            key = f"{grade}|{major}"
            if key not in plan_keys and not db.get(AcademicPlan, key):
                db.add(AcademicPlan(key=key, grade=grade, major=major, modules=MODULES))
                plan_keys.add(key)
            db.add(
                AcademicProgress(
                    student_id=sid,
                    modules=[{"key": m["key"], "earned": max(0, m["required"] - i % 4)} for i, m in enumerate(MODULES)],
                    uploads=[],
                    courses=[],
                ),
            )
            current = "activist" if "2024" in grade else "candidate"
            db.add(
                PartyProgress(
                    student_id=sid,
                    current_key=current,
                    history=[{"stageKey": "applicant", "at": int((datetime.now(timezone.utc) - timedelta(days=40)).timestamp() * 1000), "remark": "已递交申请书"}],
                    tasks=[{"id": f"task_{sid}_1", "title": "提交阶段材料", "body": "按当前阶段材料清单补齐材料。", "dueAt": int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp() * 1000), "done": False}],
                ),
            )

        for kid, title, category, tags, summary, sensitive in KNOWLEDGE:
            db.add(
                KnowledgeItem(
                    id=kid,
                    title=title,
                    category=category,
                    tags=tags,
                    summary=summary,
                    body=f"{summary}\n请以学院官网最新通知为准。",
                    sensitive_hint=sensitive,
                ),
            )

        for tid, name, scene, fmt in TEMPLATES:
            db.add(TemplateFile(id=tid, name=name, scene=scene, format=fmt))

        for nid, title, tags, summary, published_at in NOTICES:
            db.add(Notice(id=nid, title=title, tags=tags, summary=summary, content=f"{summary}\n\n请关注补充说明。", published_at=published_at))
            for sid, *_ in STUDENTS:
                db.add(
                    Message(
                        id=f"msg_{sid}_{nid}",
                        student_id=sid,
                        notice_id=nid,
                        title=title,
                        summary=summary,
                        batch_id="seed",
                        channels=[{"name": "站内", "state": "送达成功", "detail": "站内信已生成"}],
                    ),
                )

        for qid, stem, opts, ans, expl, cat in THEORY_QUESTIONS:
            db.add(
                TheoryQuestion(
                    id=qid,
                    stem=stem,
                    options=[o for o in opts.split(";") if o],
                    answer=ans,
                    explanation=expl,
                    category=cat,
                    online=True,
                ),
            )

        for tid, name, apply_type, subtype, body_html in APPLICATION_TEMPLATES:
            db.add(ApplicationTemplate(id=tid, name=name, apply_type=apply_type, subtype=subtype, body_html=body_html))

        for stage_key, duration, remind, material in [
            ("applicant", 30, 7, "入党申请书、谈话记录"),
            ("activist", 365, 30, "培养考察登记表、思想汇报"),
            ("candidate", 90, 14, "政审材料、公示记录、培训结业材料"),
            ("probationary", 365, 30, "预备党员考察表、转正申请"),
            ("member", 0, 0, "归档材料"),
        ]:
            db.merge(PartyTimelineRule(stage_key=stage_key, duration_days=duration, remind_before_days=remind, material=material))

        db.add(Application(id="app_pending", student_id="2024201581", type="证明申请", subtype="在读证明", status="审批中", form={"reason": "实习入职"}, attachments=[], audit_trail=[]))
        db.add(Application(id="app_reject", student_id="2024201581", type="盖章申请", subtype="行政用印", status="已驳回", form={"reason": "社团年审材料"}, attachments=[{"name": "年审材料.pdf"}], teacher_comment="缺少指导单位签字页。", decided_at=datetime.now(timezone.utc), audit_trail=[]))

        db.add(Honor(id="h1", title="国家奖学金", winner="李某", year=2025, major="计算机科学与技术", grade="2022级", category="国家级", intro="学年绩点与综合素质评价列前。", visibility="public", attachments=[]))
        db.add(Honor(id="h2", title="校级优秀共青团员", winner="王某", year=2024, major="软件工程", grade="2023级", category="校级", intro="志愿服务与团支部建设突出。", visibility="public", attachments=[]))

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
