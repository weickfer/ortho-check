from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey
from geoalchemy2 import Geometry
from datetime import datetime
from sqlalchemy.orm import relationship

from app.core.database import Base

class AuditAnalysis(Base):
    __tablename__ = "audit_analyses"

    id = Column(Integer, primary_key=True, index=True)
    audit_area_id     = Column(Integer, ForeignKey("audit_areas.id", ondelete="CASCADE"), nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    audit_area = relationship("AuditArea", back_populates="analyses")
    