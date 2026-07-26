package com.example.weathermcpservice.dto;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class CreateAlertRequest {
    @NotBlank(message = "User ID is required")
    private String userId;

    @NotBlank(message = "City is required")
    private String city;

    @NotNull(message = "Temperature threshold is required")
    private BigDecimal temperatureThreshold;

    private String alertType;
}
