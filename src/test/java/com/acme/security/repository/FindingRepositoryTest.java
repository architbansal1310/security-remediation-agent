package com.acme.security.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

class FindingRepositoryTest {
    private final FindingRepository repository = new FindingRepository(new ObjectMapper());

    @Test
    void loadsTwentySampleFindings() {
        assertThat(repository.findAll()).hasSize(20);
        assertThat(repository.findById("cve-2021-44228")).isPresent();
    }

    @Test
    void returnsEmptyForUnknownFinding() {
        assertThat(repository.findById("CVE-NOT-THERE")).isEmpty();
    }
}
