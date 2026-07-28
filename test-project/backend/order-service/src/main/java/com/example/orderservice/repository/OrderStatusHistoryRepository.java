package com.example.orderservice.repository;

import com.example.orderservice.entity.OrderStatusHistory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface OrderStatusHistoryRepository extends JpaRepository<OrderStatusHistory, Long> {

    Page<OrderStatusHistory> findByOrderIdOrderByTimestampDesc(Long orderId, Pageable pageable);
}