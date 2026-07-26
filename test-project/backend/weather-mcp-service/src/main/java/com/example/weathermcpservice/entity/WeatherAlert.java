package com.example.weathermcpservice.entity;

import javax.persistence.*;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "weather_alerts", indexes = {
    @Index(name = "idx_alert_user_id", columnList = "userId"),
    @Index(name = "idx_alert_city", columnList = "city"),
    @Index(name = "idx_alert_active", columnList = "active")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WeatherAlert {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "User ID is required")
    @Column(name = "user_id", nullable = false, length = 50)
    private String userId;

    @NotBlank(message = "City is required")
    @Column(nullable = false, length = 100)
    private String city;

    @NotNull(message = "Temperature threshold is required")
    @Column(name = "temperature_threshold", nullable = false, precision = 5, scale = 2)
    private BigDecimal temperatureThreshold;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private AlertType alertType = AlertType.HIGH_TEMPERATURE;

    @Column(nullable = false)
    @Builder.Default
    private Boolean active = true;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    public enum AlertType {
        HIGH_TEMPERATURE,
        LOW_TEMPERATURE,
        PRECIPITATION,
        WIND,
        STORM
    }
}