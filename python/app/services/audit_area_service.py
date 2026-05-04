from shapely import wkt
from app.entities.audit_area import AuditArea
from app.entities.audit_analylis import AuditAnalysis
from app.repositories.audit_area_repository import AuditAreaRepository
from app.geoprocessing.raster_service import crop_tiff
from app.services.openai_service import analyze_bridge_image
import math

class AuditAreaService:

    def __init__(self):
        self.repo = AuditAreaRepository()

    def create(self, db, request):
        geom = wkt.loads(request.geometry)

        area = self.calculate_area(geom)

        output_path = crop_tiff("/data/02-02-2026.tif", geom, "/data/outputs")
        
        entity = AuditArea(
            description=request.description,
            geometry=f"SRID=4326;{request.geometry}",
            captured_at=request.captured_at,
            image_path=output_path,
            area_sq_meters=area
        )

        saved_entity = self.repo.save(db, entity)

        # Pipeline de IA: Analisa a imagem da ponte com OpenAI
        ai_analysis_result = analyze_bridge_image(output_path)

        # Salva o resultado no banco
        analysis = AuditAnalysis(
            audit_area_id=saved_entity.id,
            description=ai_analysis_result
        )
        db.add(analysis)
        db.commit()

        return saved_entity

    def calculate_area(self, polygon):
        centroid_lat = polygon.centroid.y
        lat_rad = math.radians(centroid_lat)

        meters_per_deg_lat = 111132.92
        meters_per_deg_lon = 111132.92 * math.cos(lat_rad)

        area_deg = polygon.area
        return area_deg * meters_per_deg_lat * meters_per_deg_lon
