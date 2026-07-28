package com.example.orderservice.entity;

import javax.persistence.*;
import javax.validation.constraints.DecimalMin;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "orders", indexes = {
    @Index(name = "idx_order_user_id", columnList = "user_id"),
    @Index(name = "idx_order_status", columnList = "status"),
    @Index(name = "idx_order_created_at", columnList = "created_at")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "User ID is required")
    @Column(name = "user_id", nullable = false, length = 50)
    private String userId;

    @NotNull(message = "Total amount is required")
    @DecimalMin(value = "0.0", inclusive = false, message = "Total amount must be greater than 0")
    @Column(name = "total_amount", nullable = false, precision = 10, scale = 2)
    private BigDecimal totalAmount;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private OrderStatus status = OrderStatus.PENDING;

    @Column(length = 255)
    private String shippingAddress;

    @Column(columnDefinition = "TEXT")
    private String items;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private Instant updatedAt;

    @OneToMany(mappedBy = "orderId", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<OrderStatusHistory> statusHistory = new ArrayList<>();

    public enum OrderStatus {
        PENDING,
        CONFIRMED,
        PROCESSING,
        SHIPPED,
        DELIVERED,
        CANCELLED,
        REFUNDED
    }
}