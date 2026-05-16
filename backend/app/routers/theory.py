import csv
import json
from io import StringIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.deps import CurrentSession, get_current_session
from app.services.common import now_ms, uid

router = APIRouter(prefix="/theory", tags=["theory"])

DEFAULT_QUESTIONS = [
    {
        "id": "theory_q1",
        "stem": "入党申请人递交申请书后，通常应接受党组织的谈话和培养教育。",
        "type": "single",
        "options": ["正确", "错误"],
        "answer": "正确",
        "explanation": "入党申请提交后，党组织会安排谈话并开展培养教育。",
        "category": "入党流程",
        "online": True,
    },
    {
        "id": "theory_q2",
        "stem": "发展对象阶段通常需要完成政审、公示和集中培训等材料或环节。",
        "type": "single",
        "options": ["正确", "错误"],
        "answer": "正确",
        "explanation": "发展对象阶段需按组织要求完成相关审查和培训材料。",
        "category": "发展对象",
        "online": True,
    },
]


@router.get("/questions")
def student_questions(session: CurrentSession = Depends(get_current_session)) -> dict:
    rows = [public_question(row) for row in read_questions() if row.get("online", True)]
    attempts = [row for row in read_attempts() if row.get("studentId") == session.student_id]
    return {"list": rows, "latestAttempt": attempts[0] if attempts else None}


@router.post("/attempt")
def submit_attempt(payload: dict, session: CurrentSession = Depends(get_current_session)) -> dict:
    answers = payload.get("answers", {})
    questions = [row for row in read_questions() if row.get("online", True)]
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
    result = {
        "id": uid("attempt"),
        "studentId": session.student_id,
        "at": now_ms(),
        "total": len(questions),
        "correct": correct,
        "score": round(correct * 100 / len(questions), 1) if questions else 0,
        "details": details,
    }
    attempts = [result, *read_attempts()]
    write_json(attempt_path(), attempts[:200])
    return result


@router.get("/workbench/questions")
def admin_questions(session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"list": read_questions()}


@router.put("/workbench/questions")
def save_questions(payload: dict, session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    questions = [normalize_question(row) for row in payload.get("questions", [])]
    write_json(question_path(), questions)
    return {"ok": True, "list": questions}


@router.post("/workbench/questions/import")
async def import_questions(
    file: UploadFile = File(...),
    dry_run: bool = Form(default=True, alias="dryRun"),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    rows = parse_question_csv((await file.read()).decode("utf-8-sig"))
    errors = validate_questions(rows)
    questions = [normalize_question(row) for row in rows] if not errors else []
    if dry_run or errors:
        return {"ok": not errors, "dryRun": True, "total": len(rows), "questions": questions, "errors": errors}
    write_json(question_path(), questions)
    return {"ok": True, "dryRun": False, "total": len(rows), "questions": questions, "errors": []}


def storage_path(name: str) -> Path:
    path = Path(get_settings().upload_dir).parent / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def question_path() -> Path:
    return storage_path("theory_questions.json")


def attempt_path() -> Path:
    return storage_path("theory_attempts.json")


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_questions() -> list[dict]:
    return read_json(question_path(), DEFAULT_QUESTIONS)


def read_attempts() -> list[dict]:
    return read_json(attempt_path(), [])


def public_question(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "answer"}


def normalize_question(row: dict) -> dict:
    options = row.get("options", [])
    if isinstance(options, str):
        options = [item.strip() for item in options.replace("；", ";").split(";") if item.strip()]
    return {
        "id": row.get("id") or uid("theory"),
        "stem": str(row.get("stem", "")).strip(),
        "type": row.get("type") or "single",
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
