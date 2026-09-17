package com.acme.security.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record RemediationRequest(
        @NotBlank(message = "findingId is required") String findingId,
        @NotBlank(message = "repository is required") String repository,
        @Pattern(regexp = "^$|^[0-9A-Za-z][0-9A-Za-z._+-]*$", message = "requestedFixedVersion is invalid")
        String requestedFixedVersion) {
}
