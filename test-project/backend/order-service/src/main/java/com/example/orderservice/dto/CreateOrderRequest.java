package com.example.orderservice.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import javax.validation.constraints.DecimalMin;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;

@Data
@Schema(description = "Request to create a new order")
public class CreateOrderRequest {
    @Schema(description = "User ID", example = "user123", required = true)
    @NotBlank(message = "User ID is required")
    private String userId;

    @Schema(description = "Total order amount", example = "99.99", required = true)
    @NotNull(message = "Total amount is required")
    @DecimalMin(value = "0.0", inclusive = false, message = "Total amount must be greater than 0")
    private BigDecimal totalAmount;

    @Schema(description = "Shipping address", example = "123 Main St, City")
    private String shippingAddress;

    @Schema(description = "Order items as JSON string")
    private String items;
}
