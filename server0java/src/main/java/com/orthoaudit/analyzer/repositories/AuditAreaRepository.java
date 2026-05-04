package com.orthoaudit.analyzer.repositories;

import com.orthoaudit.analyzer.entities.AuditArea;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface AuditAreaRepository extends JpaRepository<AuditArea, Long> {
    List<AuditArea> findByCapturedAt(LocalDate capturedAt);
}
