package com.example.orderservice.dto;

import com.example.orderservice.entity.Order;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

@Data
@Builder
@Schema(description = "Order data transfer object")
public class OrderDTO {
    @Schema(description = "Order ID", example = "1")
    private Long id;
    @Schema(description = "User ID", example = "user123")
    private String userId;
    @Schema(description = "Total order amount", example = "99.99")
    private BigDecimal totalAmount;
    @Schema(description = "Order status", example = "PENDING", allowableValues = {"PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"})
    private String status;
    @Schema(description = "Shipping address", example = "123 Main St, City")
    private String shippingAddress;
    @Schema(description = "Order items as JSON string")
    private String items;
    @Schema(description = "Creation timestamp")
    private Instant createdAt;
    @Schema(description = "Last update timestamp")
    private Instant updatedAt;

    public static OrderDTO fromEntity(Order order) {
        return OrderDTO.builder()
            .id(order.getId())
            .userId(order.getUserId())
            .totalAmount(order.getTotalAmount())
            .status(order.getStatus().name())
            .shippingAddress(order.getShippingAddress())
            .items(order.getItems())
            .createdAt(order.getCreatedAt())
            .updatedAt(order.getUpdatedAt())
            .build();
    }
}
