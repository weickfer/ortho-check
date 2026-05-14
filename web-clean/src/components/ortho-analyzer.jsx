import { useCallback, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ImageEditorModal from './image-editor-modal';

export default function OrthoAnalyzer() {
  const [imageRef, setImageRef] = useState(null);
  const [imageCurrent, setImageCurrent] = useState(null);
  const [previewRef, setPreviewRef] = useState(null);
  const [previewCurrent, setPreviewCurrent] = useState(null);
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(false);
  const [dragOverRef, setDragOverRef] = useState(false);
  const [dragOverCurrent, setDragOverCurrent] = useState(false);

  // Editor modal state (PRD §5.1)
  const [editorConfig, setEditorConfig] = useState({
    isOpen: false,
    fileType: null,     // 'ref' or 'current'
    pendingFile: null,
    previewUrl: null,
  });

  const refInputRef = useRef(null);
  const currentInputRef = useRef(null);

  // Intercepted: opens the editor modal instead of saving directly (PRD §5.2)
  const handleFileSelect = useCallback((file, type) => {
    if (!file) return;

    setEditorConfig({
      isOpen: true,
      fileType: type,
      pendingFile: file,
      previewUrl: URL.createObjectURL(file),
    });
  }, []);

  // Callback from the editor modal after the user saves (PRD §5.4)
  const handleEditorSave = useCallback((editedFile) => {
    const { fileType } = editorConfig;

    if (fileType === 'ref') {
      setImageRef(editedFile);
      setPreviewRef(URL.createObjectURL(editedFile));
    } else if (fileType === 'current') {
      setImageCurrent(editedFile);
      setPreviewCurrent(URL.createObjectURL(editedFile));
    }

    // Close editor & clean up
    if (editorConfig.previewUrl) {
      URL.revokeObjectURL(editorConfig.previewUrl);
    }
    setEditorConfig({ isOpen: false, fileType: null, pendingFile: null, previewUrl: null });
  }, [editorConfig]);

  const handleEditorCancel = useCallback(() => {
    if (editorConfig.previewUrl) {
      URL.revokeObjectURL(editorConfig.previewUrl);
    }
    setEditorConfig({ isOpen: false, fileType: null, pendingFile: null, previewUrl: null });
  }, [editorConfig]);

  const handleDrop = useCallback((e, type) => {
    e.preventDefault();
    setDragOverRef(false);
    setDragOverCurrent(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleFileSelect(file, type);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e, type) => {
    e.preventDefault();
    if (type === 'ref') setDragOverRef(true);
    else setDragOverCurrent(true);
  }, []);

  const handleDragLeave = useCallback((e, type) => {
    e.preventDefault();
    if (type === 'ref') setDragOverRef(false);
    else setDragOverCurrent(false);
  }, []);

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

  const dropzoneClasses = (type) => {
    const base = 'dropzone';
    const isDragOver = type === 'ref' ? dragOverRef : dragOverCurrent;
    const hasFile = type === 'ref' ? imageRef : imageCurrent;
    return `${base}${isDragOver ? ' dropzone--dragover' : ''}${hasFile ? ' dropzone--has-file' : ''}`;
  };

  return (
    <>
      {/* Hero */}
      <section className="hero">
        <h1 className="hero__title">Fiscalização Assistida por IA</h1>
        <p className="hero__subtitle">
          Envie duas imagens ortográficas aéreas e receba um laudo automático
          com os avanços físicos identificados pelo modelo GPT-4o.
        </p>
      </section>

      {/* Upload Form */}
      <form onSubmit={handleSubmit} id="upload-form">
        <div className="upload-card">
          <div className="upload-grid">
            {/* Reference Image */}
            <div
              className={dropzoneClasses('ref')}
              onDrop={(e) => handleDrop(e, 'ref')}
              onDragOver={(e) => handleDragOver(e, 'ref')}
              onDragLeave={(e) => handleDragLeave(e, 'ref')}
              onClick={() => refInputRef.current?.click()}
              id="dropzone-ref"
            >
              <input
                ref={refInputRef}
                type="file"
                accept="image/*"
                onClick={(e) => e.stopPropagation()}
                className="dropzone__input"
                onChange={(e) => handleFileSelect(e.target.files[0], 'ref')}
                aria-label="Selecionar imagem de referência"
                id="input-image-ref"
              />

              {previewRef ? (
                <div className="dropzone__preview">
                  <img src={previewRef} alt="Pré-visualização da imagem de referência" />
                  <div className="dropzone__preview-overlay">
                    <span className="dropzone__preview-name">
                      📷 {imageRef?.name}
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="dropzone__icon">🛰️</div>
                  <span className="dropzone__label">Imagem de Referência</span>
                  <span className="dropzone__hint">Arraste ou clique para selecionar (antes)</span>
                </>
              )}
            </div>

            {/* Current Image */}
            <div
              className={dropzoneClasses('current')}
              onDrop={(e) => handleDrop(e, 'current')}
              onDragOver={(e) => handleDragOver(e, 'current')}
              onDragLeave={(e) => handleDragLeave(e, 'current')}
              onClick={() => currentInputRef.current?.click()}
              id="dropzone-current"
            >
              <input
                ref={currentInputRef}
                type="file"
                accept="image/*"
                className="dropzone__input"
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => handleFileSelect(e.target.files[0], 'current')}
                aria-label="Selecionar imagem atual"
                id="input-image-current"
              />

              {previewCurrent ? (
                <div className="dropzone__preview">
                  <img src={previewCurrent} alt="Pré-visualização da imagem atual" />
                  <div className="dropzone__preview-overlay">
                    <span className="dropzone__preview-name">
                      📷 {imageCurrent?.name}
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="dropzone__icon">📸</div>
                  <span className="dropzone__label">Imagem Atual</span>
                  <span className="dropzone__hint">Arraste ou clique para selecionar (depois)</span>
                </>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !imageRef || !imageCurrent}
            className="submit-btn"
            id="submit-analysis"
          >
            <span className="submit-btn__content">
              {loading ? (
                <>
                  <span className="spinner" />
                  Analisando Imagens…
                </>
              ) : (
                <>
                  🔍 Gerar Relatório de Avanço
                </>
              )}
            </span>
          </button>
        </div>
      </form>

      {/* Loading State */}
      {loading && (
        <div className="report-section">
          <div className="report-card">
            <div className="loading-overlay">
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <p className="loading-text">
                O modelo GPT-4o está analisando as imagens…<br />
                Isso pode levar alguns segundos.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Report */}
      {report && !loading && (
        <section className="report-section" id="report-section">
          <div className="report-header">
            <div className="report-header__icon">📋</div>
            <h2 className="report-header__title">Relatório de Avanço</h2>
          </div>
          <div className="report-card">
            <div className="report-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
            </div>
          </div>
        </section>
      )}

      {/* Image Editor Modal */}
      {editorConfig.isOpen && (
        <ImageEditorModal
          imageUrl={editorConfig.previewUrl}
          onSave={handleEditorSave}
          onCancel={handleEditorCancel}
        />
      )}
    </>
  );
}
