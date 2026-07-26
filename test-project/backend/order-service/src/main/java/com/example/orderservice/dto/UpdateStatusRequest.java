package com.example.orderservice.dto;

import javax.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class UpdateStatusRequest {
    @NotBlank(message = "Status is required")
    private String status;
}
