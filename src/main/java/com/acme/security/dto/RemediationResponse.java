package com.acme.security.dto;

public record RemediationResponse(
        String requestId,
        String status,
        String findingId,
        String repository,
        String dependency,
        String severity,
        String currentVersion,
        String fixedVersion,
        String versionOwner,
        String message) {
}
