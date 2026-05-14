"""
Experimento 02: Comparação de avanço físico com imagens reais recortadas de GeoTIFFs.

Fluxo:
    1. Recorta o polígono de auditoria de dois TIFFs (datas diferentes) usando rasterio
    2. Envia as duas imagens recortadas para o GPT-4o
    3. Pede análise de avanço físico informando a área real e as datas

Uso:
    python comparar_avanco_02.py

Pré-requisitos:
    - OPENAI_API_KEY definida no ambiente
    - TIFFs em /data/03-03-2026.tif e /data/13-02-2026.tif
    - pip install openai python-dotenv rasterio shapely geopandas
"""

import os
import sys
import base64
import tempfile
from pathlib import Path

# ── Carrega .env se existir ───────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely import wkt
from openai import OpenAI

# ── Configurações ─────────────────────────────────────────────────────────────
DATA_DIR = Path("/data")

# Polígono da área de auditoria (WKT em EPSG:4326)
POLYGON_WKT = (
    "POLYGON (("
    "-59.863968526324484 -3.284054671351626, "
    "-59.86380066089423 -3.284175637778503, "
    "-59.86323867662769 -3.283341988522011, "
    "-59.86337296892736 -3.2832618298930925, "
    "-59.863968526324484 -3.284054671351626"
    "))"
)

AREA_M2 = 2232.60  # área do polígono em metros quadrados

# TIFFs e suas datas
# TIFF_ANTES  = DATA_DIR / "03-03-2026.tif"
# DATE_ANTES  = "03/03/2026"
TIFF_ANTES  = DATA_DIR / "13-02-2026.tif"
DATE_ANTES  = "13/02/2026"

TIFF_DEPOIS = DATA_DIR / "03-03-2026.tif"
DATE_DEPOIS = "03/03/2026"
# TIFF_DEPOIS = DATA_DIR / "13-02-2026.tif"
# DATE_DEPOIS = "13/02/2026"

MODEL = "gpt-4o"
MAX_TOKENS = 2000

# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "Você é um auditor sênior de obras rodoviárias do DNIT, especializado em "
    "análise de imagens ortomosaicas obtidas por drones. "
    "Sua função é comparar duas imagens de uma mesma área de obra capturadas em "
    "datas diferentes e identificar com precisão o avanço físico da obra."
)

USER_PROMPT = """\
Você recebeu DUAS imagens ortomosaicas recortadas da MESMA área de auditoria de uma obra.

📐 Dados da área:
- Área total do recorte: {area_m2:.2f} m²
- Coordenadas do polígono (WGS84): {polygon_wkt}

📅 Datas:
- Imagem 1 (ANTES): capturada em {date_antes}
- Imagem 2 (DEPOIS): capturada em {date_depois}
- Intervalo entre capturas: {dias_intervalo} dias

Analise as duas imagens e responda em português:

## 1. Descrição geral de cada imagem
Descreva brevemente o que se observa em cada imagem (elementos de obra, terreno, estruturas).

## 2. Avanços físicos identificados
Para cada mudança detectada entre ANTES e DEPOIS:
- O que mudou (elemento de obra, pavimentação, terraplenagem, estrutura, etc.)
- Localização aproximada na imagem
- Mensuração: estime a área afetada pela mudança em m² (usando a área total de {area_m2:.2f} m² como referência)
- Nível de confiança: [ALTO | MÉDIO | BAIXO]

## 3. Estimativa de avanço físico (%)
Estime o percentual de avanço físico da obra entre as duas datas.
Considere a proporção da área que sofreu alteração em relação à área total.
Formato: X% — Justificativa: ...

## 4. Elementos sem alteração
Partes da área que permaneceram visualmente iguais entre as duas datas.

## 5. Observações técnicas
Anomalias, riscos ou pontos de atenção (erosão, drenagem, acúmulo de material, etc.)

Seja direto, técnico e QUANTITATIVO. Use a área de {area_m2:.2f} m² como base para mensurar as mudanças.
"""

