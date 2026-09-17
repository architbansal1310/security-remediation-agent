package com.acme.security.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.acme.security.dto.RemediationRequest;
import com.acme.security.exception.DuplicateRemediationException;
import com.acme.security.exception.FindingNotFoundException;
import com.acme.security.exception.IneligibleFindingException;
import com.acme.security.model.FindingRecord;
import com.acme.security.repository.FindingRepository;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class RemediationServiceTest {
    private FindingRepository repository;
    private RemediationService service;

    @BeforeEach
    void setUp() {
        repository = mock(FindingRepository.class);
        service = new RemediationService(repository);
    }

    @Test
    void approvesEligibleCriticalFinding() {
        when(repository.findById("CVE-1")).thenReturn(Optional.of(finding("CRITICAL", true)));

        var response = service.approve(new RemediationRequest(
                "CVE-1", "vulnerable-java-platform", "2.17.1"));

        assertThat(response.status()).isEqualTo("APPROVED");
        assertThat(response.fixedVersion()).isEqualTo("2.17.1");
        assertThat(response.versionOwner()).isEqualTo("parent");
        assertThat(response.requestId()).isNotBlank();
    }

    @Test
    void rejectsDuplicateFindingForSameRepository() {
        when(repository.findById("CVE-1")).thenReturn(Optional.of(finding("HIGH", true)));
        var request = new RemediationRequest("CVE-1", "vulnerable-java-platform", "2.17.1");
        service.approve(request);

        assertThatThrownBy(() -> service.approve(request))
                .isInstanceOf(DuplicateRemediationException.class)
                .hasMessageContaining("already exists");
    }

    @Test
    void rejectsIneligibleSeverity() {
        when(repository.findById("CVE-1")).thenReturn(Optional.of(finding("MEDIUM", false)));

        assertThatThrownBy(() -> service.approve(
                new RemediationRequest("CVE-1", "vulnerable-java-platform", "2.17.1")))
                .isInstanceOf(IneligibleFindingException.class)
                .hasMessageContaining("Critical and High");
    }

    @Test
    void rejectsRepositoryMismatch() {
        when(repository.findById("CVE-1")).thenReturn(Optional.of(finding("HIGH", true)));

        assertThatThrownBy(() -> service.approve(
                new RemediationRequest("CVE-1", "another-repository", "2.17.1")))
                .isInstanceOf(IneligibleFindingException.class)
                .hasMessageContaining("does not belong");
    }

    @Test
    void rejectsUnapprovedFixedVersion() {
        when(repository.findById("CVE-1")).thenReturn(Optional.of(finding("HIGH", true)));

        assertThatThrownBy(() -> service.approve(
                new RemediationRequest("CVE-1", "vulnerable-java-platform", "9.9.9")))
                .isInstanceOf(IneligibleFindingException.class)
                .hasMessageContaining("scanner-approved");
    }

    @Test
    void rejectsUnknownFinding() {
        when(repository.findById("UNKNOWN")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.approve(
                new RemediationRequest("UNKNOWN", "vulnerable-java-platform", "")))
                .isInstanceOf(FindingNotFoundException.class);
    }

    @Test
    void clearProcessedAllowsControlledRetry() {
        when(repository.findById("CVE-1")).thenReturn(Optional.of(finding("HIGH", true)));
        var request = new RemediationRequest("CVE-1", "vulnerable-java-platform", "");
        service.approve(request);
        service.clearProcessed();
        assertThat(service.approve(request).status()).isEqualTo("APPROVED");
    }

    private FindingRecord finding(String severity, boolean eligible) {
        return new FindingRecord("CVE-1", "NEXUS", severity,
                "vulnerable-java-platform", "orders-api",
                "org.apache.logging.log4j:log4j-core", "2.14.1", "2.17.1",
                "parent", eligible);
    }
}
