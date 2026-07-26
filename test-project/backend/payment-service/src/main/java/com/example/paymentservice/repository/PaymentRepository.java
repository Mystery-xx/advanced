package com.example.paymentservice.repository;

import com.example.paymentservice.entity.Payment;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PaymentRepository extends JpaRepository<Payment, Long> {

    Optional<Payment> findByTransactionId(String transactionId);

    Page<Payment> findByOrderId(String orderId, Pageable pageable);

    Page<Payment> findByUserId(String userId, Pageable pageable);

    Page<Payment> findByStatus(Payment.PaymentStatus status, Pageable pageable);

    List<Payment> findByOrderIdAndStatus(String orderId, Payment.PaymentStatus status);
}