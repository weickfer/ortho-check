# Product Requirements Document (PRD)
## Módulo: Editor de Imagem com Three.js (Polygon Draw)

### 1. Visão Geral
O objetivo é interceptar o fluxo atual de upload de imagens da aplicação `OrthoAnalyzer`. Antes que a imagem selecionada (seja de referência ou atual) seja anexada ao estado final e enviada para a API, o usuário deverá passar por um modal contendo um editor 2D construído em Three.js. Neste editor, o usuário poderá desenhar polígonos para destacar áreas específicas de interesse (como avanços físicos na obra). Após a conclusão do desenho, um "screenshot" do canvas do Three.js será capturado e salvo como o arquivo final no estado do React.

### 2. Fluxo da Aplicação (Current vs. New)

**Fluxo Atual:**
1. Usuário faz drop/clica e seleciona o arquivo.
2. O arquivo vai direto para os estados `imageRef` ou `imageCurrent` (e gera o preview).
3. Usuário clica em "Gerar Relatório" -> Envio para API.

**Novo Fluxo:**
1. Usuário faz drop/clica e seleciona o arquivo.
2. O arquivo é salvo em um estado temporário (`pendingFile`) e abre o Modal do Editor Three.js.
3. A imagem carrega como uma textura de fundo no plano do Three.js.
4. Usuário clica no canvas criando vértices de um polígono.
5. Ao concluir o polígono e clicar em "Confirmar", a aplicação extrai um Blob/Base64 do canvas.
6. Esse novo arquivo editado é salvo em `imageRef` ou `imageCurrent`.
7. O Modal fecha e o fluxo de envio para a API segue normalmente.

### 3. Requisitos Funcionais

* **Renderização Base:** O componente deve iniciar um `WebGLRenderer` com `preserveDrawingBuffer: true` (crucial para conseguir extrair a imagem depois sem tela preta).
* **Câmera:** Utilizar `THREE.OrthographicCamera` ajustada à proporção (aspect ratio) da imagem carregada para evitar distorções.
* **Textura de Fundo:** A imagem original deve ser carregada via `THREE.TextureLoader` e aplicada a um `THREE.PlaneGeometry` que cubra a visão da câmera.
* **Desenho de Polígonos:**
    * Clique simples (`mousedown`/`pointerdown`): Adiciona um vértice.
    * Movimento (`mousemove`): Desenha uma linha guia entre o último vértice e o cursor do mouse.
    * Fechamento: Duplo clique ou clique em um botão "Fechar Polígono" para conectar o último vértice ao primeiro.
* **Exportação de Imagem:** A ação de confirmação deve acionar o método `.toBlob()` no elemento `<canvas>` gerado pelo Three.js, convertendo a cena renderizada em um objeto `File` que substituirá a imagem original.
* **Gerenciamento de Estado:** Controles de UI para "Desfazer último ponto", "Limpar tudo", "Cancelar" e "Salvar".

### 4. Requisitos Não Funcionais

* **Desempenho/Memory Leaks:** O componente do editor deve garantir o descarte correto da cena (`scene.dispose()`, `material.dispose()`, `geometry.dispose()`, `renderer.dispose()`) no evento de unmount (`useEffect` cleanup) para evitar vazamento de memória, muito comum ao abrir e fechar modais no React com Three.js.
* **Responsividade:** O canvas do editor deve se ajustar ao tamanho da tela (modal), recalculando os frustums da câmera ortográfica no evento de `resize`.

### 5. Modificações Necessárias na Arquitetura Atual

Para integrar o editor ao código fornecido, as seguintes alterações de arquitetura devem ser implementadas no arquivo base:

#### 5.1. Novos Estados
Você precisará de estados para controlar o modal e a imagem pendente:
```javascript
const [editorConfig, setEditorConfig] = useState({
  isOpen: false,
  fileType: null, // 'ref' ou 'current'
  pendingFile: null, // O arquivo original recém upado
  previewUrl: null // URL.createObjectURL para carregar no texture loader
});
```

#### 5.2. Interceptação do `handleFileSelect`
O `handleFileSelect` não salvará mais direto no state principal. Ele abrirá o modal:
```javascript
const handleFileSelect = useCallback((file, type) => {
  if (!file) return;
  
  // Em vez de salvar em setImageRef/setImageCurrent, abre o editor:
  setEditorConfig({
    isOpen: true,
    fileType: type,
    pendingFile: file,
    previewUrl: URL.createObjectURL(file)
  });
}, []);
```

#### 5.3. Novo Componente: `image-editor-modal` (Sugestão de kebab-case)
Criação de um novo arquivo `image-editor-modal.jsx` que conterá a lógica do Three.js. Ele receberá props como:
* `imageUrl` (a textura de fundo)
* `onSave` (função que recebe o novo Blob/File finalizado)
* `onCancel` (função para fechar o modal limpando a fila)

#### 5.4. Callback de Salvamento do Editor
Adicionar a função que lidará com a resposta do modal no seu componente principal:
```javascript
const handleEditorSave = (editedFile) => {
  const { fileType } = editorConfig;
  
  if (fileType === 'ref') {
    setImageRef(editedFile);
    setPreviewRef(URL.createObjectURL(editedFile));
  } else if (fileType === 'current') {
    setImageCurrent(editedFile);
    setPreviewCurrent(URL.createObjectURL(editedFile));
  }
  
  // Fecha o editor
  setEditorConfig({ isOpen: false, fileType: null, pendingFile: null, previewUrl: null });
};
```

### 6. Estratégia Técnica no Three.js (Dica de Implementação)

Como você já tem experiência com a abordagem 2D no Three.js, aqui estão os pontos de atenção para essa integração específica com o React:

1.  **Raycaster:** Para mapear os cliques do mouse para a coordenada 2D da câmera ortográfica, o cálculo do vetor do mouse deve ser normalizado de -1 a +1 baseado no tamanho do `<canvas>`, não na janela (`window`), já que ele estará dentro de um Modal.
2.  **Linhas Dinâmicas:** Use `THREE.Line` ou `THREE.LineLoop` combinados com uma `THREE.BufferGeometry` para atualizar os vértices do polígono dinamicamente no clique. O array de posições da geometria precisa ter sua flag `needsUpdate = true` setada a cada clique.
3.  **Captura da Imagem:**
    ```javascript
    renderer.render(scene, camera); // Força um render final
    canvasRef.current.toBlob((blob) => {
      const file = new File([blob], "edited-ortho.jpg", { type: "image/jpeg" });
      onSave(file);
    }, 'image/jpeg', 0.9);
    ```