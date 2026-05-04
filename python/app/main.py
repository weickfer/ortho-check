from fastapi import FastAPI
from app.controllers.audit_area_controller import router
from app.core.database import Base, engine
from app.entities.audit_area import AuditArea

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router)
