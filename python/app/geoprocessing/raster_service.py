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
