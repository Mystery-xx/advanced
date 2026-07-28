package com.example.orderservice.service;

import com.example.orderservice.dto.CreateOrderRequest;
import com.example.orderservice.dto.OrderDTO;
import com.example.orderservice.dto.OrderStatusHistoryDTO;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.Optional;

public interface OrderService {

    OrderDTO createOrder(CreateOrderRequest request);

    Optional<OrderDTO> getOrderById(Long id);

    Page<OrderDTO> getOrdersByUserId(String userId, Pageable pageable);

    Page<OrderDTO> getAllOrders(Pageable pageable);

    OrderDTO updateOrderStatus(Long id, String status);

    OrderDTO cancelOrder(Long id);

    Page<OrderDTO> getOrdersByStatus(String status, Pageable pageable);

    Page<OrderStatusHistoryDTO> getOrderHistory(Long orderId, Pageable pageable);
}