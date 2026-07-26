package com.example.orderservice.controller;

import com.example.orderservice.dto.CreateOrderRequest;
import com.example.orderservice.dto.OrderDTO;
import com.example.orderservice.dto.UpdateStatusRequest;
import com.example.orderservice.service.OrderService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import javax.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Order Management", description = "APIs for managing orders")
public class OrderController {

    private final OrderService orderService;

    @PostMapping
    @Operation(summary = "Create a new order", description = "Creates a new order with the provided details")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<OrderDTO> createOrder(@Valid @RequestBody CreateOrderRequest request) {
        log.info("POST /api/orders - Creating order for userId: {}", request.getUserId());
        OrderDTO createdOrder = orderService.createOrder(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdOrder);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get order by ID", description = "Retrieves an order by its unique ID")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<OrderDTO> getOrderById(
            @Parameter(description = "Order ID") @PathVariable Long id) {
        log.info("GET /api/orders/{} - Retrieving order", id);
        return orderService.getOrderById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    @Operation(summary = "Get all orders", description = "Retrieves all orders with pagination support")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<OrderDTO>> getAllOrders(
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/orders - Retrieving all orders");
        return ResponseEntity.ok(orderService.getAllOrders(pageable));
    }

    @GetMapping("/user/{userId}")
    @Operation(summary = "Get orders by user ID", description = "Retrieves orders for a specific user")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<Page<OrderDTO>> getOrdersByUserId(
            @Parameter(description = "User ID") @PathVariable String userId,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/orders/user/{} - Retrieving orders by user", userId);
        return ResponseEntity.ok(orderService.getOrdersByUserId(userId, pageable));
    }

    @PutMapping("/{id}/status")
    @Operation(summary = "Update order status", description = "Updates the status of an existing order")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<OrderDTO> updateOrderStatus(
            @Parameter(description = "Order ID") @PathVariable Long id,
            @Valid @RequestBody UpdateStatusRequest request) {
        log.info("PUT /api/orders/{}/status - Updating order status to {}", id, request.getStatus());
        try {
            OrderDTO updatedOrder = orderService.updateOrderStatus(id, request.getStatus());
            return ResponseEntity.ok(updatedOrder);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }

    @PostMapping("/{id}/cancel")
    @Operation(summary = "Cancel order", description = "Cancels an existing order")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<OrderDTO> cancelOrder(
            @Parameter(description = "Order ID") @PathVariable Long id) {
        log.info("POST /api/orders/{}/cancel - Cancelling order", id);
        try {
            OrderDTO cancelledOrder = orderService.cancelOrder(id);
            return ResponseEntity.ok(cancelledOrder);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }

    @GetMapping("/status/{status}")
    @Operation(summary = "Get orders by status", description = "Retrieves orders filtered by status")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<OrderDTO>> getOrdersByStatus(
            @Parameter(description = "Order status") @PathVariable String status,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/orders/status/{} - Retrieving orders by status", status);
        try {
            return ResponseEntity.ok(orderService.getOrdersByStatus(status, pageable));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }
}