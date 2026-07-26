package com.example.orderservice.dto;

import com.example.orderservice.entity.Order;
import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

@Data
@Builder
public class OrderDTO {
    private Long id;
    private String userId;
    private BigDecimal totalAmount;
    private String status;
    private String shippingAddress;
    private String items;
    private Instant createdAt;
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
