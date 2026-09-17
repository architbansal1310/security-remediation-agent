package com.acme.security.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.acme.security.dto.RemediationResponse;
import com.acme.security.exception.DuplicateRemediationException;
import com.acme.security.exception.FindingNotFoundException;
import com.acme.security.exception.IneligibleFindingException;
import com.acme.security.model.FindingRecord;
import com.acme.security.repository.FindingRepository;
import com.acme.security.service.RemediationService;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(RemediationController.class)
class RemediationControllerTest {
    @Autowired private MockMvc mvc;
    @MockBean private RemediationService service;
    @MockBean private FindingRepository repository;

    @Test
    void returnsCreatedForApprovedRequest() throws Exception {
        when(service.approve(any())).thenReturn(new RemediationResponse(
                "request-1", "APPROVED", "CVE-1", "repo", "g:a", "CRITICAL",
                "1.0", "1.1", "parent", "approved"));

        mvc.perform(post("/api/v1/remediations")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"findingId\":\"CVE-1\",\"repository\":\"repo\",\"requestedFixedVersion\":\"1.1\"}"))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", "/api/v1/remediations/request-1"))
                .andExpect(jsonPath("$.status").value("APPROVED"));
    }

    @Test
    void returnsBadRequestForMissingFields() throws Exception {
        mvc.perform(post("/api/v1/remediations")
                        .contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.details.length()").value(2));
    }

    @Test
    void mapsDomainFailuresToUsefulStatuses() throws Exception {
        when(service.approve(any()))
                .thenThrow(new DuplicateRemediationException("duplicate"))
                .thenThrow(new IneligibleFindingException("ineligible"))
                .thenThrow(new FindingNotFoundException("missing"));
        String body = "{\"findingId\":\"CVE-1\",\"repository\":\"repo\",\"requestedFixedVersion\":\"1.1\"}";

        mvc.perform(post("/api/v1/remediations").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isConflict());
        mvc.perform(post("/api/v1/remediations").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isUnprocessableEntity());
        mvc.perform(post("/api/v1/remediations").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isNotFound());
    }

    @Test
    void listsFindings() throws Exception {
        when(repository.findAll()).thenReturn(List.of(new FindingRecord(
                "CVE-1", "NEXUS", "HIGH", "repo", "module", "g:a",
                "1.0", "1.1", "child", true)));
        mvc.perform(get("/api/v1/findings"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].findingId").value("CVE-1"));
    }
}
