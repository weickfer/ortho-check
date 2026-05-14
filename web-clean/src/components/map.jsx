import Feature from 'ol/Feature';
import OlMap from 'ol/Map';
import View from 'ol/View';
import WKT from 'ol/format/WKT';
import Draw from 'ol/interaction/Draw';
import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import 'ol/ol.css';
import { fromLonLat } from 'ol/proj';
import { XYZ } from 'ol/source';
import OSM from 'ol/source/OSM';
import VectorSource from 'ol/source/Vector';
import { Fill, Stroke, Style } from 'ol/style';
import { useEffect, useRef, useState } from 'react';
import { createAuditArea, listAuditAreas } from '../services/api';
import { DateSelector } from './DateSelector';

export function Map() {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const vectorSourceRef = useRef(new VectorSource({ wrapX: false }));
  const drawInteractionRef = useRef(null);
  const orthoSourceRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [selectedDate, setSelectedDate] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const date = !!params.get('date') ? new Date(params.get('date')) : new Date()

    return date;
  });
  const formattedDate = selectedDate.toISOString().split("T")[0]

  useEffect(() => {
    if (mapInstanceRef.current) return; // já inicializado

    const vectorLayer = new VectorLayer({
      source: vectorSourceRef.current,
      zIndex: 20,
      style: new Style({
        fill: new Fill({
          color: 'rgba(76, 175, 80, 0.15)' // Verde com opacidade baixa para ver a imagem
        }),
        stroke: new Stroke({
          color: '#4CAF50', // Borda verde bem visível
          width: 3
        })
      })
    });

    const xyz = `http://localhost:8082/tiles/${formattedDate}/{z}/{x}/{y}.png`

    orthoSourceRef.current = new XYZ({
      url: xyz,
      maxZoom: 22,
    });

    mapInstanceRef.current = new OlMap({
      target: mapRef.current,
      layers: [
        // Camada Base: Mapa global de ruas (OpenStreetMap)
        new TileLayer({
          source: new OSM(),
          zIndex: 0,
        }),
        // Camada Sobreposta: Ortomosaico do Drone servido pelo Nginx
        new TileLayer({
          source: orthoSourceRef.current,
          zIndex: 10,
        }),
        vectorLayer, // Camada vetorial para as geometrias (polígonos)
      ],
      view: new View({
        // -3.2844304,-59.8666249
        center: fromLonLat([-59.8666249, -3.2844304]), // Ajuste para a longitude/latitude da sua obra
        zoom: 18,
        maxZoom: 22,
      }),
    });

    return () => {
      mapInstanceRef.current?.setTarget(undefined);
      mapInstanceRef.current = null;
    };
  }, []); // Inicialização executada apenas uma vez

  // Efeito para carregar as geometrias do backend quando a data mudar
  useEffect(() => {
    if (!vectorSourceRef.current) return;

    // Limpar geometrias anteriores
    vectorSourceRef.current.clear();

    listAuditAreas(selectedDate).then((areas) => {
      const format = new WKT();
      areas.forEach((area) => {
        if (area.geometry) {
          const geometry = format.readGeometry(area.geometry, {
            dataProjection: 'EPSG:4326',
            featureProjection: 'EPSG:3857'
          });
          const feature = new Feature({
            geometry,
            description: area.description,
            capturedAt: area.capturedAt
          });
          feature.setId(area.id);
          vectorSourceRef.current.addFeature(feature);
        }
      });
    }).catch(err => console.error("Erro ao carregar áreas:", err));
  }, [selectedDate]);

  // Efeito para atualizar a URL do XYZ e a query string sempre que a data selecionada mudar
  useEffect(() => {
    if (orthoSourceRef.current) {
      orthoSourceRef.current.setUrl(`http://localhost:8082/tiles/${formattedDate}/{z}/{x}/{y}.png`);
    }

    const params = new URLSearchParams(window.location.search);
    if (selectedDate) {
      params.set('date', selectedDate.toISOString().split("T")[0]);
    } else {
      params.delete('date');
    }
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState(null, '', newUrl);
  }, [selectedDate]);

  useEffect(() => {
    if (!mapInstanceRef.current) return;

    if (isDrawing) {
      const draw = new Draw({
        source: vectorSourceRef.current,
        type: 'Polygon',
        style: new Style({
          fill: new Fill({
            color: 'rgba(76, 175, 80, 0.2)'
          }),
          stroke: new Stroke({
            color: '#4CAF50',
            lineDash: [10, 10],
            width: 3
          })
        })
      });

      draw.on('drawend', async (event) => {
        const feature = event.feature;
        const format = new WKT();

        // Converter geometria do mapa (EPSG:3857) para WKT (EPSG:4326)
        const geometry = format.writeGeometry(feature.getGeometry(), {
          dataProjection: 'EPSG:4326',
          featureProjection: 'EPSG:3857'
        });

        setIsDrawing(false); // Desativar desenho

        // Pequeno atraso para permitir o encerramento da interação de desenho na UI antes do prompt
        setTimeout(async () => {
          try {
            const description = window.prompt("Digite uma descrição para a área auditada:") || "Área sem descrição";

            const newArea = await createAuditArea({
              description,
              geometry,
              captured_at: formattedDate
            });

            feature.setId(newArea.id);
            feature.set('description', description);
            feature.set('capturedAt', formattedDate);
          } catch (err) {
            console.error("Erro ao salvar área:", err);
            vectorSourceRef.current.removeFeature(feature);
            window.alert("Falha ao salvar a área.");
          }
        }, 100);
      });

      mapInstanceRef.current.addInteraction(draw);
      drawInteractionRef.current = draw;
    } else {
      if (drawInteractionRef.current) {
        mapInstanceRef.current.removeInteraction(drawInteractionRef.current);
        drawInteractionRef.current = null;
      }
    }
  }, [isDrawing]);

  return (
    <div style={{ position: 'relative', height: '100vh', width: '100vw' }}>
      <div
        ref={mapRef}
        style={{ height: '100%', width: '100%' }}
      />

      {/* Seletor de Data */}
      <DateSelector
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
      />

      {/* Controles de UI sobrepostos ao mapa */}
      <div style={{
        position: 'absolute',
        top: 20,
        right: 20,
        zIndex: 1000,
        background: 'white',
        padding: '10px',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
      }}>
        <button
          onClick={() => setIsDrawing(!isDrawing)}
          style={{
            padding: '10px 20px',
            cursor: 'pointer',
            backgroundColor: isDrawing ? '#f44336' : '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 'bold',
            fontSize: '14px',
            transition: 'background-color 0.2s'
          }}
        >
          {isDrawing ? 'Cancelar Desenho' : '+ Nova Área'}
        </button>
      </div>
    </div>
  );
}