package com.example.userservice.dto;

import com.example.userservice.entity.User;
import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class UserDTO {
    private Long id;
    private String username;
    private String email;
    private String role;
    private Boolean enabled;
    private Instant createdAt;
    private Instant updatedAt;

    public static UserDTO fromEntity(User user) {
        return UserDTO.builder()
            .id(user.getId())
            .username(user.getUsername())
            .email(user.getEmail())
            .role(user.getRole().name())
            .enabled(user.getEnabled())
            .createdAt(user.getCreatedAt())
            .updatedAt(user.getUpdatedAt())
            .build();
    }
}
