from fastapi import APIRouter, Depends, HTTPException
import json
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import AcademicPlan, AcademicProgress, Application, AuditLog, KnowledgeItem, KnowledgeMissKeyword, LeagueProgress, Notice, NoticeBatch, PartyProgress, PartyStage, SmsSimulation, Student
from app.routers.academic import _resolve_academic_plan
from app.services.permissions import scoped_student_ids
from app.services.serializers import audit_log

router = APIRouter(tags=["workbench"])

RISK_ORDER = {"高": 0, "中": 1, "低": 2, "数据缺失": 3}


def knowledge_miss_rows(db: Session, limit: int) -> list[dict]:
    rows = db.scalars(select(KnowledgeMissKeyword).order_by(KnowledgeMissKeyword.count.desc()).limit(limit)).all()
    if rows:
        return [
            {"keyword": row.keyword, "count": row.count, "lastAt": int(row.updated_at.timestamp() * 1000) if row.updated_at else None}
            for row in rows
        ]
    count_expr = func.count().label("count")
    last_at_expr = func.max(AuditLog.at).label("last_at")
    legacy = db.execute(
        select(AuditLog.target, count_expr, last_at_expr)
        .where(AuditLog.action == "knowledge_miss", AuditLog.target != "")
        .group_by(AuditLog.target)
        .order_by(count_expr.desc())
        .limit(limit),
    ).all()
    return [
        {
            "keyword": row._mapping["target"],
            "count": row._mapping["count"],
            "lastAt": int(row._mapping["last_at"].timestamp() * 1000) if row._mapping["last_at"] else None,
        }
        for row in legacy
    ]


@router.get("/workbench/summary")
def summary(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader", "coordinator"}:
        raise HTTPException(status_code=403, detail="forbidden")
    student_filter = None
    if session.role == "coordinator":
        current = db.get(Student, session.student_id)
        if not current:
            raise HTTPException(status_code=404, detail="student not found")
        student_filter = select(Student.student_id).where(Student.class_name == current.class_name)
        student_count = db.scalar(select(func.count()).select_from(Student).where(Student.class_name == current.class_name)) or 0
    else:
        student_count = db.scalar(select(func.count()).select_from(Student)) or 0
    pending_stmt = select(func.count()).select_from(Application).where(Application.status == "审批中")
    if student_filter is not None:
        pending_stmt = pending_stmt.where(Application.student_id.in_(student_filter))
    miss_count = db.scalar(select(func.count()).select_from(KnowledgeMissKeyword)) or 0
    if not miss_count:
        miss_count = db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == "knowledge_miss")) or 0
    return {
        "students": student_count,
        "pendingApps": db.scalar(pending_stmt) or 0,
        "miss": miss_count,
        "batches": db.scalar(select(func.count()).select_from(NoticeBatch)) or 0,
        "sms": db.scalar(select(func.count()).select_from(SmsSimulation)) or 0,
    }


