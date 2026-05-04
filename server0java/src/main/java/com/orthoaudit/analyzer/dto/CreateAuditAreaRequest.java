package com.orthoaudit.analyzer.dto;

import lombok.Data;
import java.time.LocalDate;

/**
 * DTO de entrada para criação de uma AuditArea.
 * Espera receber uma string WKT no campo "geometry".
 */
@Data
public class CreateAuditAreaRequest {

    private String description;
    private String geometry;
    private LocalDate capturedAt;
}
