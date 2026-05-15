"""
Experimento 04: Reprodução do analyze-controller.js em Python.

Reproduz a lógica do endpoint analyzeProgress do servidor Node.js,
que compara duas imagens aéreas (referência × atual) e gera um
relatório de avanço físico com tabela comparativa de pavimentos.

Fluxo:
    1. Carrega duas imagens (referência e atual) de /data
    2. Codifica ambas em base64
    3. Envia para o GPT-4o com os mesmos prompts do controller JS
    4. Exibe o relatório Markdown gerado

Pré-requisitos:
    - OPENAI_API_KEY definida no ambiente
    - Imagens em /data/ref.png e /data/atual.png (ou ajuste abaixo)
    - pip install openai python-dotenv
"""

import os
import sys
import base64
from pathlib import Path

# ── Carrega .env se existir ──────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

# ── Configurações ─────────────────────────────────────────────────────────────
DATA_DIR = Path("/data")
IMAGE_REF = DATA_DIR / "ref.png"
IMAGE_ATUAL = DATA_DIR / "atual.png"

MODEL = "gpt-4o"
MAX_TOKENS = 2000

# ── Prompts (idênticos ao analyze-controller.js) ─────────────────────────────

SYSTEM_PROMPT = (
    "Você é um Engenheiro Civil fiscal de obras especializado em análise "
    "de imagens aéreas ortográficas. Sua tarefa é comparar duas imagens "
    "aéreas, relatar o progresso físico da construção e estimar visualmente "
    "a porcentagem de avanço de cada tipo de pavimento ou superfície dentro "
    "das áreas demarcadas. Mesmo que a estimativa seja aproximada, forneça "
    "valores percentuais baseados na proporção visual da área coberta."
)

USER_PROMPT = (
    "Compare estas duas imagens aéreas de uma obra de infraestrutura. "
    "A primeira é a referência (situação anterior) e a segunda é a situação "
    "atual. As imagens possuem polígonos coloridos desenhados pelo fiscal "
    "que delimitam as áreas de interesse. Analise EXCLUSIVAMENTE o que está "
    "dentro dessas áreas demarcadas pelos polígonos, ignorando completamente "
    "o restante da imagem. Para cada área demarcada: "
    "1) Identifique os tipos de pavimento/superfície presentes (ex: asfalto, "
    "terra, concreto, base granular, meio-fio, calçada, vegetação, etc.); "
    "2) Estime a porcentagem aproximada de cobertura de cada tipo de "
    "superfície NA IMAGEM DE REFERÊNCIA e NA IMAGEM ATUAL; "
    "3) Calcule a variação percentual (evolução) de cada tipo. "
    "Responda em formato Markdown com: um Resumo Executivo (incluindo o "
    "percentual geral de avanço físico estimado), uma Tabela Comparativa "
    "por área (com colunas: Tipo de Pavimento | % Referência | % Atual | "
    "Variação) e os Principais Avanços detalhados."
)


# ── Funções ───────────────────────────────────────────────────────────────────

def encode_image(path: Path) -> str:
    """Converte imagem para base64 data-URI (image/png)."""
    with open(path, "rb") as f:
        raw = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{raw}"


def analyze_progress(img_ref: Path, img_atual: Path) -> str:
    """
    Envia as duas imagens para o GPT-4o e retorna o relatório
    de avanço físico — mesma lógica do analyzeProgress() do controller JS.
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
                    "image_url": {"url": encode_image(img_ref)},
                },
                {
                    "type": "image_url",
                    "image_url": {"url": encode_image(img_atual)},
                },
            ],
        },
    ]

    print(f"[info] Enviando imagens para {MODEL}...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
    )

    return response.choices[0].message.content


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Valida API key
    if not os.getenv("OPENAI_API_KEY"):
        print("[erro] OPENAI_API_KEY não encontrada no ambiente.")
        sys.exit(1)

    # Valida imagens
    for label, img in [("REFERÊNCIA", IMAGE_REF), ("ATUAL", IMAGE_ATUAL)]:
        if not img.exists():
            print(f"[erro] Imagem {label} não encontrada: {img}")
            sys.exit(1)

    print(f"[info] Imagem REFERÊNCIA: {IMAGE_REF}")
    print(f"[info] Imagem ATUAL     : {IMAGE_ATUAL}")
    print()

    resultado = analyze_progress(IMAGE_REF, IMAGE_ATUAL)

    print("=" * 60)
    print("RELATÓRIO DE AVANÇO FÍSICO")
    print("=" * 60)
    print(resultado)
    print("=" * 60)


if __name__ == "__main__":
    main()
