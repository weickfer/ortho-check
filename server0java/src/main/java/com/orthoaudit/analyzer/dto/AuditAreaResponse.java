package com.orthoaudit.analyzer.dto;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * DTO de saída que representa uma AuditArea persistida.
 */
@Data
@Builder
public class AuditAreaResponse {

    private Long id;
    private String description;
    private String geometry;
    private Double areaSquareMeters;
    private LocalDate capturedAt;
    private LocalDateTime createdAt;
}
