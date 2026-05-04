from pydantic import BaseModel
from datetime import date, datetime

class CreateAuditAreaRequest(BaseModel):
    description: str
    geometry: str
    captured_at: date

class AuditAreaResponse(BaseModel):
    id: int
    description: str
    geometry: str
    area_square_meters: float
    captured_at: date
    created_at: datetime
