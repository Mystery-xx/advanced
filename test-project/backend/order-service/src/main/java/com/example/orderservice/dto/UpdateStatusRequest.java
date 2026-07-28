package com.example.orderservice.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import javax.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "Request to update order status")
public class UpdateStatusRequest {
    @Schema(description = "New order status", example = "CONFIRMED", allowableValues = {"PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"}, required = true)
    @NotBlank(message = "Status is required")
    private String status;
}
