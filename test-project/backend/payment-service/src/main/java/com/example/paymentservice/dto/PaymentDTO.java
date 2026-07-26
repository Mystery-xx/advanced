package com.example.paymentservice.dto;

import com.example.paymentservice.entity.Payment;
import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

@Data
@Builder
public class PaymentDTO {
    private Long id;
    private String transactionId;
    private String orderId;
    private String userId;
    private BigDecimal amount;
    private String status;
    private String method;
    private String description;
    private String failureReason;
    private Instant createdAt;

    public static PaymentDTO fromEntity(Payment payment) {
        return PaymentDTO.builder()
            .id(payment.getId())
            .transactionId(payment.getTransactionId())
            .orderId(payment.getOrderId())
            .userId(payment.getUserId())
            .amount(payment.getAmount())
            .status(payment.getStatus().name())
            .method(payment.getMethod().name())
            .description(payment.getDescription())
            .failureReason(payment.getFailureReason())
            .createdAt(payment.getCreatedAt())
            .build();
    }
}
