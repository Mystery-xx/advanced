package com.example.orderservice.entity;

import javax.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.Instant;

@Entity
@Table(name = "order_status_history", indexes = {
    @Index(name = "idx_history_order_id", columnList = "order_id"),
    @Index(name = "idx_history_timestamp", columnList = "timestamp")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OrderStatusHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "order_id", nullable = false)
    private Long orderId;

    @Column(name = "old_status", length = 20)
    private String oldStatus;

    @Column(name = "new_status", nullable = false, length = 20)
    private String newStatus;

    @CreationTimestamp
    @Column(name = "timestamp", nullable = false, updatable = false)
    private Instant timestamp;

    @Column(name = "changed_by", length = 50)
    private String changedBy;
}