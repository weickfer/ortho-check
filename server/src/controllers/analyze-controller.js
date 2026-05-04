import dotenv from 'dotenv';
import OpenAI from 'openai';

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export const analyzeProgress = async (req, res) => {
  try {
    const files = req.files;
    if (!files || !files['image-ref'] || !files['image-current']) {
      return res.status(400).json({ error: 'As duas imagens são obrigatórias.' });
    }

    const imageRef = files['image-ref'][0];
    const imageCurrent = files['image-current'][0];

    const base64Ref = `data:${imageRef.mimetype};base64,${imageRef.buffer.toString('base64')}`;
    const base64Current = `data:${imageCurrent.mimetype};base64,${imageCurrent.buffer.toString('base64')}`;

    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content: "Você é um Engenheiro Civil fiscal de obras especializado em análise de imagens aéreas ortográficas. Sua tarefa é comparar duas imagens aéreas, relatar o progresso físico da construção e estimar visualmente a porcentagem de avanço de cada tipo de pavimento ou superfície dentro das áreas demarcadas. Mesmo que a estimativa seja aproximada, forneça valores percentuais baseados na proporção visual da área coberta."
        },
        {
          role: "user",
          content: [
            {
              type: "text",
              text: "Compare estas duas imagens aéreas de uma obra de infraestrutura. A primeira é a referência (situação anterior) e a segunda é a situação atual. As imagens possuem polígonos coloridos desenhados pelo fiscal que delimitam as áreas de interesse. Analise EXCLUSIVAMENTE o que está dentro dessas áreas demarcadas pelos polígonos, ignorando completamente o restante da imagem. Para cada área demarcada: 1) Identifique os tipos de pavimento/superfície presentes (ex: asfalto, terra, concreto, base granular, meio-fio, calçada, vegetação, etc.); 2) Estime a porcentagem aproximada de cobertura de cada tipo de superfície NA IMAGEM DE REFERÊNCIA e NA IMAGEM ATUAL; 3) Calcule a variação percentual (evolução) de cada tipo. Responda em formato Markdown com: um Resumo Executivo (incluindo o percentual geral de avanço físico estimado), uma Tabela Comparativa por área (com colunas: Tipo de Pavimento | % Referência | % Atual | Variação) e os Principais Avanços detalhados."
            },
            {
              type: "image_url",
              image_url: { "url": base64Ref }
            },
            {
              type: "image_url",
              image_url: { "url": base64Current }
            },
          ],
        },
      ],
      max_tokens: 2000,
    });

    return res.status(200).json({ report: response.choices[0].message.content });

  } catch (error) {
    console.error('Erro na API da OpenAI:', error);
    return res.status(500).json({ error: 'Falha ao processar análise visual.' });
  }
};
