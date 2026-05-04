import rasterio
from rasterio.mask import mask
import geopandas as gpd
import uuid
import os

def crop_tiff(tiff_path, geometry, output_dir="/data/outputs"):
    # Verifica se recebemos um GeoJSON (dict) ou um objeto Shapely direto
    if isinstance(geometry, dict):
        gdf = gpd.GeoDataFrame.from_features(geometry["features"])
    else:
        # Se for um objeto shapely direto (como o 'geom'), cria o GeoDataFrame com ele
        gdf = gpd.GeoDataFrame({'geometry': [geometry]})

    with rasterio.open(tiff_path) as src:
        gdf = gdf.set_crs("EPSG:4326").to_crs(src.crs)

        out_image, out_transform = mask(src, gdf.geometry, crop=True)

        filename = f"{uuid.uuid4()}.png"
        
        # Garante que o diretório de destino exista antes de salvar
        os.makedirs(output_dir, exist_ok=True)
        
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
