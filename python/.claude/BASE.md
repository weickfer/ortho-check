Aí sim — agora você está pedindo algo de nível **projeto real**. Vou te entregar um PRD + backend completo já estruturado em Python, seguindo o padrão que você usava em Java (**entities / repositories / services / controllers**), mas adaptado pro ecossistema certo.

---

# 📄 PRD — Sistema de Auditoria Geoespacial (MVP)

## 🎯 Objetivo

Permitir que usuários:

* desenhem uma área (ROI) no mapa
* registrem essa área no sistema
* recortem automaticamente imagens georreferenciadas (GeoTIFF)
* analisem visualmente o conteúdo da área

---

## 🧠 Problema

Atualmente, a validação de obras é:

* manual
* sujeita a erro
* difícil de auditar

---

## 💡 Solução

Sistema backend que:

1. armazena áreas geográficas (PostGIS)
2. processa imagens (GeoTIFF)
3. gera recortes automáticos
4. expõe via API

---

## 📦 Escopo do MVP

### ✅ Inclui:

* CRUD de áreas de auditoria
* cálculo de área
* recorte de imagem via polígono
* API REST

### ❌ Não inclui (ainda):

* IA avançada
* comparação temporal
* fila de processamento

---

# 🧱 Arquitetura

```text
FastAPI
 ├── Controllers
 ├── Services
 ├── Repositories
 ├── Entities (SQLAlchemy + PostGIS)
 └── Geoprocessamento (Rasterio)
```

---

# 🗂️ Estrutura de pastas

```text
/ortho-check/
├── python/
│   ├── src/
│   │   ├── main.py
│
│   ├── controllers/
│   │   └── audit_area_controller.py
│
│   ├── services/
│   │   └── audit_area_service.py
│
│   ├── repositories/
│   │   └── audit_area_repository.py
│
│   ├── entities/
│   │   └── audit_area.py
│
│   ├── schemas/
│   │   └── audit_area_schema.py
│
│   ├── geoprocessing/
│   │   └── raster_service.py
│
│   ├── core/
│   │   └── database.py
│
├── data/
│   ├── tiffs/
│   └── outputs/
│
├── requirements.txt
├── Dockerfile
|-- docker/
|---- docker-compose.yaml
```

---

# 🧩 Código

---

## 🔹 main.py

```python
from fastapi import FastAPI
from app.controllers.audit_area_controller import router

app = FastAPI()
app.include_router(router)
```

---

## 🔹 database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:postgres@db:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
```

---

## 🔹 entity (AuditArea)

```python
from sqlalchemy import Column, Integer, String, Date, DateTime, Float
from geoalchemy2 import Geometry
from datetime import datetime
from app.core.database import Base

class AuditArea(Base):
    __tablename__ = "audit_areas"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    geometry = Column(Geometry("POLYGON", srid=4326))
    area_sq_meters = Column(Float)
    captured_at = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🔹 schema

```python
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
```

---

## 🔹 repository

```python
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
```

---

## 🔹 service (equivalente ao seu Java)

```python
from shapely import wkt
from app.entities.audit_area import AuditArea
from app.repositories.audit_area_repository import AuditAreaRepository
import math

class AuditAreaService:

    def __init__(self):
        self.repo = AuditAreaRepository()

    def create(self, db, request):
        geom = wkt.loads(request.geometry)

        area = self.calculate_area(geom)

        entity = AuditArea(
            description=request.description,
            geometry=f"SRID=4326;{request.geometry}",
            captured_at=request.captured_at,
            area_sq_meters=area
        )

        return self.repo.save(db, entity)

    def calculate_area(self, polygon):
        centroid_lat = polygon.centroid.y
        lat_rad = math.radians(centroid_lat)

        meters_per_deg_lat = 111132.92
        meters_per_deg_lon = 111132.92 * math.cos(lat_rad)

        area_deg = polygon.area
        return area_deg * meters_per_deg_lat * meters_per_deg_lon
```

---

## 🔹 controller

```python
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
```

---

# 🌍 Geoprocessamento (recorte TIFF)

```python
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import uuid

def crop_tiff(tiff_path, geojson, output_dir="/data/outputs"):
    gdf = gpd.GeoDataFrame.from_features(geojson["features"])

    with rasterio.open(tiff_path) as src:
        gdf = gdf.set_crs("EPSG:4326").to_crs(src.crs)

        out_image, out_transform = mask(src, gdf.geometry, crop=True)

        filename = f"{uuid.uuid4()}.png"
        output_path = f"{output_dir}/{filename}"

        meta = src.meta.copy()
        meta.update({
            "driver": "PNG",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })

        with rasterio.open(output_path, "w", **meta) as dest:
            dest.write(out_image)

    return output_path
```