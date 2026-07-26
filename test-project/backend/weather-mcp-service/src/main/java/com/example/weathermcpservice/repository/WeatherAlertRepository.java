package com.example.weathermcpservice.repository;

import com.example.weathermcpservice.entity.WeatherAlert;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface WeatherAlertRepository extends JpaRepository<WeatherAlert, Long> {

    Page<WeatherAlert> findByUserId(String userId, Pageable pageable);

    List<WeatherAlert> findByUserIdAndActive(String userId, Boolean active);

    Page<WeatherAlert> findByCity(String city, Pageable pageable);

    Page<WeatherAlert> findByActive(Boolean active, Pageable pageable);
}