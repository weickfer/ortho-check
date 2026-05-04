package com.orthoaudit.analyzer.entities;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.locationtech.jts.geom.Polygon;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * Entidade responsável por armazenar a Região de Interesse (ROI) 
 * georreferenciada para auditoria.
 */
@Entity
@Table(name = "audit_areas")
@Data
@NoArgsConstructor
public class AuditArea {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String description;

    /**
     * O SRID 4326 define o sistema de coordenadas WGS84, 
     * padrão utilizado pelo GPS e pelo Leaflet.
     */
    @Column(columnDefinition = "geometry(Polygon, 4326)", nullable = false)
    private Polygon geometry;

    /**
     * Armazena o cálculo da área em m² no momento da criação 
     * para facilitar consultas rápidas.
     */
    @Column(name = "area_sq_meters")
    private Double areaSquareMeters;

    @Column(name = "captured_at", nullable = false)
    private LocalDate capturedAt;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
}