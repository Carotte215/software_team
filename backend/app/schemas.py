from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionInfo(BaseModel):
    student_id: str = Field(alias="studentId")
    role: str = "student"


class LoginRequest(BaseModel):
    student_id: str = Field(alias="studentId")
    role: str = "student"
    password: str = ""


class PasswordResetRequest(BaseModel):
    student_id: str = Field(alias="studentId")
    new_password: str = Field(alias="newPassword")


class ApplicationCreate(BaseModel):
    type: str
    subtype: str = ""
    form: dict[str, Any] = Field(default_factory=dict)
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    remark: str = ""


class ApplicationDecision(BaseModel):
    comment: str = ""
    reason: str = ""
    new_status: str = Field(default="", alias="newStatus")


class NoticePublish(BaseModel):
    title: str
    summary: str = ""
    content: str = ""
    tags: list[str] = Field(default_factory=list)
    target_rule: dict[str, Any] = Field(default_factory=lambda: {"kind": "all"}, alias="targetRule")
    source: str = "管理老师"
    scheduled_at: int = Field(default=0, alias="scheduledAt")


class AcademicProgressPut(BaseModel):
    modules: list[dict[str, Any]] = Field(default_factory=list)


class AcademicPlanPut(BaseModel):
    grade: str
    major: str
    modules: list[dict[str, Any]] = Field(default_factory=list)


class TranscriptMetaCreate(BaseModel):
    meta: dict[str, Any] = Field(default_factory=dict)


class KnowledgeCreate(BaseModel):
    title: str
    category: str
    tags: list[str] = Field(default_factory=list)
    summary: str
    body: str = ""
    official_link: str = Field(default="", alias="officialLink")
    sensitive_hint: bool = Field(default=False, alias="sensitiveHint")
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class KnowledgeUpdate(KnowledgeCreate):
    online: bool = True


class KnowledgeOnlinePut(BaseModel):
    online: bool = True


class HonorCreate(BaseModel):
    title: str
    winner: str
    year: int
    major: str = ""
    grade: str = ""
    category: str = ""
    intro: str = ""
    visibility: str = "public"
    online: bool = True
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class HonorOnlinePut(BaseModel):
    online: bool = True


class ApplicationTemplateCreate(BaseModel):
    name: str
    apply_type: str = Field(default="", alias="applyType")
    subtype: str = ""
    body_html: str = Field(default="", alias="bodyHtml")


class ApplicationTemplateUpdate(ApplicationTemplateCreate):
    pass


class TemplateFileCreate(BaseModel):
    name: str
    scene: str = ""
    format: str = "docx"
    file_url: str = Field(default="", alias="fileUrl")
    file_id: str = Field(default="", alias="fileId")


class TemplateFileUpdate(TemplateFileCreate):
    pass


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(alias="oldPassword")
    new_password: str = Field(alias="newPassword")


class NoticeImport(BaseModel):
    title: str
    summary: str = ""
    content: str = ""
    tags: list[str] = Field(default_factory=list)
    source: str = "外部导入"


class NoticeFetchUrl(BaseModel):
    url: str
    source: str = "网页抓取"


class ApiMessage(BaseModel):
    ok: bool = True
    message: str = ""
    data: Any | None = None


def ms(dt: datetime | None) -> int | None:
    if not dt:
        return None
    return int(dt.timestamp() * 1000)
