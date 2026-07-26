package com.example.paymentservice.service;

import com.example.paymentservice.dto.PaymentDTO;
import com.example.paymentservice.dto.PaymentRequest;
import com.example.paymentservice.dto.RefundRequest;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.Optional;

public interface PaymentService {

    PaymentDTO processPayment(PaymentRequest request);

    Optional<PaymentDTO> getPaymentById(Long id);

    Optional<PaymentDTO> getPaymentByTransactionId(String transactionId);

    Page<PaymentDTO> getPaymentsByOrderId(String orderId, Pageable pageable);

    Page<PaymentDTO> getPaymentsByUserId(String userId, Pageable pageable);

    PaymentDTO refundPayment(Long id, RefundRequest request);

    Page<PaymentDTO> getPaymentsByStatus(String status, Pageable pageable);
}