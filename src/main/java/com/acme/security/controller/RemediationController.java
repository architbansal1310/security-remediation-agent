package com.acme.security.controller;

import com.acme.security.dto.RemediationRequest;
import com.acme.security.dto.RemediationResponse;
import com.acme.security.model.FindingRecord;
import com.acme.security.repository.FindingRepository;
import com.acme.security.service.RemediationService;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
public class RemediationController {
    private final RemediationService service;
    private final FindingRepository repository;

    public RemediationController(RemediationService service, FindingRepository repository) {
        this.service = service;
        this.repository = repository;
    }

    @PostMapping("/remediations")
    public ResponseEntity<RemediationResponse> create(@Valid @RequestBody RemediationRequest request) {
        RemediationResponse response = service.approve(request);
        return ResponseEntity.created(URI.create("/api/v1/remediations/" + response.requestId()))
                .body(response);
    }

    @GetMapping("/findings")
    public List<FindingRecord> findings() {
        return repository.findAll();
    }
}
