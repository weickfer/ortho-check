package com.orthoaudit.analyzer.services;

import com.orthoaudit.analyzer.dto.AuditAreaResponse;
import com.orthoaudit.analyzer.dto.CreateAuditAreaRequest;
import com.orthoaudit.analyzer.entities.AuditArea;
import com.orthoaudit.analyzer.repositories.AuditAreaRepository;
import lombok.RequiredArgsConstructor;
import org.locationtech.jts.geom.Polygon;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.locationtech.jts.io.WKTReader;
import org.locationtech.jts.io.WKTWriter;

import java.util.List;
import java.time.LocalDate;

@Service
@RequiredArgsConstructor
public class AuditAreaService {

    private final AuditAreaRepository repository;

    /**
     * Registra uma nova área de auditoria.
     * Garante SRID 4326 e calcula a área aproximada em m².
     */
    @Transactional
    public AuditAreaResponse create(CreateAuditAreaRequest request) {
        if (request.getCapturedAt() == null) {
            throw new IllegalArgumentException("A data de captura (capturedAt) é obrigatória.");
        }

        Polygon polygon;
        try {
            polygon = (Polygon) new WKTReader().read(request.getGeometry());
        } catch (Exception e) {
            throw new RuntimeException("Geometria WKT inválida", e);
        }

        // Garante que o SRID seja 4326 (WGS84)
        if (polygon.getSRID() == 0) {
            polygon.setSRID(4326);
        }

        AuditArea entity = new AuditArea();
        entity.setDescription(request.getDescription());
        entity.setGeometry(polygon);
        entity.setCapturedAt(request.getCapturedAt());
        entity.setAreaSquareMeters(calculateApproxAreaInSquareMeters(polygon));

        AuditArea saved = repository.save(entity);
        return toResponse(saved);
    }

    /**
     * Lista todas as áreas de auditoria cadastradas.
     */
    @Transactional(readOnly = true)
    public List<AuditAreaResponse> findAll() {
        return repository.findAll()
                .stream()
                .map(this::toResponse)
                .toList();
    }

    /**
     * Lista áreas de auditoria por data de captura.
     */
    @Transactional(readOnly = true)
    public List<AuditAreaResponse> findByCapturedAt(LocalDate capturedAt) {
        return repository.findByCapturedAt(capturedAt)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    /**
     * Busca uma área de auditoria pelo ID.
     */
    @Transactional(readOnly = true)
    public AuditAreaResponse findById(Long id) {
        AuditArea entity = repository.findById(id)
                .orElseThrow(() -> new RuntimeException("AuditArea não encontrada com id: " + id));
        return toResponse(entity);
    }

    // ── helpers ──────────────────────────────────────────────

    private AuditAreaResponse toResponse(AuditArea entity) {
        return AuditAreaResponse.builder()
                .id(entity.getId())
                .description(entity.getDescription())
                .geometry(new WKTWriter().write(entity.getGeometry()))
                .capturedAt(entity.getCapturedAt())
                .areaSquareMeters(entity.getAreaSquareMeters())
                .createdAt(entity.getCreatedAt())
                .build();
    }

    /**
     * Cálculo aproximado da área em m² usando a fórmula simplificada
     * baseada no centróide do polígono (graus → metros).
     * Para polígonos pequenos a média-escala, a precisão é aceitável.
     */
    private double calculateApproxAreaInSquareMeters(Polygon polygon) {
        double centroidLat = polygon.getCentroid().getY();
        double latRadians = Math.toRadians(centroidLat);

        // Comprimento de 1 grau em metros na latitude do centróide
        double metersPerDegreeLat = 111_132.92;
        double metersPerDegreeLon = 111_132.92 * Math.cos(latRadians);

        // Área do polígono em graus²
        double areaDegrees = polygon.getArea();

        return areaDegrees * metersPerDegreeLat * metersPerDegreeLon;
    }
}
