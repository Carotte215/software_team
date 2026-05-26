from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.migrate import ensure_schema
from app.db.session import Base, engine
from app.routers import (
    academic,
    application_templates,
    applications,
    auth,
    files,
    health,
    honors,
    knowledge,
    notices,
    party,
    students,
    templates,
    theory,
    workbench,
)
from app.services.scheduler import start_schedulers

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables() -> None:
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    ensure_schema(engine)
    start_schedulers()


app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(application_templates.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(notices.router, prefix="/api")
app.include_router(party.router, prefix="/api")
app.include_router(academic.router, prefix="/api")
app.include_router(honors.router, prefix="/api")
app.include_router(theory.router, prefix="/api")
app.include_router(workbench.router, prefix="/api")
