package com.example.weathermcpservice.service.impl;

import com.example.weathermcpservice.dto.CreateAlertRequest;
import com.example.weathermcpservice.dto.WeatherAlertDTO;
import com.example.weathermcpservice.dto.WeatherResponse;
import com.example.weathermcpservice.entity.WeatherAlert;
import com.example.weathermcpservice.repository.WeatherAlertRepository;
import com.example.weathermcpservice.service.WeatherMcpService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class WeatherMcpServiceImpl implements WeatherMcpService {

    private final WeatherAlertRepository weatherAlertRepository;

    @Override
    public WeatherResponse getCurrentWeather(String city) {
        log.info("Getting current weather for city: {}", city);
        // Mock weather data - in production, this would call a real weather API
        return WeatherResponse.mockWeather(city);
    }

    @Override
    @Transactional
    public WeatherAlertDTO createAlert(CreateAlertRequest request) {
        log.info("Creating weather alert for userId: {}, city: {}", request.getUserId(), request.getCity());

        WeatherAlert.AlertType alertType = WeatherAlert.AlertType.HIGH_TEMPERATURE;
        if (request.getAlertType() != null) {
            try {
                alertType = WeatherAlert.AlertType.valueOf(request.getAlertType().toUpperCase());
            } catch (IllegalArgumentException e) {
                throw new IllegalArgumentException("Invalid alert type: " + request.getAlertType());
            }
        }

        WeatherAlert alert = WeatherAlert.builder()
            .userId(request.getUserId())
            .city(request.getCity())
            .temperatureThreshold(request.getTemperatureThreshold())
            .alertType(alertType)
            .active(true)
            .build();

        WeatherAlert savedAlert = weatherAlertRepository.save(alert);
        log.info("Weather alert created with id: {}", savedAlert.getId());

        return WeatherAlertDTO.fromEntity(savedAlert);
    }

    @Override
    public List<WeatherAlertDTO> getUserAlerts(String userId) {
        log.debug("Getting alerts for userId: {}", userId);
        return weatherAlertRepository.findByUserIdAndActive(userId, true)
            .stream()
            .map(WeatherAlertDTO::fromEntity)
            .collect(java.util.stream.Collectors.toList());
    }

    @Override
    @Transactional
    public WeatherAlertDTO deactivateAlert(Long id) {
        log.info("Deactivating weather alert with id: {}", id);

        WeatherAlert alert = weatherAlertRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("Alert not found with id: " + id));

        alert.setActive(false);
        WeatherAlert deactivatedAlert = weatherAlertRepository.save(alert);
        log.info("Weather alert deactivated");

        return WeatherAlertDTO.fromEntity(deactivatedAlert);
    }

    @Override
    public Page<WeatherAlertDTO> getAllAlerts(Pageable pageable) {
        log.debug("Getting all alerts with pagination: {}", pageable);
        return weatherAlertRepository.findAll(pageable).map(WeatherAlertDTO::fromEntity);
    }
}