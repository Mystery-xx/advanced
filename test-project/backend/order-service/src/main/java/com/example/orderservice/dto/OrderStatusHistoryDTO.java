package com.example.orderservice.dto;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class OrderStatusHistoryDTO {
    private Long id;
    private Long orderId;
    private String oldStatus;
    private String newStatus;
    private Instant timestamp;
    private String changedBy;

    public static OrderStatusHistoryDTO fromEntity(com.example.orderservice.entity.OrderStatusHistory history) {
        return OrderStatusHistoryDTO.builder()
            .id(history.getId())
            .orderId(history.getOrderId())
            .oldStatus(history.getOldStatus())
            .newStatus(history.getNewStatus())
            .timestamp(history.getTimestamp())
            .changedBy(history.getChangedBy())
            .build();
    }
}