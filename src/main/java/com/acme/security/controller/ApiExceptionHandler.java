package com.acme.security.controller;

import com.acme.security.dto.ErrorResponse;
import com.acme.security.exception.DuplicateRemediationException;
import com.acme.security.exception.FindingNotFoundException;
import com.acme.security.exception.IneligibleFindingException;
import java.time.Instant;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(FindingNotFoundException.class)
    ResponseEntity<ErrorResponse> notFound(FindingNotFoundException exception) {
        return error(HttpStatus.NOT_FOUND, exception.getMessage());
    }

    @ExceptionHandler(DuplicateRemediationException.class)
    ResponseEntity<ErrorResponse> duplicate(DuplicateRemediationException exception) {
        return error(HttpStatus.CONFLICT, exception.getMessage());
    }

    @ExceptionHandler(IneligibleFindingException.class)
    ResponseEntity<ErrorResponse> ineligible(IneligibleFindingException exception) {
        return error(HttpStatus.UNPROCESSABLE_ENTITY, exception.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ErrorResponse> validation(MethodArgumentNotValidException exception) {
        List<String> details = exception.getBindingResult().getFieldErrors().stream()
                .map(field -> field.getField() + ": " + field.getDefaultMessage())
                .toList();
        return new ResponseEntity<>(new ErrorResponse(
                Instant.now(), HttpStatus.BAD_REQUEST.value(), "Bad Request", details),
                HttpStatus.BAD_REQUEST);
    }

    private ResponseEntity<ErrorResponse> error(HttpStatus status, String detail) {
        return new ResponseEntity<>(new ErrorResponse(
                Instant.now(), status.value(), status.getReasonPhrase(), List.of(detail)), status);
    }
}
