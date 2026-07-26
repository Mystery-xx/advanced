package com.example.weathermcpservice.service;

import com.example.weathermcpservice.dto.CreateAlertRequest;
import com.example.weathermcpservice.dto.WeatherAlertDTO;
import com.example.weathermcpservice.dto.WeatherResponse;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;

public interface WeatherMcpService {

    WeatherResponse getCurrentWeather(String city);

    WeatherAlertDTO createAlert(CreateAlertRequest request);

    List<WeatherAlertDTO> getUserAlerts(String userId);

    WeatherAlertDTO deactivateAlert(Long id);

    Page<WeatherAlertDTO> getAllAlerts(Pageable pageable);
}