@router.get("/leader/dashboard")
def leader_dashboard(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "leader":
        raise HTTPException(status_code=403, detail="forbidden")
    apps = db.scalars(select(Application)).all()
    by_status: dict[str, int] = {}
    for app in apps:
        by_status[app.status] = by_status.get(app.status, 0) + 1
    return {
        "students": db.scalar(select(func.count()).select_from(Student)) or 0,
        "knowledgeCount": db.scalar(select(func.count()).select_from(KnowledgeItem)) or 0,
        "noticeCount": db.scalar(select(func.count()).select_from(Notice)) or 0,
        "pendingApps": by_status.get("审批中", 0),
        "applicationsByStatus": by_status,
        "missKeywordsTop": knowledge_miss_rows(db, 5),
        "academicHighRiskStudents": count_high_risk_students(db),
        "batches": db.scalar(select(func.count()).select_from(NoticeBatch)) or 0,
        "partyProgress": party_progress_stats(db),
        "leagueProgress": league_progress_stats(db),
        "lastReset": None,
    }


def party_progress_stats(db: Session) -> dict:
    stages = {row.stage_key: row.name for row in db.scalars(select(PartyStage)).all()}
    if not stages:
        from app.services.party_official_data import OFFICIAL_FLOW_STAGES

        stages = {item["key"]: item["name"] for item in OFFICIAL_FLOW_STAGES}
    by_stage: dict[str, int] = {}
    pending_verify = 0
    for row in db.scalars(select(PartyProgress)).all():
        by_stage[row.current_key] = by_stage.get(row.current_key, 0) + 1
        completed = set(row.completed_steps or [])
        verified = set(row.verified_steps or [])
        pending_verify += len(completed - verified)
    return {
        "total": sum(by_stage.values()),
        "byStage": [{"key": key, "name": stages.get(key, key), "count": count} for key, count in sorted(by_stage.items())],
        "pendingVerifySteps": pending_verify,
    }


def league_progress_stats(db: Session) -> dict:
    from app.services.party_official_data import LEAGUE_FLOW_STAGES

    stages = {item["key"]: item["name"] for item in LEAGUE_FLOW_STAGES}
    by_stage: dict[str, int] = {}
    pending_verify = 0
    for row in db.scalars(select(LeagueProgress)).all():
        by_stage[row.current_key] = by_stage.get(row.current_key, 0) + 1
        completed = set(row.completed_steps or [])
        verified = set(row.verified_steps or [])
        pending_verify += len(completed - verified)
    return {
        "total": sum(by_stage.values()),
        "byStage": [{"key": key, "name": stages.get(key, key), "count": count} for key, count in sorted(by_stage.items())],
        "pendingVerifySteps": pending_verify,
    }


@router.get("/audit/logs")
def logs(limit: int = 120, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    rows = db.scalars(select(AuditLog).order_by(AuditLog.at.desc()).limit(limit)).all()
    return {"list": [audit_log(row) for row in rows]}


@router.get("/audit/logs/export")
def export_audit_logs(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)):
    import csv
    from io import StringIO
    from urllib.parse import quote

    from fastapi.responses import Response

    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    rows = db.scalars(select(AuditLog).order_by(AuditLog.at.desc()).limit(5000)).all()
    fp = StringIO()
    writer = csv.writer(fp)
    writer.writerow(["时间", "操作人", "角色", "动作", "目标", "详情"])
    for row in rows:
        writer.writerow([
            int(row.at.timestamp() * 1000) if row.at else "",
            row.actor_id,
            row.role,
            row.action,
            row.target,
            json.dumps(row.detail or {}, ensure_ascii=False) if row.detail else "",
        ])
    filename = quote("审计日志导出.csv")
    return Response(
        "\ufeff" + fp.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/workbench/knowledge/misses")
def knowledge_misses(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader", "coordinator"}:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"list": knowledge_miss_rows(db, 50)}


@router.get("/workbench/sms")
def sms_simulation(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader", "coordinator"}:
        raise HTTPException(status_code=403, detail="forbidden")
    rows = db.scalars(select(SmsSimulation).order_by(SmsSimulation.created_at.desc()).limit(100)).all()
    return {
        "list": [
            {
                "id": row.id,
                "batchId": row.batch_id,
                "at": int(row.created_at.timestamp() * 1000) if row.created_at else None,
                "audience": [row.phone_masked],
                "text": row.text,
                "studentId": row.student_id,
            }
            for row in rows
        ],
    }


def count_high_risk_students(db: Session) -> int:
    return sum(1 for row in academic_risk_rows(db) if row["riskLevel"] == "高")


@router.get("/workbench/academic/risks")
def academic_risks(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"list": academic_risk_rows(db)}


def academic_risk_rows(db: Session) -> list[dict]:
    rows = [academic_risk_for_student(db, student) for student in db.scalars(select(Student)).all()]
    return sorted(rows, key=lambda item: (RISK_ORDER.get(item["riskLevel"], 9), -item["totalGap"], item["studentId"]))


def academic_risk_for_student(db: Session, student: Student) -> dict:
    plan = _resolve_academic_plan(db, student.grade, student.major)
    progress = db.get(AcademicProgress, student.student_id)
    if not plan or not progress:
        return {
            "studentId": student.student_id,
            "name": student.name,
            "grade": student.grade,
            "major": student.major,
            "className": student.class_name,
            "riskLevel": "数据缺失",
            "totalGap": 0,
            "gaps": [],
        }
    progress_by_key = {item.get("key"): item for item in (progress.modules or [])}
    gaps = []
    for module in plan.modules or []:
        earned = float(progress_by_key.get(module.get("key"), {}).get("earned", 0))
        required = float(module.get("required", 0))
        gap = max(0, required - earned)
        if gap > 0:
            gaps.append({"key": module.get("key"), "name": module.get("name"), "required": required, "earned": earned, "gap": gap})
    total_gap = sum(item["gap"] for item in gaps)
    risk_level = "高" if any(item["gap"] >= 4 for item in gaps) else "中" if any(item["gap"] >= 2 for item in gaps) else "低"
    return {
        "studentId": student.student_id,
        "name": student.name,
        "grade": student.grade,
        "major": student.major,
        "className": student.class_name,
        "riskLevel": risk_level,
        "totalGap": total_gap,
        "gaps": gaps,
    }


@router.get("/workbench/applications/export")
def export_applications(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)):
    import csv
    from io import StringIO
    from urllib.parse import quote

    from fastapi.responses import Response

    if session.role not in {"teacher", "leader", "coordinator"}:
        raise HTTPException(status_code=403, detail="forbidden")
    stmt = select(Application).order_by(Application.created_at.desc())
    scope_ids = scoped_student_ids(db, session) if session.role == "coordinator" else None
    if scope_ids is not None:
        stmt = stmt.where(Application.student_id.in_(scope_ids))
    rows = db.scalars(stmt).all()
    students = {row.student_id: row for row in db.scalars(select(Student)).all()}
    fp = StringIO()
    writer = csv.writer(fp)
    writer.writerow(["申请ID", "学号", "姓名", "类型", "子类", "状态", "提交时间", "审批意见"])
    for row in rows:
        student = students.get(row.student_id)
        writer.writerow([
            row.id,
            row.student_id,
            student.name if student else "",
            row.type,
            row.subtype or "",
            row.status,
            int(row.created_at.timestamp() * 1000) if row.created_at else "",
            row.teacher_comment or "",
        ])
    filename = quote("申请记录导出.csv")
    return Response(
        "\ufeff" + fp.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
