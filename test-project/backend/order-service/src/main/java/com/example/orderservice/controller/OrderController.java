package com.example.orderservice.controller;

import com.example.orderservice.dto.CreateOrderRequest;
import com.example.orderservice.dto.OrderDTO;
import com.example.orderservice.dto.OrderStatusHistoryDTO;
import com.example.orderservice.dto.UpdateStatusRequest;
import com.example.orderservice.service.OrderService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
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
    @ApiResponse(responseCode = "201", description = "Order created successfully", content = @Content(schema = @Schema(implementation = OrderDTO.class)))
    @ApiResponse(responseCode = "400", description = "Invalid request data")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<OrderDTO> createOrder(@Valid @RequestBody CreateOrderRequest request) {
        log.info("POST /api/orders - Creating order for userId: {}", request.getUserId());
        OrderDTO createdOrder = orderService.createOrder(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdOrder);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get order by ID", description = "Retrieves an order by its unique ID")
    @ApiResponse(responseCode = "200", description = "Order found", content = @Content(schema = @Schema(implementation = OrderDTO.class)))
    @ApiResponse(responseCode = "404", description = "Order not found")
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
    @ApiResponse(responseCode = "200", description = "Successfully retrieved orders", content = @Content(schema = @Schema(implementation = Page.class)))
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<OrderDTO>> getAllOrders(
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/orders - Retrieving all orders");
        return ResponseEntity.ok(orderService.getAllOrders(pageable));
    }

    @GetMapping("/user/{userId}")
    @Operation(summary = "Get orders by user ID", description = "Retrieves orders for a specific user")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved user orders", content = @Content(schema = @Schema(implementation = Page.class)))
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<Page<OrderDTO>> getOrdersByUserId(
            @Parameter(description = "User ID") @PathVariable String userId,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/orders/user/{} - Retrieving orders by user", userId);
        return ResponseEntity.ok(orderService.getOrdersByUserId(userId, pageable));
    }

    @PutMapping("/{id}/status")
    @Operation(summary = "Update order status", description = "Updates the status of an existing order")
    @ApiResponse(responseCode = "200", description = "Status updated successfully", content = @Content(schema = @Schema(implementation = OrderDTO.class)))
    @ApiResponse(responseCode = "400", description = "Invalid status or request data")
    @ApiResponse(responseCode = "404", description = "Order not found")
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
    @ApiResponse(responseCode = "200", description = "Order cancelled successfully", content = @Content(schema = @Schema(implementation = OrderDTO.class)))
    @ApiResponse(responseCode = "400", description = "Order cannot be cancelled")
    @ApiResponse(responseCode = "404", description = "Order not found")
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
    @ApiResponse(responseCode = "200", description = "Successfully retrieved orders by status", content = @Content(schema = @Schema(implementation = Page.class)))
    @ApiResponse(responseCode = "400", description = "Invalid status value")
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

    @GetMapping("/{id}/history")
    @Operation(summary = "Get order status history", description = "Retrieves the status change history for an order")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved order history", content = @Content(schema = @Schema(implementation = Page.class)))
    @ApiResponse(responseCode = "404", description = "Order not found")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<Page<OrderStatusHistoryDTO>> getOrderHistory(
            @Parameter(description = "Order ID") @PathVariable Long id,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/orders/{}/history - Retrieving order status history", id);
        return ResponseEntity.ok(orderService.getOrderHistory(id, pageable));
    }
}