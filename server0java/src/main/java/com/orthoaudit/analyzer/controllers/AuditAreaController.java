package com.orthoaudit.analyzer.controllers;

import com.orthoaudit.analyzer.dto.AuditAreaResponse;
import com.orthoaudit.analyzer.dto.CreateAuditAreaRequest;
import com.orthoaudit.analyzer.services.AuditAreaService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.time.LocalDate;

@RestController
@RequestMapping("/api/audit-areas")
@RequiredArgsConstructor
public class AuditAreaController {

    private final AuditAreaService auditAreaService;

    /**
     * POST /api/audit-areas
     * Registra uma nova área de auditoria.
     */
    @PostMapping
    public ResponseEntity<AuditAreaResponse> create(@RequestBody CreateAuditAreaRequest request) {
        AuditAreaResponse response = auditAreaService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * GET /api/audit-areas
     * Lista todas as áreas de auditoria cadastradas.
     */
    @GetMapping
    public ResponseEntity<List<AuditAreaResponse>> findAll(
            @RequestParam(required = false) LocalDate capturedAt) {
        if (capturedAt != null) {
            return ResponseEntity.ok(auditAreaService.findByCapturedAt(capturedAt));
        }
        return ResponseEntity.ok(auditAreaService.findAll());
    }

    /**
     * GET /api/audit-areas/{id}
     * Busca uma área de auditoria pelo ID.
     */
    @GetMapping("/{id}")
    public ResponseEntity<AuditAreaResponse> findById(@PathVariable Long id) {
        return ResponseEntity.ok(auditAreaService.findById(id));
    }
}
