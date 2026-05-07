import os
import base64
from openai import OpenAI

# Initialize the OpenAI client
# It will automatically look for the OPENAI_API_KEY environment variable.
client = OpenAI()

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_bridge_image(image_path: str) -> str:
    """
    Sends the image to OpenAI Vision API and asks for an analysis of the bridge construction.
    """
    try:
        base64_image = encode_image(image_path)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um auditor de engenharia civil especializado em obras rodoviárias, mais especificamente na construção de pontes."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": '''Analise esta imagem ortomosaica como um inspetor de obras rodoviárias.
Identifique:

* elementos da infraestrutura rodoviária
* equipamentos e máquinas presentes
* estágio da obra
* áreas pavimentadas e não pavimentadas
* possíveis anomalias
* drenagem
* erosão
* sinalização
* acessos temporários
* estruturas incompletas
* indícios de movimentação recente de solo

Para cada item:

* descreva evidências visuais
* indique nível de confiança
* diferencie observação direta de inferência

Evite descrições genéricas.
'''
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return f"Não foi possível analisar a imagem automaticamente: {str(e)}"
