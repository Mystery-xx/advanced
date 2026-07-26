package com.example.paymentservice.service.impl;

import com.example.paymentservice.dto.PaymentDTO;
import com.example.paymentservice.dto.PaymentRequest;
import com.example.paymentservice.dto.RefundRequest;
import com.example.paymentservice.entity.Payment;
import com.example.paymentservice.repository.PaymentRepository;
import com.example.paymentservice.service.PaymentService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class PaymentServiceImpl implements PaymentService {

    private final PaymentRepository paymentRepository;

    @Override
    @Transactional
    public PaymentDTO processPayment(PaymentRequest request) {
        log.info("Processing payment for orderId: {}, userId: {}, amount: {}",
            request.getOrderId(), request.getUserId(), request.getAmount());

        String transactionId = UUID.randomUUID().toString().replace("-", "");

        Payment.PaymentMethod method = Payment.PaymentMethod.CARD;
        if (request.getMethod() != null) {
            try {
                method = Payment.PaymentMethod.valueOf(request.getMethod().toUpperCase());
            } catch (IllegalArgumentException e) {
                throw new IllegalArgumentException("Invalid payment method: " + request.getMethod() +
                    ". Valid methods: " + Arrays.toString(Payment.PaymentMethod.values()));
            }
        }

        Payment payment = Payment.builder()
            .transactionId(transactionId)
            .orderId(request.getOrderId())
            .userId(request.getUserId())
            .amount(request.getAmount())
            .method(method)
            .description(request.getDescription())
            .status(Payment.PaymentStatus.PENDING)
            .build();

        // Simulate payment processing
        payment.setStatus(Payment.PaymentStatus.PROCESSING);
        payment = paymentRepository.save(payment);

        // Simulate successful payment
        payment.setStatus(Payment.PaymentStatus.COMPLETED);
        Payment completedPayment = paymentRepository.save(payment);

        log.info("Payment completed with transactionId: {}", completedPayment.getTransactionId());

        return PaymentDTO.fromEntity(completedPayment);
    }

    @Override
    public Optional<PaymentDTO> getPaymentById(Long id) {
        log.debug("Getting payment by id: {}", id);
        return paymentRepository.findById(id).map(PaymentDTO::fromEntity);
    }

    @Override
    public Optional<PaymentDTO> getPaymentByTransactionId(String transactionId) {
        log.debug("Getting payment by transactionId: {}", transactionId);
        return paymentRepository.findByTransactionId(transactionId).map(PaymentDTO::fromEntity);
    }

    @Override
    public Page<PaymentDTO> getPaymentsByOrderId(String orderId, Pageable pageable) {
        log.debug("Getting payments by orderId: {}", orderId);
        return paymentRepository.findByOrderId(orderId, pageable).map(PaymentDTO::fromEntity);
    }

    @Override
    public Page<PaymentDTO> getPaymentsByUserId(String userId, Pageable pageable) {
        log.debug("Getting payments by userId: {}", userId);
        return paymentRepository.findByUserId(userId, pageable).map(PaymentDTO::fromEntity);
    }

    @Override
    @Transactional
    public PaymentDTO refundPayment(Long id, RefundRequest request) {
        log.info("Processing refund for payment id: {}, amount: {}", id, request.getAmount());

        Payment payment = paymentRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("Payment not found with id: " + id));

        if (payment.getStatus() != Payment.PaymentStatus.COMPLETED) {
            throw new IllegalArgumentException("Cannot refund payment with status: " + payment.getStatus());
        }

        if (request.getAmount().compareTo(payment.getAmount()) > 0) {
            throw new IllegalArgumentException("Refund amount cannot exceed original payment amount");
        }

        if (request.getAmount().compareTo(payment.getAmount()) < 0) {
            payment.setStatus(Payment.PaymentStatus.PARTIALLY_REFUNDED);
        } else {
            payment.setStatus(Payment.PaymentStatus.REFUNDED);
        }

        payment.setFailureReason(request.getReason());
        Payment refundedPayment = paymentRepository.save(payment);

        log.info("Refund processed for transactionId: {}", refundedPayment.getTransactionId());

        return PaymentDTO.fromEntity(refundedPayment);
    }

    @Override
    public Page<PaymentDTO> getPaymentsByStatus(String status, Pageable pageable) {
        log.debug("Getting payments by status: {}", status);
        try {
            Payment.PaymentStatus paymentStatus = Payment.PaymentStatus.valueOf(status.toUpperCase());
            return paymentRepository.findByStatus(paymentStatus, pageable).map(PaymentDTO::fromEntity);
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("Invalid payment status: " + status +
                ". Valid statuses: " + Arrays.toString(Payment.PaymentStatus.values()));
        }
    }
}