# ── Funções ───────────────────────────────────────────────────────────────────

def crop_tiff_to_png(tiff_path: Path, geometry, output_path: Path):
    """Recorta o TIFF pelo polígono e salva como PNG."""
    gdf = gpd.GeoDataFrame({"geometry": [geometry]}, crs="EPSG:4326")

    with rasterio.open(tiff_path) as src:
        gdf_proj = gdf.to_crs(src.crs)
        out_image, out_transform = mask(src, gdf_proj.geometry, crop=True)

        meta = src.meta.copy()
        meta.update({
            "driver": "PNG",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
        })

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output_path, "w", **meta) as dest:
            dest.write(out_image)

    print(f"[info] Recortado: {tiff_path.name} → {output_path}")
    return output_path


def encode_image(path: Path) -> str:
    """Converte imagem para base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_image_content(path: Path, label: str) -> list[dict]:
    """Retorna os blocos de conteúdo (texto + imagem) para a mensagem."""
    b64 = encode_image(path)
    return [
        {"type": "text", "text": f"--- {label} ---"},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"},
        },
    ]


def comparar_avanco(img_antes: Path, img_depois: Path) -> str:
    """Envia as duas imagens recortadas para o GPT-4o e retorna a análise."""
    client = OpenAI()

    from datetime import datetime
    d1 = datetime.strptime(DATE_ANTES, "%d/%m/%Y")
    d2 = datetime.strptime(DATE_DEPOIS, "%d/%m/%Y")
    dias = (d2 - d1).days

    prompt = USER_PROMPT.format(
        area_m2=AREA_M2,
        polygon_wkt=POLYGON_WKT,
        date_antes=DATE_ANTES,
        date_depois=DATE_DEPOIS,
        dias_intervalo=dias,
    )

    content = (
        [{"type": "text", "text": prompt}]
        + build_image_content(img_antes,  f"Imagem 1 — ANTES ({DATE_ANTES})")
        + build_image_content(img_depois, f"Imagem 2 — DEPOIS ({DATE_DEPOIS})")
    )

    print(f"[info] Enviando imagens para {MODEL} (temperature=0.0)...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": content},
        ],
        max_tokens=MAX_TOKENS,
        temperature=0.0,
    )

    return response.choices[0].message.content


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Valida API key
    if not os.getenv("OPENAI_API_KEY"):
        print("[erro] OPENAI_API_KEY não encontrada no ambiente.")
        sys.exit(1)

    # Valida TIFFs
    for tiff in (TIFF_ANTES, TIFF_DEPOIS):
        if not tiff.exists():
            print(f"[erro] TIFF não encontrado: {tiff}")
            sys.exit(1)

    # Parseia o polígono
    geometry = wkt.loads(POLYGON_WKT)
    print(f"[info] Polígono: {geometry.geom_type} com {len(geometry.exterior.coords)} vértices")
    print(f"[info] Área informada: {AREA_M2} m²")

    # Recorta as imagens
    output_dir = Path("/data/outputs/experimento02")
    img_antes  = crop_tiff_to_png(TIFF_ANTES,  geometry, output_dir / "antes.png")
    img_depois = crop_tiff_to_png(TIFF_DEPOIS, geometry, output_dir / "depois.png")

    print()
    print(f"[info] Imagem ANTES : {img_antes}  (data: {DATE_ANTES})")
    print(f"[info] Imagem DEPOIS: {img_depois} (data: {DATE_DEPOIS})")
    print()

    # Envia para análise
    resultado = comparar_avanco(img_antes, img_depois)

    print("=" * 60)
    print(f"ANÁLISE DE AVANÇO FÍSICO — {DATE_ANTES} → {DATE_DEPOIS}")
    print("=" * 60)
    print(resultado)
    print("=" * 60)


if __name__ == "__main__":
    main()
