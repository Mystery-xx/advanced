package com.example.orderservice.service;

import com.example.orderservice.dto.CreateOrderRequest;
import com.example.orderservice.dto.OrderDTO;
import com.example.orderservice.dto.OrderStatusHistoryDTO;
import com.example.orderservice.entity.Order;
import com.example.orderservice.entity.OrderStatusHistory;
import com.example.orderservice.repository.OrderRepository;
import com.example.orderservice.repository.OrderStatusHistoryRepository;
import com.example.orderservice.service.impl.OrderServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Arrays;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class OrderServiceImplTest {

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private OrderStatusHistoryRepository orderStatusHistoryRepository;

    private OrderServiceImpl orderService;

    @BeforeEach
    void setUp() {
        orderService = new OrderServiceImpl(orderRepository, orderStatusHistoryRepository);
    }

    @Test
    void createOrder_shouldCreateOrderAndRecordHistory() {
        CreateOrderRequest request = new CreateOrderRequest();
        request.setUserId("user123");
        request.setTotalAmount(new BigDecimal("100.00"));
        request.setShippingAddress("123 Test St");
        request.setItems("item1,item2");

        Order savedOrder = Order.builder()
            .id(1L)
            .userId("user123")
            .totalAmount(new BigDecimal("100.00"))
            .shippingAddress("123 Test St")
            .items("item1,item2")
            .status(Order.OrderStatus.PENDING)
            .createdAt(Instant.now())
            .build();

        when(orderRepository.save(any(Order.class))).thenReturn(savedOrder);
        when(orderStatusHistoryRepository.save(any(OrderStatusHistory.class))).thenAnswer(i -> i.getArguments()[0]);

        OrderDTO result = orderService.createOrder(request);

        assertNotNull(result);
        assertEquals(1L, result.getId());
        assertEquals("PENDING", result.getStatus());

        ArgumentCaptor<OrderStatusHistory> historyCaptor = ArgumentCaptor.forClass(OrderStatusHistory.class);
        verify(orderStatusHistoryRepository).save(historyCaptor.capture());

        OrderStatusHistory capturedHistory = historyCaptor.getValue();
        assertEquals(1L, capturedHistory.getOrderId());
        assertNull(capturedHistory.getOldStatus());
        assertEquals("PENDING", capturedHistory.getNewStatus());
        assertEquals("user123", capturedHistory.getChangedBy());
    }

    @Test
    void updateOrderStatus_shouldUpdateStatusAndRecordHistory() {
        Order existingOrder = Order.builder()
            .id(1L)
            .userId("user123")
            .totalAmount(new BigDecimal("100.00"))
            .status(Order.OrderStatus.PENDING)
            .build();

        Order updatedOrder = Order.builder()
            .id(1L)
            .userId("user123")
            .totalAmount(new BigDecimal("100.00"))
            .status(Order.OrderStatus.CONFIRMED)
            .build();

        when(orderRepository.findById(1L)).thenReturn(Optional.of(existingOrder));
        when(orderRepository.save(any(Order.class))).thenReturn(updatedOrder);
        when(orderStatusHistoryRepository.save(any(OrderStatusHistory.class))).thenAnswer(i -> i.getArguments()[0]);

        OrderDTO result = orderService.updateOrderStatus(1L, "CONFIRMED");

        assertNotNull(result);
        assertEquals("CONFIRMED", result.getStatus());

        ArgumentCaptor<OrderStatusHistory> historyCaptor = ArgumentCaptor.forClass(OrderStatusHistory.class);
        verify(orderStatusHistoryRepository).save(historyCaptor.capture());

        OrderStatusHistory capturedHistory = historyCaptor.getValue();
        assertEquals(1L, capturedHistory.getOrderId());
        assertEquals("PENDING", capturedHistory.getOldStatus());
        assertEquals("CONFIRMED", capturedHistory.getNewStatus());
    }

    @Test
    void cancelOrder_shouldCancelOrderAndRecordHistory() {
        Order existingOrder = Order.builder()
            .id(1L)
            .userId("user123")
            .totalAmount(new BigDecimal("100.00"))
            .status(Order.OrderStatus.PENDING)
            .build();

        Order cancelledOrder = Order.builder()
            .id(1L)
            .userId("user123")
            .totalAmount(new BigDecimal("100.00"))
            .status(Order.OrderStatus.CANCELLED)
            .build();

        when(orderRepository.findById(1L)).thenReturn(Optional.of(existingOrder));
        when(orderRepository.save(any(Order.class))).thenReturn(cancelledOrder);
        when(orderStatusHistoryRepository.save(any(OrderStatusHistory.class))).thenAnswer(i -> i.getArguments()[0]);

        OrderDTO result = orderService.cancelOrder(1L);

        assertNotNull(result);
        assertEquals("CANCELLED", result.getStatus());

        ArgumentCaptor<OrderStatusHistory> historyCaptor = ArgumentCaptor.forClass(OrderStatusHistory.class);
        verify(orderStatusHistoryRepository).save(historyCaptor.capture());

        OrderStatusHistory capturedHistory = historyCaptor.getValue();
        assertEquals(1L, capturedHistory.getOrderId());
        assertEquals("PENDING", capturedHistory.getOldStatus());
        assertEquals("CANCELLED", capturedHistory.getNewStatus());
    }

    @Test
    void getOrderHistory_shouldReturnHistoryPage() {
        Long orderId = 1L;
        Pageable pageable = PageRequest.of(0, 20);

        OrderStatusHistory history1 = OrderStatusHistory.builder()
            .id(1L)
            .orderId(orderId)
            .oldStatus(null)
            .newStatus("PENDING")
            .timestamp(Instant.now())
            .changedBy("user123")
            .build();

        OrderStatusHistory history2 = OrderStatusHistory.builder()
            .id(2L)
            .orderId(orderId)
            .oldStatus("PENDING")
            .newStatus("CONFIRMED")
            .timestamp(Instant.now())
            .changedBy("admin")
            .build();

        Page<OrderStatusHistory> historyPage = new PageImpl<>(Arrays.asList(history1, history2));

        when(orderStatusHistoryRepository.findByOrderIdOrderByTimestampDesc(orderId, pageable))
            .thenReturn(historyPage);

        Page<OrderStatusHistoryDTO> result = orderService.getOrderHistory(orderId, pageable);

        assertNotNull(result);
        assertEquals(2, result.getTotalElements());
        assertEquals(2, result.getContent().size());

        OrderStatusHistoryDTO firstHistory = result.getContent().get(0);
        assertEquals(1L, firstHistory.getId());
        assertEquals("PENDING", firstHistory.getNewStatus());
    }

    @Test
    void updateOrderStatus_sameStatus_shouldNotRecordHistory() {
        Order existingOrder = Order.builder()
            .id(1L)
            .userId("user123")
            .totalAmount(new BigDecimal("100.00"))
            .status(Order.OrderStatus.PENDING)
            .build();

        when(orderRepository.findById(1L)).thenReturn(Optional.of(existingOrder));

        OrderDTO result = orderService.updateOrderStatus(1L, "PENDING");

        assertNotNull(result);
        assertEquals("PENDING", result.getStatus());
        verify(orderStatusHistoryRepository, never()).save(any());
    }

    @Test
    void updateOrderStatus_invalidStatus_shouldThrowException() {
        Order existingOrder = Order.builder()
            .id(1L)
            .userId("user123")
            .totalAmount(new BigDecimal("100.00"))
            .status(Order.OrderStatus.PENDING)
            .build();

        when(orderRepository.findById(1L)).thenReturn(Optional.of(existingOrder));

        IllegalArgumentException exception = assertThrows(
            IllegalArgumentException.class,
            () -> orderService.updateOrderStatus(1L, "INVALID_STATUS")
        );

        assertTrue(exception.getMessage().contains("Invalid order status"));
    }

    @Test
    void cancelOrder_alreadyCancelled_shouldThrowException() {
        Order cancelledOrder = Order.builder()
            .id(1L)
            .userId("user123")
            .totalAmount(new BigDecimal("100.00"))
            .status(Order.OrderStatus.CANCELLED)
            .build();

        when(orderRepository.findById(1L)).thenReturn(Optional.of(cancelledOrder));

        IllegalArgumentException exception = assertThrows(
            IllegalArgumentException.class,
            () -> orderService.cancelOrder(1L)
        );

        assertEquals("Order is already cancelled", exception.getMessage());
    }

    @Test
    void cancelOrder_shippedOrder_shouldThrowException() {
        Order shippedOrder = Order.builder()
            .id(1L)
            .userId("user123")
            .totalAmount(new BigDecimal("100.00"))
            .status(Order.OrderStatus.SHIPPED)
            .build();

        when(orderRepository.findById(1L)).thenReturn(Optional.of(shippedOrder));

        IllegalArgumentException exception = assertThrows(
            IllegalArgumentException.class,
            () -> orderService.cancelOrder(1L)
        );

        assertEquals("Cannot cancel order that has been shipped", exception.getMessage());
    }
}