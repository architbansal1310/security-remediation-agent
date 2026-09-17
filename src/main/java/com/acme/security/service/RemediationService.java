package com.acme.security.service;

import com.acme.security.dto.RemediationRequest;
import com.acme.security.dto.RemediationResponse;
import com.acme.security.exception.DuplicateRemediationException;
import com.acme.security.exception.FindingNotFoundException;
import com.acme.security.exception.IneligibleFindingException;
import com.acme.security.model.FindingRecord;
import com.acme.security.repository.FindingRepository;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Service;

@Service
public class RemediationService {
    private static final Set<String> APPROVED_SEVERITIES = Set.of("CRITICAL", "HIGH");

    private final FindingRepository repository;
    private final Set<String> processed = ConcurrentHashMap.newKeySet();

    public RemediationService(FindingRepository repository) {
        this.repository = repository;
    }

    public RemediationResponse approve(RemediationRequest request) {
        FindingRecord finding = repository.findById(request.findingId())
                .orElseThrow(() -> new FindingNotFoundException(
                        "Finding " + request.findingId() + " was not found"));

        if (!finding.repository().equalsIgnoreCase(request.repository())) {
            throw new IneligibleFindingException("Finding does not belong to repository " + request.repository());
        }
        if (!finding.eligible() || !APPROVED_SEVERITIES.contains(finding.severity().toUpperCase(Locale.ROOT))) {
            throw new IneligibleFindingException(
                    "Only eligible Critical and High findings can be remediated automatically");
        }
        if (request.requestedFixedVersion() != null
                && !request.requestedFixedVersion().isBlank()
                && !finding.fixedVersion().equals(request.requestedFixedVersion())) {
            throw new IneligibleFindingException(
                    "Requested fixed version does not match the scanner-approved version " + finding.fixedVersion());
        }

        String idempotencyKey = finding.repository().toLowerCase(Locale.ROOT)
                + ":" + finding.findingId().toLowerCase(Locale.ROOT);
        if (!processed.add(idempotencyKey)) {
            throw new DuplicateRemediationException(
                    "A remediation request already exists for " + finding.findingId());
        }

        return new RemediationResponse(
                UUID.randomUUID().toString(),
                "APPROVED",
                finding.findingId(),
                finding.repository(),
                finding.dependency(),
                finding.severity(),
                finding.currentVersion(),
                finding.fixedVersion(),
                finding.versionOwner(),
                "Eligible finding approved for branch creation, validation, and human-reviewed PR");
    }

    public void clearProcessed() {
        processed.clear();
    }
}
