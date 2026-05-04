import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import * as THREE from 'three';

/* =============================================
   Sub-components rendered INSIDE the R3F Canvas
   ============================================= */

/** Background plane — loads image and sizes the plane to its real aspect ratio */
function BackgroundPlane({ imageUrl, onImageLoaded }) {
  const { viewport } = useThree();
  const [imageDims, setImageDims] = useState(null);

  // Load image to get natural dimensions
  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      setImageDims({ w: img.naturalWidth, h: img.naturalHeight });
      onImageLoaded?.({ w: img.naturalWidth, h: img.naturalHeight });
    };
    img.src = imageUrl;
  }, [imageUrl, onImageLoaded]);

  const texture = useMemo(() => {
    const tex = new THREE.TextureLoader().load(imageUrl);
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
  }, [imageUrl]);

  // Calculate plane size to "contain" image inside viewport
  const planeSize = useMemo(() => {
    if (!imageDims) return { w: viewport.width, h: viewport.height };

    const imgAspect = imageDims.w / imageDims.h;
    const vpAspect = viewport.width / viewport.height;

    if (imgAspect > vpAspect) {
      // image is wider → fit to width
      return { w: viewport.width, h: viewport.width / imgAspect };
    } else {
      // image is taller → fit to height
      return { w: viewport.height * imgAspect, h: viewport.height };
    }
  }, [imageDims, viewport]);

  return (
    <mesh position={[0, 0, -0.1]}>
      <planeGeometry args={[planeSize.w, planeSize.h]} />
      <meshBasicMaterial map={texture} toneMapped={false} />
    </mesh>
  );
}

/** Handles camera resize to keep ortho frustum matching the viewport */
function CameraController() {
  const { camera, size } = useThree();

  useEffect(() => {
    const half_w = size.width / 2;
    const half_h = size.height / 2;
    camera.left = -half_w;
    camera.right = half_w;
    camera.top = half_h;
    camera.bottom = -half_h;
    camera.near = 0.1;
    camera.far = 100;
    camera.position.set(0, 0, 5);
    camera.updateProjectionMatrix();
  }, [camera, size]);

  return null;
}

/** A single thick line segment rendered as a rotated quad mesh */
function ThickSegment({ from, to, thickness, color, zIndex = 0.02 }) {
  const dx = to[0] - from[0];
  const dy = to[1] - from[1];
  const length = Math.sqrt(dx * dx + dy * dy);
  const angle = Math.atan2(dy, dx);
  const cx = (from[0] + to[0]) / 2;
  const cy = (from[1] + to[1]) / 2;

  if (length < 0.001) return null;

  return (
    <mesh position={[cx, cy, zIndex]} rotation={[0, 0, angle]}>
      <planeGeometry args={[length, thickness]} />
      <meshBasicMaterial color={color} />
    </mesh>
  );
}

/** Renders a polyline as a series of thick quads */
function ThickPolyline({ points, thickness, color, closed, zIndex }) {
  const segments = [];
  for (let i = 0; i < points.length - 1; i++) {
    segments.push(
      <ThickSegment
        key={`seg-${i}`}
        from={points[i]}
        to={points[i + 1]}
        thickness={thickness}
        color={color}
        zIndex={zIndex}
      />
    );
  }
  if (closed && points.length > 2) {
    segments.push(
      <ThickSegment
        key="seg-close"
        from={points[points.length - 1]}
        to={points[0]}
        thickness={thickness}
        color={color}
        zIndex={zIndex}
      />
    );
  }
  return <>{segments}</>;
}

