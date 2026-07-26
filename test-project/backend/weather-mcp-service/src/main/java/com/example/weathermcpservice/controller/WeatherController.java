package com.example.weathermcpservice.controller;

import com.example.weathermcpservice.dto.CreateAlertRequest;
import com.example.weathermcpservice.dto.WeatherAlertDTO;
import com.example.weathermcpservice.dto.WeatherResponse;
import com.example.weathermcpservice.service.WeatherMcpService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import javax.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/weather")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Weather MCP", description = "APIs for weather information and alerts")
public class WeatherController {

    private final WeatherMcpService weatherMcpService;

    @GetMapping("/current/{city}")
    @Operation(summary = "Get current weather", description = "Retrieves current weather information for a city")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<WeatherResponse> getCurrentWeather(
            @Parameter(description = "City name") @PathVariable String city) {
        log.info("GET /api/weather/current/{} - Retrieving current weather", city);
        WeatherResponse weather = weatherMcpService.getCurrentWeather(city);
        return ResponseEntity.ok(weather);
    }

    @PostMapping("/alert")
    @Operation(summary = "Create weather alert", description = "Creates a new weather alert for a user")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<WeatherAlertDTO> createAlert(@Valid @RequestBody CreateAlertRequest request) {
        log.info("POST /api/weather/alert - Creating alert for userId: {}", request.getUserId());
        WeatherAlertDTO alert = weatherMcpService.createAlert(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(alert);
    }

    @GetMapping("/alert/user/{userId}")
    @Operation(summary = "Get user alerts", description = "Retrieves all active alerts for a user")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<List<WeatherAlertDTO>> getUserAlerts(
            @Parameter(description = "User ID") @PathVariable String userId) {
        log.info("GET /api/weather/alert/user/{} - Retrieving user alerts", userId);
        List<WeatherAlertDTO> alerts = weatherMcpService.getUserAlerts(userId);
        return ResponseEntity.ok(alerts);
    }

    @PostMapping("/alert/{id}/deactivate")
    @Operation(summary = "Deactivate alert", description = "Deactivates a weather alert")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<WeatherAlertDTO> deactivateAlert(
            @Parameter(description = "Alert ID") @PathVariable Long id) {
        log.info("POST /api/weather/alert/{}/deactivate - Deactivating alert", id);
        try {
            WeatherAlertDTO alert = weatherMcpService.deactivateAlert(id);
            return ResponseEntity.ok(alert);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @GetMapping("/alert")
    @Operation(summary = "Get all alerts", description = "Retrieves all weather alerts with pagination")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<WeatherAlertDTO>> getAllAlerts(
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/weather/alert - Retrieving all alerts");
        return ResponseEntity.ok(weatherMcpService.getAllAlerts(pageable));
    }
}