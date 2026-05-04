from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from typing import List

from app.core.database import SessionLocal
from app.services.audit_area_service import AuditAreaService
from app.schemas.audit_area_schema import CreateAuditAreaRequest, AuditAreaResponse

router = APIRouter(prefix="/api/audit-areas")

service = AuditAreaService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def serialize_audit_area(area) -> AuditAreaResponse:
    # to_shape converte o WKBElement do banco para objeto do shapely
    wkt_geom = to_shape(area.geometry).wkt if area.geometry is not None else ""
    return AuditAreaResponse(
        id=area.id,
        description=area.description,
        geometry=wkt_geom,
        area_square_meters=area.area_sq_meters,
        captured_at=area.captured_at,
        created_at=area.created_at
    )

@router.post("", response_model=AuditAreaResponse)
def create(req: CreateAuditAreaRequest, db: Session = Depends(get_db)):
    area = service.create(db, req)
    return serialize_audit_area(area)

@router.get("", response_model=List[AuditAreaResponse])
def find_all(db: Session = Depends(get_db)):
    areas = service.repo.find_all(db)
    return [serialize_audit_area(a) for a in areas]
