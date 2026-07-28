package com.example.orderservice.service.impl;

import com.example.orderservice.dto.CreateOrderRequest;
import com.example.orderservice.dto.OrderDTO;
import com.example.orderservice.dto.OrderStatusHistoryDTO;
import com.example.orderservice.entity.Order;
import com.example.orderservice.entity.OrderStatusHistory;
import com.example.orderservice.repository.OrderRepository;
import com.example.orderservice.repository.OrderStatusHistoryRepository;
import com.example.orderservice.service.OrderService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class OrderServiceImpl implements OrderService {

    private final OrderRepository orderRepository;
    private final OrderStatusHistoryRepository orderStatusHistoryRepository;

    @Override
    @Transactional
    public OrderDTO createOrder(CreateOrderRequest request) {
        log.info("Creating order for userId: {}", request.getUserId());

        Order order = Order.builder()
            .userId(request.getUserId())
            .totalAmount(request.getTotalAmount())
            .shippingAddress(request.getShippingAddress())
            .items(request.getItems())
            .status(Order.OrderStatus.PENDING)
            .build();

        Order savedOrder = orderRepository.save(order);
        
        recordStatusChange(savedOrder.getId(), null, Order.OrderStatus.PENDING.name(), request.getUserId());
        
        log.info("Order created with id: {}", savedOrder.getId());

        return OrderDTO.fromEntity(savedOrder);
    }

    @Override
    public Optional<OrderDTO> getOrderById(Long id) {
        log.debug("Getting order by id: {}", id);
        return orderRepository.findById(id).map(OrderDTO::fromEntity);
    }

    @Override
    public Page<OrderDTO> getOrdersByUserId(String userId, Pageable pageable) {
        log.debug("Getting orders by userId: {}", userId);
        return orderRepository.findByUserId(userId, pageable).map(OrderDTO::fromEntity);
    }

    @Override
    public Page<OrderDTO> getAllOrders(Pageable pageable) {
        log.debug("Getting all orders with pagination: {}", pageable);
        return orderRepository.findAll(pageable).map(OrderDTO::fromEntity);
    }

    @Override
    @Transactional
    public OrderDTO updateOrderStatus(Long id, String status) {
        log.info("Updating order status for id: {} to {}", id, status);

        Order order = orderRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("Order not found with id: " + id));

        try {
            Order.OrderStatus newStatus = Order.OrderStatus.valueOf(status.toUpperCase());
            Order.OrderStatus oldStatus = order.getStatus();
            
            if (oldStatus != newStatus) {
                order.setStatus(newStatus);
                Order updatedOrder = orderRepository.save(order);
                recordStatusChange(id, oldStatus.name(), newStatus.name(), null);
                log.info("Order status updated from {} to {}", oldStatus, newStatus);
                return OrderDTO.fromEntity(updatedOrder);
            }
            
            log.info("Order status unchanged: {}", newStatus);
            return OrderDTO.fromEntity(order);
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("Invalid order status: " + status +
                ". Valid statuses: " + Arrays.toString(Order.OrderStatus.values()));
        }
    }

    @Override
    @Transactional
    public OrderDTO cancelOrder(Long id) {
        log.info("Cancelling order with id: {}", id);

        Order order = orderRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("Order not found with id: " + id));

        if (order.getStatus() == Order.OrderStatus.CANCELLED) {
            throw new IllegalArgumentException("Order is already cancelled");
        }

        if (order.getStatus() == Order.OrderStatus.SHIPPED ||
            order.getStatus() == Order.OrderStatus.DELIVERED) {
            throw new IllegalArgumentException("Cannot cancel order that has been shipped");
        }

        Order.OrderStatus oldStatus = order.getStatus();
        order.setStatus(Order.OrderStatus.CANCELLED);
        Order cancelledOrder = orderRepository.save(order);
        recordStatusChange(id, oldStatus.name(), Order.OrderStatus.CANCELLED.name(), null);
        log.info("Order cancelled successfully");

        return OrderDTO.fromEntity(cancelledOrder);
    }

    @Override
    public Page<OrderDTO> getOrdersByStatus(String status, Pageable pageable) {
        log.debug("Getting orders by status: {}", status);
        try {
            Order.OrderStatus orderStatus = Order.OrderStatus.valueOf(status.toUpperCase());
            return orderRepository.findByStatus(orderStatus, pageable).map(OrderDTO::fromEntity);
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("Invalid order status: " + status);
        }
    }

    @Override
    public Page<OrderStatusHistoryDTO> getOrderHistory(Long orderId, Pageable pageable) {
        log.debug("Getting order history for orderId: {}", orderId);
        return orderStatusHistoryRepository.findByOrderIdOrderByTimestampDesc(orderId, pageable)
            .map(OrderStatusHistoryDTO::fromEntity);
    }

    private void recordStatusChange(Long orderId, String oldStatus, String newStatus, String changedBy) {
        OrderStatusHistory history = OrderStatusHistory.builder()
            .orderId(orderId)
            .oldStatus(oldStatus)
            .newStatus(newStatus)
            .changedBy(changedBy)
            .build();
        orderStatusHistoryRepository.save(history);
        log.debug("Recorded status change for order {}: {} -> {}", orderId, oldStatus, newStatus);
    }
}