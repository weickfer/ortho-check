from sqlalchemy import Column, Integer, String, Date, DateTime, Float
from geoalchemy2 import Geometry
from datetime import datetime
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditArea(Base):
    __tablename__ = "audit_areas"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    geometry = Column(Geometry("POLYGON", srid=4326))
    area_sq_meters = Column(Float)
    image_path = Column(String, nullable=False)
    captured_at = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    analyses = relationship(
        "AuditAnalysis",
        back_populates="audit_area",
        order_by="AuditAnalysis.created_at.desc()"
    )