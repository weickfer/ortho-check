from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.audit_area_service import AuditAreaService
from app.schemas.audit_area_schema import CreateAuditAreaRequest

router = APIRouter(prefix="/api/audit-areas")

service = AuditAreaService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("")
def create(req: CreateAuditAreaRequest, db: Session = Depends(get_db)):
    return service.create(db, req)

@router.get("")
def find_all(db: Session = Depends(get_db)):
    return service.repo.find_all(db)
