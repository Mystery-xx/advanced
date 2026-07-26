package com.example.userservice.controller;

import com.example.userservice.dto.CreateUserRequest;
import com.example.userservice.dto.UserDTO;
import com.example.userservice.service.UserService;
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
@RequestMapping("/api/users")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "User Management", description = "APIs for managing users")
public class UserController {

    private final UserService userService;

    @PostMapping
    @Operation(summary = "Create a new user", description = "Creates a new user with the provided details")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UserDTO> createUser(@Valid @RequestBody CreateUserRequest request) {
        log.info("POST /api/users - Creating user: {}", request.getUsername());
        UserDTO createdUser = userService.createUser(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdUser);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get user by ID", description = "Retrieves a user by their unique ID")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<UserDTO> getUserById(
            @Parameter(description = "User ID") @PathVariable Long id) {
        log.info("GET /api/users/{} - Retrieving user", id);
        return userService.getUserById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    @Operation(summary = "Get all users", description = "Retrieves all users with pagination support")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<UserDTO>> getAllUsers(
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/users - Retrieving all users with pagination");
        return ResponseEntity.ok(userService.getAllUsers(pageable));
    }

    @GetMapping("/username/{username}")
    @Operation(summary = "Get user by username", description = "Retrieves a user by their username")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<UserDTO> getUserByUsername(
            @Parameter(description = "Username") @PathVariable String username) {
        log.info("GET /api/users/username/{} - Retrieving user by username", username);
        return userService.getUserByUsername(username)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update user", description = "Updates an existing user with the provided details")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<UserDTO> updateUser(
            @Parameter(description = "User ID") @PathVariable Long id,
            @Valid @RequestBody CreateUserRequest request) {
        log.info("PUT /api/users/{} - Updating user", id);
        try {
            UserDTO updatedUser = userService.updateUser(id, request);
            return ResponseEntity.ok(updatedUser);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete user", description = "Deletes a user by their ID")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> deleteUser(
            @Parameter(description = "User ID") @PathVariable Long id) {
        log.info("DELETE /api/users/{} - Deleting user", id);
        try {
            userService.deleteUser(id);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @GetMapping("/role/{role}")
    @Operation(summary = "Get users by role", description = "Retrieves users filtered by role")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<UserDTO>> getUsersByRole(
            @Parameter(description = "User role (USER or ADMIN)") @PathVariable String role,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/users/role/{} - Retrieving users by role", role);
        try {
            return ResponseEntity.ok(userService.getUsersByRole(role, pageable));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }

    @GetMapping("/search")
    @Operation(summary = "Search users", description = "Searches users by username or email")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<UserDTO>> searchUsers(
            @Parameter(description = "Search query") @RequestParam String query,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/users/search - Searching users with query: {}", query);
        return ResponseEntity.ok(userService.searchUsers(query, pageable));
    }
}