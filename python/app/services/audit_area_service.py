from shapely import wkt
from app.entities.audit_area import AuditArea
from app.repositories.audit_area_repository import AuditAreaRepository
from app.geoprocessing.raster_service import crop_tiff
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

        crop_tiff("/data/02-02-2026.tif", geom, "/data/outputs")


        return self.repo.save(db, entity)

    def calculate_area(self, polygon):
        centroid_lat = polygon.centroid.y
        lat_rad = math.radians(centroid_lat)

        meters_per_deg_lat = 111132.92
        meters_per_deg_lon = 111132.92 * math.cos(lat_rad)

        area_deg = polygon.area
        return area_deg * meters_per_deg_lat * meters_per_deg_lon
