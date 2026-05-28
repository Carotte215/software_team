import csv
from io import StringIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import TheoryAttempt, TheoryQuestion
from app.services.common import audit, now_ms, uid

router = APIRouter(prefix="/theory", tags=["theory"])

DEFAULT_QUESTIONS = [
    {
        "id": "theory_q1",
        "stem": "入党申请人递交申请书后，通常应接受党组织的谈话和培养教育。",
        "options": ["正确", "错误"],
        "answer": "正确",
        "explanation": "入党申请提交后，党组织会安排谈话并开展培养教育。",
        "category": "入党流程",
        "online": True,
    },
    {
        "id": "theory_q2",
        "stem": "发展对象阶段通常需要完成政审、公示和集中培训等材料或环节。",
        "options": ["正确", "错误"],
        "answer": "正确",
        "explanation": "发展对象阶段需按组织要求完成相关审查和培训材料。",
        "category": "发展对象",
        "online": True,
    },
]


@router.get("/questions")
def student_questions(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    import random
    from datetime import datetime, timezone

    pool = [public_question(row) for row in load_questions(db) if row.get("online", True)]
    count = min(get_settings().theory_question_count, len(pool))
    rows = random.sample(pool, count) if count and count < len(pool) else pool
    latest = db.scalars(
        select(TheoryAttempt)
        .where(TheoryAttempt.student_id == session.student_id)
        .order_by(TheoryAttempt.created_at.desc()),
    ).first()
    limit = get_settings().theory_daily_attempt_limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_attempts = db.scalar(
        select(func.count())
        .select_from(TheoryAttempt)
        .where(TheoryAttempt.student_id == session.student_id, TheoryAttempt.created_at >= today_start),
    ) or 0
    return {
        "list": rows,
        "latestAttempt": attempt_payload(latest) if latest else None,
        "dailyLimit": limit,
        "todayAttempts": today_attempts,
    }


@router.post("/attempt")
def submit_attempt(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    from datetime import datetime, timezone

    limit = get_settings().theory_daily_attempt_limit
    if limit > 0:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = db.scalar(
            select(func.count())
            .select_from(TheoryAttempt)
            .where(TheoryAttempt.student_id == session.student_id, TheoryAttempt.created_at >= today_start),
        ) or 0
        if today_count >= limit:
            raise HTTPException(status_code=429, detail=f"今日答题次数已达上限（{limit} 次）")

    answers = payload.get("answers", {})
    question_ids = payload.get("questionIds") or list(answers.keys())
    all_questions = {row["id"]: row for row in load_questions(db) if row.get("online", True)}
    questions = [all_questions[qid] for qid in question_ids if qid in all_questions]
    details = []
    correct = 0
    for question in questions:
        answer = str(answers.get(question["id"], "")).strip()
        ok = answer == str(question.get("answer", "")).strip()
        correct += 1 if ok else 0
        details.append(
            {
                "id": question["id"],
                "stem": question["stem"],
                "answer": answer,
                "correctAnswer": question.get("answer", ""),
                "correct": ok,
                "explanation": question.get("explanation", ""),
            },
        )
    row = TheoryAttempt(
        id=uid("attempt"),
        student_id=session.student_id,
        score=int(round(correct * 100 / len(questions), 0)) if questions else 0,
        total=len(questions),
        detail=details,
    )
    db.add(row)
    audit(db, session, "theory_attempt", row.id, {"score": row.score})
    db.commit()
    return attempt_payload(row, correct=correct)


@router.get("/workbench/questions")
def admin_questions(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"list": load_questions(db)}


@router.put("/workbench/questions")
def save_questions(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    questions = [normalize_question(row) for row in payload.get("questions", [])]
    persist_questions(db, questions)
    audit(db, session, "theory_questions_save", "theory_questions", {"count": len(questions)})
    db.commit()
    return {"ok": True, "list": questions}


@router.post("/workbench/questions/import")
async def import_questions(
    file: UploadFile = File(...),
    dry_run: bool = Form(default=True, alias="dryRun"),
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    rows = parse_question_csv((await file.read()).decode("utf-8-sig"))
    errors = validate_questions(rows)
    questions = [normalize_question(row) for row in rows] if not errors else []
    if dry_run or errors:
        return {"ok": not errors, "dryRun": True, "total": len(rows), "questions": questions, "errors": errors}
    persist_questions(db, questions)
    audit(db, session, "theory_questions_import", file.filename or "theory.csv", {"count": len(questions)})
    db.commit()
    return {"ok": True, "dryRun": False, "total": len(rows), "questions": questions, "errors": []}


def load_questions(db: Session) -> list[dict]:
    rows = db.scalars(select(TheoryQuestion).order_by(TheoryQuestion.created_at)).all()
    if rows:
        return [question_dict(row) for row in rows]
    defaults = [normalize_question(item) for item in DEFAULT_QUESTIONS]
    persist_questions(db, defaults)
    db.commit()
    return defaults


def persist_questions(db: Session, questions: list[dict]) -> None:
    existing = {row.id: row for row in db.scalars(select(TheoryQuestion)).all()}
    seen = set()
    for item in questions:
        seen.add(item["id"])
        row = existing.get(item["id"]) or TheoryQuestion(id=item["id"])
        row.stem = item["stem"]
        row.options = item["options"]
        row.answer = item["answer"]
        row.explanation = item["explanation"]
        row.category = item["category"]
        row.online = item["online"]
        db.add(row)
    for qid, row in existing.items():
        if qid not in seen:
            db.delete(row)


def question_dict(row: TheoryQuestion) -> dict:
    return {
        "id": row.id,
        "stem": row.stem,
        "options": row.options or [],
        "answer": row.answer,
        "explanation": row.explanation,
        "category": row.category,
        "online": row.online,
    }


def attempt_payload(row: TheoryAttempt, correct: int | None = None) -> dict:
    correct_count = correct if correct is not None else sum(1 for item in row.detail or [] if item.get("correct"))
    return {
        "id": row.id,
        "studentId": row.student_id,
        "at": int(row.created_at.timestamp() * 1000) if row.created_at else now_ms(),
        "total": row.total,
        "correct": correct_count,
        "score": row.score,
        "details": row.detail or [],
    }


def public_question(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "answer"}


def normalize_question(row: dict) -> dict:
    options = row.get("options", [])
    if isinstance(options, str):
        options = [item.strip() for item in options.replace("；", ";").split(";") if item.strip()]
    return {
        "id": row.get("id") or uid("theory"),
        "stem": str(row.get("stem", "")).strip(),
        "options": options,
        "answer": str(row.get("answer", "")).strip(),
        "explanation": str(row.get("explanation", "")).strip(),
        "category": str(row.get("category", "理论知识")).strip(),
        "online": row.get("online", True) is not False,
    }


def parse_question_csv(text: str) -> list[dict]:
    reader = csv.DictReader(StringIO(text))
    rows = []
    for index, row in enumerate(reader, start=2):
        rows.append(
            {
                "row": index,
                "stem": row.get("题干") or row.get("stem") or "",
                "options": row.get("选项") or row.get("options") or "",
                "answer": row.get("答案") or row.get("answer") or "",
                "explanation": row.get("解析") or row.get("explanation") or "",
                "category": row.get("分类") or row.get("category") or "理论知识",
                "online": (row.get("上线") or row.get("online") or "true") not in {"false", "0", "否"},
            },
        )
    return rows


def validate_questions(rows: list[dict]) -> list[dict]:
    errors = []
    for row in rows:
        if not row.get("stem") or not row.get("answer"):
            errors.append({"row": row["row"], "field": "stem,answer", "message": "题干和答案必填"})
            continue
        options = [item.strip() for item in str(row.get("options", "")).replace("；", ";").split(";") if item.strip()]
        if len(options) < 2:
            errors.append({"row": row["row"], "field": "options", "message": "至少需要 2 个选项，使用分号分隔"})
            continue
        if row["answer"] not in options:
            errors.append({"row": row["row"], "field": "answer", "message": "答案必须包含在选项中"})
    return errors
