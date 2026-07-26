package com.example.weathermcpservice.dto;

import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;

@Data
@Builder
public class WeatherResponse {
    private String city;
    private String country;
    private BigDecimal temperature;
    private String description;
    private BigDecimal humidity;
    private BigDecimal windSpeed;
    private Long timestamp;

    public static WeatherResponse mockWeather(String city) {
        return WeatherResponse.builder()
            .city(city)
            .country("Unknown")
            .temperature(BigDecimal.valueOf(20.5))
            .description("Partly cloudy")
            .humidity(BigDecimal.valueOf(65))
            .windSpeed(BigDecimal.valueOf(5.2))
            .timestamp(System.currentTimeMillis())
            .build();
    }
}
