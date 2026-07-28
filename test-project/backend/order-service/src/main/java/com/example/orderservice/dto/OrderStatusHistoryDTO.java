package com.example.orderservice.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
@Schema(description = "Order status change history record")
public class OrderStatusHistoryDTO {
    @Schema(description = "History record ID", example = "1")
    private Long id;
    @Schema(description = "Order ID", example = "1")
    private Long orderId;
    @Schema(description = "Previous order status", example = "PENDING")
    private String oldStatus;
    @Schema(description = "New order status", example = "CONFIRMED")
    private String newStatus;
    @Schema(description = "Timestamp of status change")
    private Instant timestamp;
    @Schema(description = "User who made the change", example = "admin")
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