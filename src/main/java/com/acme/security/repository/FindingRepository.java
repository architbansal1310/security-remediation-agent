package com.acme.security.repository;

import com.acme.security.model.FindingRecord;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class FindingRepository {
    private final List<FindingRecord> findings;

    public FindingRepository(ObjectMapper objectMapper) {
        try (InputStream input = getClass().getResourceAsStream("/mock-findings.json")) {
            if (input == null) {
                throw new IllegalStateException("Sample dataset mock-findings.json is missing");
            }
            findings = List.copyOf(objectMapper.readValue(input, new TypeReference<>() {}));
        } catch (IOException exception) {
            throw new IllegalStateException("Cannot load sample findings", exception);
        }
    }

    public Optional<FindingRecord> findById(String findingId) {
        return findings.stream()
                .filter(finding -> finding.findingId().equalsIgnoreCase(findingId))
                .findFirst();
    }

    public List<FindingRecord> findAll() {
        return findings;
    }
}
