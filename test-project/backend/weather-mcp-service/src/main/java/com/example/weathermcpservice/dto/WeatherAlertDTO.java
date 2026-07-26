package com.example.weathermcpservice.dto;

import com.example.weathermcpservice.entity.WeatherAlert;
import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

@Data
@Builder
public class WeatherAlertDTO {
    private Long id;
    private String userId;
    private String city;
    private BigDecimal temperatureThreshold;
    private String alertType;
    private Boolean active;
    private Instant createdAt;

    public static WeatherAlertDTO fromEntity(WeatherAlert alert) {
        return WeatherAlertDTO.builder()
            .id(alert.getId())
            .userId(alert.getUserId())
            .city(alert.getCity())
            .temperatureThreshold(alert.getTemperatureThreshold())
            .alertType(alert.getAlertType().name())
            .active(alert.getActive())
            .createdAt(alert.getCreatedAt())
            .build();
    }
}
