"""
Experimento 03: Observabilidade espacial de elementos em recorte de GeoTIFF.

Fluxo:
    1. Recorta o polígono de auditoria de um TIFF usando rasterio.
    2. Envia a imagem recortada para o modelo visual.
    3. Retorna uma análise estruturada baseada exclusivamente em evidências visuais.

Pré-requisitos:
    - OPENAI_API_KEY definida no ambiente
    - TIFF em /data/03-03-2026.tif
    - pip install openai python-dotenv rasterio shapely geopandas
"""

import os
import sys
import base64
from pathlib import Path

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

# TIFF e data única
TIFF = DATA_DIR / "03-03-2026.tif"
DATE = "03/03/2026"

MODEL = "gpt-4o"
MAX_TOKENS = 2000

# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Você é um sistema de observação visual para auditoria de obras.

Sua função é identificar elementos visualmente observáveis
em imagens ortomosaicas de obras obtidas por drones.

Regras:
- Use apenas evidências visuais.
- Não invente informações técnicas.
- Não estime percentual de avanço.
- Não estime área em m².
- Não faça conclusões sobre cronograma.
- Não faça avaliações de engenharia.
- Se houver dúvida, indique explicitamente.

Sua saída deve ser objetiva e estruturada.
"""

USER_PROMPT = """\
Você recebeu uma imagem ortomosaica recortada de uma obra rodoviária.

📐 Contexto:
- Área do recorte: {area_m2:.2f} m²
- Data da imagem: {date}
- Coordenadas do polígono: {polygon_wkt}

Analise SOMENTE elementos visualmente observáveis.

Categorias permitidas:
- escavação
- terraplenagem
- concreto
- pilares
- vigas
- tabuleiro de ponte
- maquinário
- estoque de materiais
- drenagem
- vegetação
- solo exposto
- estruturas provisórias
- corpos d'água

Responda EXATAMENTE neste formato:

# ELEMENTOS IDENTIFICADOS

Para cada elemento:
- classe:
- localização aproximada:
- confiança: [ALTA|MEDIA|BAIXA]
- evidência visual:

# ELEMENTOS INCERTOS

Liste elementos que não puderam ser identificados com confiança.

# RESUMO OBJETIVO

Resumo curto da cena observada.

Regras:
- Não invente medições.
- Não use linguagem subjetiva.
- Não faça interpretações de engenharia.
- Use somente evidências visuais.
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


def build_image_content(path: Path) -> list[dict]:
    """Cria a estrutura de conteúdo da imagem para a API."""
    b64 = encode_image(path)

    return [{
        "type": "image_url",
        "image_url": {
            "url": f"data:image/png;base64,{b64}",
            "detail": "high"
        },
    }]


def analisar_imagem(img: Path) -> str:
    """Envia a imagem recortada para o modelo e retorna a análise."""
    client = OpenAI()

    prompt = USER_PROMPT.format(
        area_m2=AREA_M2,
        date=DATE,
        polygon_wkt=POLYGON_WKT,
    )

    content = (
        [{"type": "text", "text": prompt}]
        + build_image_content(img)
    )

    print(f"[info] Enviando imagem para {MODEL} (temperature=0.0)...")
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

    # Valida o TIFF
    if not TIFF.exists():
        print(f"[erro] TIFF não encontrado: {TIFF}")
        sys.exit(1)

    # Parseia o polígono
    geometry = wkt.loads(POLYGON_WKT)
    print(f"[info] Polígono: {geometry.geom_type} com {len(geometry.exterior.coords)} vértices")
    print(f"[info] Área informada: {AREA_M2} m²")

    # Recorta a imagem
    output_dir = Path("/data/outputs/experimento03")
    img = crop_tiff_to_png(TIFF, geometry, output_dir / "experimento03-crop.png")

    print()

    # Envia para análise
    resultado = analisar_imagem(img)

    print("=" * 60)
    print(f"ANÁLISE DE OBSERVAÇÃO VISUAL — {DATE}")
    print("=" * 60)
    print(resultado)
    print("=" * 60)


if __name__ == "__main__":
    main()