/** The interactive polygon drawing layer */
function PolygonDrawer({
  vertices,
  setVertices,
  closedPolygons,
  setClosedPolygons,
  guideLine,
  setGuideLine,
}) {
  const { camera, gl } = useThree();

  // Threshold in world units — how close you need to click to the first vertex to close
  const CLOSE_THRESHOLD = 12;

  // Convert screen coords to world coords (ortho)
  const screenToWorld = useCallback((clientX, clientY) => {
    const rect = gl.domElement.getBoundingClientRect();
    const ndcX = ((clientX - rect.left) / rect.width) * 2 - 1;
    const ndcY = -((clientY - rect.top) / rect.height) * 2 + 1;

    const vec = new THREE.Vector3(ndcX, ndcY, 0);
    vec.unproject(camera);
    return [vec.x, vec.y];
  }, [camera, gl]);

  const dist = (a, b) => Math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2);

  // Click handler: add vertex OR close polygon if clicking near the first vertex
  useEffect(() => {
    const canvas = gl.domElement;

    const handlePointerDown = (e) => {
      if (e.button !== 0) return;
      const [wx, wy] = screenToWorld(e.clientX, e.clientY);

      setVertices(prev => {
        // If we have 3+ vertices, check if click is near the first one
        if (prev.length >= 3) {
          const d = dist([wx, wy], prev[0]);
          if (d < CLOSE_THRESHOLD) {
            // Close the polygon
            setClosedPolygons(cp => [...cp, [...prev]]);
            setGuideLine(null);
            return []; // reset current vertices
          }
        }
        return [...prev, [wx, wy]];
      });
    };

    const handlePointerMove = (e) => {
      const [wx, wy] = screenToWorld(e.clientX, e.clientY);
      setGuideLine([wx, wy]);
    };

    canvas.addEventListener('pointerdown', handlePointerDown);
    canvas.addEventListener('pointermove', handlePointerMove);
    return () => {
      canvas.removeEventListener('pointerdown', handlePointerDown);
      canvas.removeEventListener('pointermove', handlePointerMove);
    };
  }, [gl, screenToWorld, setVertices, setClosedPolygons, setGuideLine]);

  // Build guide-line points for active polygon
  const activePoints = useMemo(() => {
    if (vertices.length === 0) return [];
    const pts = [...vertices];
    if (guideLine) pts.push(guideLine);
    return pts;
  }, [vertices, guideLine]);

  // Vertex marker size
  const MARKER_RADIUS = 6;
  const FIRST_MARKER_RADIUS = 9;

  return (
    <>
      {/* Closed polygons */}
      {closedPolygons.map((poly, pi) => {
        const shape = new THREE.Shape();
        shape.moveTo(poly[0][0], poly[0][1]);
        for (let i = 1; i < poly.length; i++) {
          shape.lineTo(poly[i][0], poly[i][1]);
        }
        shape.closePath();

        return (
          <group key={`poly-${pi}`}>
            {/* Fill */}
            <mesh position={[0, 0, 0.005]}>
              <shapeGeometry args={[shape]} />
              <meshBasicMaterial color="#6366f1" transparent opacity={0.18} />
            </mesh>
            {/* Outline — thick */}
            <ThickPolyline
              points={poly}
              thickness={3}
              color="#a78bfa"
              closed
              zIndex={0.01}
            />
          </group>
        );
      })}

      {/* Active polyline (in-progress) — thick */}
      {activePoints.length >= 2 && (
        <ThickPolyline
          points={activePoints}
          thickness={3}
          color="#f59e0b"
          closed={false}
          zIndex={0.02}
        />
      )}

      {/* Vertex markers */}
      {vertices.map(([x, y], i) => (
        <mesh key={`v-${i}`} position={[x, y, 0.03]}>
          <circleGeometry args={[i === 0 ? FIRST_MARKER_RADIUS : MARKER_RADIUS, 20]} />
          <meshBasicMaterial color={i === 0 ? '#22c55e' : '#6366f1'} />
        </mesh>
      ))}
    </>
  );
}

/* =============================================
   Main export: the modal wrapper
   ============================================= */

export default function ImageEditorModal({ imageUrl, onSave, onCancel }) {
  const canvasWrapperRef = useRef(null);
  const glRef = useRef(null);

  // Polygon state
  const [vertices, setVertices] = useState([]);
  const [closedPolygons, setClosedPolygons] = useState([]);
  const [guideLine, setGuideLine] = useState(null);

  // ---- Actions ----
  const handleUndo = useCallback(() => {
    setVertices(prev => prev.slice(0, -1));
  }, []);

  const handleClearAll = useCallback(() => {
    setVertices([]);
    setClosedPolygons([]);
    setGuideLine(null);
  }, []);

  const handleSave = useCallback(() => {
    if (!glRef.current) return;

    const renderer = glRef.current;
    const canvas = renderer.domElement;

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], 'edited-ortho.jpg', { type: 'image/jpeg' });
        onSave(file);
      }
    }, 'image/jpeg', 0.92);
  }, [onSave]);

  // Close on ESC key
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onCancel]);

  return (
    <div className="editor-modal-backdrop" id="editor-modal">
      <div className="editor-modal">
        {/* Header */}
        <div className="editor-modal__header">
          <div className="editor-modal__title-group">
            <div className="editor-modal__icon">✏️</div>
            <h2 className="editor-modal__title">Editor de Marcação</h2>
          </div>
          <p className="editor-modal__hint">
            Clique para adicionar pontos · Clique no ponto verde para fechar o polígono · ESC para cancelar
          </p>
        </div>

        {/* Canvas */}
        <div className="editor-modal__canvas-wrapper" ref={canvasWrapperRef}>
          <Canvas
            orthographic
            camera={{ position: [0, 0, 5], near: 0.1, far: 100 }}
            gl={{ preserveDrawingBuffer: true, antialias: true }}
            onCreated={({ gl }) => { glRef.current = gl; }}
            style={{ cursor: 'crosshair' }}
          >
            <CameraController />
            <BackgroundPlane imageUrl={imageUrl} />
            <PolygonDrawer
              vertices={vertices}
              setVertices={setVertices}
              closedPolygons={closedPolygons}
              setClosedPolygons={setClosedPolygons}
              guideLine={guideLine}
              setGuideLine={setGuideLine}
            />
          </Canvas>
        </div>

        {/* Toolbar */}
        <div className="editor-modal__toolbar">
          <div className="editor-modal__toolbar-left">
            <button
              type="button"
              className="editor-btn editor-btn--ghost"
              onClick={handleUndo}
              disabled={vertices.length === 0}
              title="Desfazer último ponto"
              id="btn-undo"
            >
              ↩ Desfazer
            </button>
            <button
              type="button"
              className="editor-btn editor-btn--ghost"
              onClick={handleClearAll}
              disabled={vertices.length === 0 && closedPolygons.length === 0}
              title="Limpar tudo"
              id="btn-clear"
            >
              🗑 Limpar
            </button>
          </div>

          <div className="editor-modal__toolbar-right">
            <button
              type="button"
              className="editor-btn editor-btn--cancel"
              onClick={onCancel}
              id="btn-cancel-editor"
            >
              Cancelar
            </button>
            <button
              type="button"
              className="editor-btn editor-btn--primary"
              onClick={handleSave}
              id="btn-save-editor"
            >
              ✅ Salvar Imagem
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
