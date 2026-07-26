package com.example.orderservice.repository;

import com.example.orderservice.entity.Order;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {

    Page<Order> findByUserId(String userId, Pageable pageable);

    Page<Order> findByStatus(Order.OrderStatus status, Pageable pageable);

    List<Order> findByUserIdAndStatus(String userId, Order.OrderStatus status);

    @Query("SELECT o FROM Order o WHERE o.userId = :userId AND o.status NOT IN (:excludedStatuses)")
    Page<Order> findActiveOrders(@Param("userId") String userId,
                                  @Param("excludedStatuses") List<Order.OrderStatus> excludedStatuses,
                                  Pageable pageable);
}