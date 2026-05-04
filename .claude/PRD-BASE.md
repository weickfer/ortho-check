# PRD: MVP Ortho-Check (OpenAI Edition)

## 1. Visão Geral
Sistema web minimalista para automatizar a triagem visual de obras de infraestrutura. O usuário faz o upload de duas imagens aéreas ortográficas (referência e atual), e o sistema utiliza o modelo GPT-4o para gerar um laudo textual destacando os avanços físicos no canteiro de obras.

## 2. Escopo Técnico
* **Frontend:** React.js (Vite).
* **Backend:** Node.js (Express) com processamento de upload em memória (Multer).
* **IA:** OpenAI API (Modelo: `gpt-4o`).
* **Objetivo principal:** Reduzir o tempo de análise visual e geração de laudos de fiscalização.

---

## 3. Estrutura do Projeto (Monorepo)

```text
ortho-check/
├── server/                     
│   ├── src/
│   │   ├── controllers/
│   │   │   └── analyze-controller.js
│   │   └── server.js                  
│   ├── .env                           
│   └── package.json                   
│
└── web/                        
    ├── src/
    │   ├── components/
    │   │   └── ortho-analyzer.jsx     
    │   ├── App.jsx                    
    │   └── main.jsx
    ├── index.html
    └── package.json                   
```

---

## 4. Backend (`/server`)


**Arquivo `.env`:**
```env
PORT=3000
OPENAI_API_KEY=sua_chave_aqui
```

### `src/server.js`
```javascript
import express from 'express';
import cors from 'cors';
import multer from 'multer';
import { analyzeProgress } from './controllers/analyze-controller.js';

const app = express();
app.use(cors());
app.use(express.json());

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// Endpoint principal
app.post(
  '/api/analyze-progress', 
  upload.fields([
    { name: 'image-ref', maxCount: 1 }, 
    { name: 'image-current', maxCount: 1 }
  ]), 
  analyzeProgress
);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
```

### `src/controllers/analyze-controller.js`
```javascript
import OpenAI from 'openai';
import dotenv from 'dotenv';

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
          content: "Você é um Engenheiro Civil fiscal de obras. Sua tarefa é comparar duas imagens aéreas e relatar o progresso físico da construção."
        },
        {
          role: "user",
          content: [
            { 
              type: "text", 
              text: "Compare estas duas imagens de uma obra (A primeira é a referência antiga, a segunda é a situação atual). Liste apenas os avanços físicos visíveis em formato Markdown com um Resumo Executivo e os Principais Avanços." 
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
      max_tokens: 1000,
    });

    return res.status(200).json({ report: response.choices[0].message.content });

  } catch (error) {
    console.error('Erro na API da OpenAI:', error);
    return res.status(500).json({ error: 'Falha ao processar análise visual.' });
  }
};
```

---

## 5. Frontend (`/web`)

### `src/components/ortho-analyzer.jsx`
```jsx
import React, { useState } from 'react';

export default function OrthoAnalyzer() {
  const [imageRef, setImageRef] = useState(null);
  const [imageCurrent, setImageCurrent] = useState(null);
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!imageRef || !imageCurrent) {
      alert('Por favor, selecione as duas imagens.');
      return;
    }

    setLoading(true);
    setReport('');

    const formData = new FormData();
    formData.append('image-ref', imageRef);
    formData.append('image-current', imageCurrent);

    try {
      const response = await fetch('http://localhost:3000/api/analyze-progress', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setReport(data.report);
      } else {
        alert(data.error || 'Erro ao analisar imagens.');
      }
    } catch (error) {
      console.error('Erro na requisição:', error);
      alert('Falha na comunicação com o servidor.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px', fontFamily: 'sans-serif' }}>
      <h2>Ortho-Check: Fiscalização Assistida</h2>
      
      <form onSubmit={handleSubmit} style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px' }}>
        <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontWeight: 'bold' }}>Imagem de Referência (Antes):</label> <br /><br />
            <input 
              type="file" 
              accept="image/*" 
              onChange={(e) => setImageRef(e.target.files[0])} 
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontWeight: 'bold' }}>Imagem Atual (Depois):</label> <br /><br />
            <input 
              type="file" 
              accept="image/*" 
              onChange={(e) => setImageCurrent(e.target.files[0])} 
            />
          </div>
        </div>

        <button 
          type="submit" 
          disabled={loading}
          style={{ padding: '10px 20px', cursor: loading ? 'not-allowed' : 'pointer', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          {loading ? 'Analisando Imagens...' : 'Gerar Relatório de Avanço'}
        </button>
      </form>

      {report && (
        <div style={{ marginTop: '30px', padding: '20px', background: '#f8f9fa', border: '1px solid #e9ecef', borderRadius: '8px' }}>
          <h3>Relatório da IA:</h3>
          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', lineHeight: '1.5' }}>
            {report}
          </pre>
        </div>
      )}
    </div>
  );
}
```

### `src/App.jsx`
```jsx
import OrthoAnalyzer from './components/ortho-analyzer';

function App() {
  return (
    <div>
      <OrthoAnalyzer />
    </div>
  )
}

export default App;
```