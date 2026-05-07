"""
Experimento: Comparação de avanço físico entre duas imagens ortomosaicas.

Uso:
    python comparar_avanco.py

Pré-requisitos:
    - OPENAI_API_KEY definida no ambiente (ou no .env do projeto)
    - Imagens em /data/01.png e /data/02.png  (ou ajuste DATA_DIR abaixo)
    - pip install openai python-dotenv
"""

import os
import base64
import sys
from pathlib import Path

# ── Carrega .env se existir (opcional — no container o env_file do compose já injeta) ──
try:
    from dotenv import load_dotenv
    load_dotenv()  # carrega .env do diretório atual, se houver
except ImportError:
    pass

from openai import OpenAI

# ── Configurações ─────────────────────────────────────────────────────────────
DATA_DIR = Path("/data")          # caminho das imagens dentro do container
IMAGE_ANTES  = DATA_DIR / "01.png"
IMAGE_DEPOIS = DATA_DIR / "02.png"

MODEL = "gpt-4o"
MAX_TOKENS = 1500

SYSTEM_PROMPT = (
    "Você é um auditor sênior de obras rodoviárias do DNIT, especializado em "
    "análise de imagens ortomosaicas obtidas por drones. "
    "Sua função é comparar duas imagens de uma mesma área de obra em momentos "
    "distintos e identificar com precisão o que avançou fisicamente.\n\n"
    "CONTEXTO DE TESTE: As imagens que você vai receber contêm QUADRADOS AMARELOS "
    "desenhados sobre a foto original. Esses quadrados amarelos simulam elementos "
    "de obra (estruturas, pavimentação, etc.) para fins de teste. "
    "Trate cada quadrado amarelo como se fosse um elemento real da obra. "
    "Se na imagem DEPOIS houver quadrados novos ou maiores em relação à imagem ANTES, "
    "isso representa avanço físico da obra."
)

USER_PROMPT = """\
⚠️ CENÁRIO DE TESTE — Os quadrados amarelos nas imagens representam elementos de obra.

Você recebeu DUAS imagens da mesma área:

• Imagem 1 (ANTES) — primeira imagem enviada
• Imagem 2 (DEPOIS) — segunda imagem enviada

Compare as duas imagens focando nos QUADRADOS AMARELOS como indicadores de avanço.
Responda em português com a seguinte estrutura:

## 1. Avanços físicos identificados
Para cada quadrado amarelo novo ou que mudou de tamanho/posição entre ANTES e DEPOIS:
- Localização aproximada na imagem (ex: canto superior esquerdo, centro, etc.)
- O que mudou (apareceu, cresceu, moveu, etc.)
- Nível de confiança: [ALTO | MÉDIO | BAIXO]

## 2. Estimativa de avanço geral (%)
Estime o percentual de avanço com base na quantidade/tamanho dos quadrados amarelos
que apareceram ou cresceram na imagem DEPOIS em relação à ANTES.
Formato: X% — Justificativa: ...

## 3. Elementos sem alteração aparente
Quadrados ou áreas que permaneceram iguais entre as duas imagens.

## 4. Observações adicionais
Qualquer outra diferença visual relevante entre as duas imagens.

Seja direto e objetivo.
"""

# ── Funções ───────────────────────────────────────────────────────────────────

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
    """Envia as duas imagens para o GPT-4o e retorna a análise de avanço."""
    client = OpenAI()  # usa OPENAI_API_KEY do ambiente

    content = (
        [{"type": "text", "text": USER_PROMPT}]
        + build_image_content(img_antes,  "Imagem 1 — ANTES")
        + build_image_content(img_depois, "Imagem 2 — DEPOIS")
    )

    print(f"[info] Enviando imagens para {MODEL}...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": content},
        ],
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
    for img in (IMAGE_ANTES, IMAGE_DEPOIS):
        if not img.exists():
            print(f"[erro] Imagem não encontrada: {img}")
            sys.exit(1)

    print(f"[info] Imagem ANTES : {IMAGE_ANTES}")
    print(f"[info] Imagem DEPOIS: {IMAGE_DEPOIS}")
    print()

    resultado = comparar_avanco(IMAGE_ANTES, IMAGE_DEPOIS)

    print("=" * 60)
    print("ANÁLISE DE AVANÇO FÍSICO")
    print("=" * 60)
    print(resultado)
    print("=" * 60)


if __name__ == "__main__":
    main()
