package com.example.paymentservice.controller;

import com.example.paymentservice.dto.PaymentDTO;
import com.example.paymentservice.dto.PaymentRequest;
import com.example.paymentservice.dto.RefundRequest;
import com.example.paymentservice.service.PaymentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import javax.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/payments")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Payment Management", description = "APIs for payment processing and refunds")
public class PaymentController {

    private final PaymentService paymentService;

    @PostMapping
    @Operation(summary = "Process payment", description = "Processes a new payment for an order")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<PaymentDTO> processPayment(@Valid @RequestBody PaymentRequest request) {
        log.info("POST /api/payments - Processing payment for orderId: {}", request.getOrderId());
        PaymentDTO payment = paymentService.processPayment(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(payment);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get payment by ID", description = "Retrieves a payment by its unique ID")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<PaymentDTO> getPaymentById(
            @Parameter(description = "Payment ID") @PathVariable Long id) {
        log.info("GET /api/payments/{} - Retrieving payment", id);
        return paymentService.getPaymentById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/transaction/{transactionId}")
    @Operation(summary = "Get payment by transaction ID", description = "Retrieves a payment by transaction ID")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<PaymentDTO> getPaymentByTransactionId(
            @Parameter(description = "Transaction ID") @PathVariable String transactionId) {
        log.info("GET /api/payments/transaction/{} - Retrieving payment", transactionId);
        return paymentService.getPaymentByTransactionId(transactionId)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/order/{orderId}")
    @Operation(summary = "Get payments by order ID", description = "Retrieves payments for a specific order")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<Page<PaymentDTO>> getPaymentsByOrderId(
            @Parameter(description = "Order ID") @PathVariable String orderId,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/payments/order/{} - Retrieving payments by order", orderId);
        return ResponseEntity.ok(paymentService.getPaymentsByOrderId(orderId, pageable));
    }

    @GetMapping("/user/{userId}")
    @Operation(summary = "Get payments by user ID", description = "Retrieves payments for a specific user")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<Page<PaymentDTO>> getPaymentsByUserId(
            @Parameter(description = "User ID") @PathVariable String userId,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/payments/user/{} - Retrieving payments by user", userId);
        return ResponseEntity.ok(paymentService.getPaymentsByUserId(userId, pageable));
    }

    @PostMapping("/{id}/refund")
    @Operation(summary = "Refund payment", description = "Processes a refund for a payment")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<PaymentDTO> refundPayment(
            @Parameter(description = "Payment ID") @PathVariable Long id,
            @Valid @RequestBody RefundRequest request) {
        log.info("POST /api/payments/{}/refund - Processing refund", id);
        try {
            PaymentDTO refundedPayment = paymentService.refundPayment(id, request);
            return ResponseEntity.ok(refundedPayment);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }

    @GetMapping("/status/{status}")
    @Operation(summary = "Get payments by status", description = "Retrieves payments filtered by status")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<PaymentDTO>> getPaymentsByStatus(
            @Parameter(description = "Payment status") @PathVariable String status,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/payments/status/{} - Retrieving payments by status", status);
        try {
            return ResponseEntity.ok(paymentService.getPaymentsByStatus(status, pageable));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }
}