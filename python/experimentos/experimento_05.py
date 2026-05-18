"""
Experimento 05: Classificação de Recorte Georreferenciado via VLM.

Refatora a lógica do Experimento 04 para atender ao novo escopo:
analisar uma única imagem (já recortada pelo rasterio) e retornar
APENAS um array JSON contendo as categorias identificadas na área.

Fluxo:
    1. Carrega uma imagem de recorte (ex: /data/recorte_poligono.png)
    2. Codifica a imagem em base64
    3. Envia para o GPT-4o com prompt restritivo e modo JSON ativado
    4. Exibe a saída de dados estruturada

Pré-requisitos:
    - OPENAI_API_KEY definida no ambiente
    - Imagem em /data/recorte_poligono.png
    - pip install openai python-dotenv
"""

import os
import sys
import base64
import json
from pathlib import Path

# ── Carrega .env se existir ──────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

# ── Configurações ─────────────────────────────────────────────────────────────
DATA_DIR = Path("/data/outputs")
IMAGE_CROP = DATA_DIR / "f48488b4-b6dc-4332-805a-af197fed14ea-teste.png"

MODEL = "gpt-4o"
MAX_TOKENS = 500 # Reduzido, pois a saída esperada é apenas um JSON curto

# ── Prompts Restritivos ───────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "Atue como um classificador de dados para um sistema integrado de "
    "Sistemas de Informação Geográfica (GIS). A sua função é analisar recortes "
    "de ortoimagens e categorizar o conteúdo visual de forma estrita. "
    "Você deve retornar EXCLUSIVAMENTE um objeto JSON válido. "
    "É estritamente proibido incluir qualquer texto explicativo, saudações "
    "ou formatação Markdown fora do escopo do JSON."
)

USER_PROMPT = (
    "Analise a imagem aérea fornecida, que representa o recorte exato de um "
    "polígono de interesse em um canteiro de obras. Identifique os elementos "
    "e as fases de construção presentes estritamente dentro da imagem. "
    "Selecione as categorias correspondentes EXCLUSIVAMENTE a partir da "
    "seguinte lista predefinida: "
    "['terraplanagem', 'fundacao', 'estrutura_metalica', 'pavimentacao', "
    "'vegetacao', 'maquinario', 'solo_exposto', 'concreto_armado']. "
    "Retorne o resultado no seguinte formato JSON: "
    "{\"categorias\": [\"item1\", \"item2\"]}"
)


# ── Funções ───────────────────────────────────────────────────────────────────

def encode_image(path: Path) -> str:
    """Converte imagem para base64 data-URI (image/png)."""
    with open(path, "rb") as f:
        raw = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{raw}"


def analyze_cropped_area(img_crop: Path) -> dict:
    """
    Envia o recorte georreferenciado para o GPT-4o configurado no modo JSON.
    Retorna um dicionário Python contendo as categorias identificadas.
    """
    client = OpenAI()

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": USER_PROMPT,
                },
                {
                    "type": "image_url",
                    "image_url": {"url": encode_image(img_crop)},
                },
            ],
        },
    ]

    print(f"[info] Processando classificação via {MODEL}...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=0.0,
        response_format={ "type": "json_object" } # Garante a formatação da saída
    )

    raw_response = response.choices[0].message.content
    
    # Converte a string JSON para um dicionário Python para validação
    try:
        data_json = json.loads(raw_response)
        return data_json
    except json.JSONDecodeError:
        print("[erro] A resposta não pôde ser decodificada como JSON.")
        return {"categorias": []}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Valida API key
    if not os.getenv("OPENAI_API_KEY"):
        print("[erro] OPENAI_API_KEY não encontrada no ambiente.")
        sys.exit(1)

    # Valida imagem do recorte
    if not IMAGE_CROP.exists():
        print(f"[erro] Imagem de recorte não encontrada: {IMAGE_CROP}")
        sys.exit(1)

    print(f"[info] Imagem de Recorte (Input) : {IMAGE_CROP}")
    print()

    # Executa a inferência
    resultado_estruturado = analyze_cropped_area(IMAGE_CROP)

    print("=" * 60)
    print("DADOS ESTRUTURADOS EXTRAÍDOS (JSON)")
    print("=" * 60)
    
    # Exibe o resultado formatado de forma legível no terminal
    print(json.dumps(resultado_estruturado, indent=4, ensure_ascii=False))
    
    print("=" * 60)

if __name__ == "__main__":
    main()