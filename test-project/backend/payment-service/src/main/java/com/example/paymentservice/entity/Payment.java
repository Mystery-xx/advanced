package com.example.paymentservice.entity;

import javax.persistence.*;
import javax.validation.constraints.DecimalMin;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "payments", indexes = {
    @Index(name = "idx_payment_order_id", columnList = "orderId"),
    @Index(name = "idx_payment_user_id", columnList = "userId"),
    @Index(name = "idx_payment_status", columnList = "status"),
    @Index(name = "idx_payment_transaction_id", columnList = "transactionId")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Payment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "Transaction ID is required")
    @Column(name = "transaction_id", nullable = false, unique = true, length = 100)
    private String transactionId;

    @NotBlank(message = "Order ID is required")
    @Column(name = "order_id", nullable = false, length = 50)
    private String orderId;

    @NotBlank(message = "User ID is required")
    @Column(name = "user_id", nullable = false, length = 50)
    private String userId;

    @NotNull(message = "Amount is required")
    @DecimalMin(value = "0.01", message = "Amount must be greater than 0")
    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal amount;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private PaymentStatus status = PaymentStatus.PENDING;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private PaymentMethod method = PaymentMethod.CARD;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "failure_reason", length = 255)
    private String failureReason;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    public enum PaymentStatus {
        PENDING,
        PROCESSING,
        COMPLETED,
        FAILED,
        REFUNDED,
        PARTIALLY_REFUNDED
    }

    public enum PaymentMethod {
        CARD,
        BANK_TRANSFER,
        PAYPAL,
        CRYPTO
    }
}