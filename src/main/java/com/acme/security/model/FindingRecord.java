package com.acme.security.model;

public record FindingRecord(
        String findingId,
        String scanner,
        String severity,
        String repository,
        String module,
        String dependency,
        String currentVersion,
        String fixedVersion,
        String versionOwner,
        boolean eligible) {
}
