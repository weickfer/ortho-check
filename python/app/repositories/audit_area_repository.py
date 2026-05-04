from sqlalchemy.orm import Session
from app.entities.audit_area import AuditArea

class AuditAreaRepository:

    def save(self, db: Session, entity: AuditArea):
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    def find_all(self, db: Session):
        return db.query(AuditArea).all()

    def find_by_id(self, db: Session, id: int):
        return db.query(AuditArea).filter(AuditArea.id == id).first()
