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

/**
 * REST controller for managing user operations.
 * Provides endpoints for creating, retrieving, updating, and deleting users.
 * All endpoints require authentication and appropriate role-based access control.
 * 
 * Base URL: /api/users
 */
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "User Management", description = "APIs for managing users")
public class UserController {

    private final UserService userService;

    /**
     * Creates a new user with the provided details.
     * 
     * @param request The user creation request containing username, email, password, and role
     * @return ResponseEntity with the created UserDTO and HTTP 201 CREATED status
     * @throws org.springframework.web.bind.MethodArgumentNotValidException if request validation fails
     * 
     * Example request:
     * POST /api/users
     * {
     *   "username": "john_doe",
     *   "email": "john@example.com",
     *   "password": "securePassword123",
     *   "role": "USER"
     * }
     * 
     * Example response:
     * {
     *   "id": 1,
     *   "username": "john_doe",
     *   "email": "john@example.com",
     *   "role": "USER",
     *   "createdAt": "2024-01-15T10:30:00Z"
     * }
     */
    @PostMapping
    @Operation(summary = "Create a new user", description = "Creates a new user with the provided details")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UserDTO> createUser(@Valid @RequestBody CreateUserRequest request) {
        log.info("POST /api/users - Creating user: {}", request.getUsername());
        UserDTO createdUser = userService.createUser(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdUser);
    }

/**
     * Retrieves a user by their unique ID.
     * 
     * @param id The unique identifier of the user to retrieve
     * @return ResponseEntity with UserDTO if found (HTTP 200 OK), or empty response (HTTP 404 NOT FOUND)
     * 
     * Example request:
     * GET /api/users/1
     * 
     * Example response (200 OK):
     * {
     *   "id": 1,
     *   "username": "john_doe",
     *   "email": "john@example.com",
     *   "role": "USER"
     * }
     */
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

    /**
     * Retrieves all users with pagination support.
     * 
     * @param pageable Pagination configuration (default: page=0, size=10)
     * @return ResponseEntity containing Page of UserDTO objects with pagination metadata
     * 
     * Example request:
     * GET /api/users?page=0&size=10&sort=username,asc
     * 
     * Example response:
     * {
     *   "content": [...],
     *   "totalElements": 50,
     *   "totalPages": 5,
     *   "number": 0,
     *   "size": 10
     * }
     */
    @GetMapping
    @Operation(summary = "Get all users", description = "Retrieves all users with pagination support")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<UserDTO>> getAllUsers(
            @PageableDefault(page = 0, size = 10) Pageable pageable) {
        log.info("GET /api/users - Retrieving all users with pagination");
        return ResponseEntity.ok(userService.getAllUsers(pageable));
    }

    /**
     * Retrieves a user by their username.
     * 
     * @param username The username of the user to retrieve
     * @return ResponseEntity with UserDTO if found (HTTP 200 OK), or empty response (HTTP 404 NOT FOUND)
     * 
     * Example request:
     * GET /api/users/username/john_doe
     * 
     * Example response (200 OK):
     * {
     *   "id": 1,
     *   "username": "john_doe",
     *   "email": "john@example.com",
     *   "role": "USER"
     * }
     */
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

    /**
     * Updates an existing user with the provided details.
     * 
     * @param id The unique identifier of the user to update
     * @param request The update request containing new user details
     * @return ResponseEntity with updated UserDTO (HTTP 200 OK), or empty response (HTTP 404 NOT FOUND)
     * @throws IllegalArgumentException if user with specified ID does not exist
     * 
     * Example request:
     * PUT /api/users/1
     * {
     *   "username": "john_updated",
     *   "email": "john.updated@example.com",
     *   "role": "ADMIN"
     * }
     * 
     * Example response (200 OK):
     * {
     *   "id": 1,
     *   "username": "john_updated",
     *   "email": "john.updated@example.com",
     *   "role": "ADMIN"
     * }
     */
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

    /**
     * Deletes a user by their ID.
     * 
     * @param id The unique identifier of the user to delete
     * @return ResponseEntity with HTTP 204 NO CONTENT on success, or HTTP 404 NOT FOUND if user doesn't exist
     * @throws IllegalArgumentException if user with specified ID does not exist
     * 
     * Example request:
     * DELETE /api/users/1
     * 
     * Example response (204 NO CONTENT):
     * (empty body)
     */
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

    /**
     * Retrieves users filtered by role.
     * 
     * @param role The role to filter by (USER or ADMIN)
     * @param pageable Pagination configuration (default: size=20)
     * @return ResponseEntity containing Page of UserDTO objects filtered by role
     * @throws IllegalArgumentException if invalid role is provided
     * 
     * Example request:
     * GET /api/users/role/ADMIN?page=0&size=20
     * 
     * Example response:
     * {
     *   "content": [
     *     {"id": 1, "username": "admin1", "role": "ADMIN"},
     *     {"id": 2, "username": "admin2", "role": "ADMIN"}
     *   ],
     *   "totalElements": 5,
     *   "totalPages": 1
     * }
     */
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

    /**
     * Searches users by username or email.
     * 
     * @param query The search query to match against username or email
     * @param pageable Pagination configuration (default: size=20)
     * @return ResponseEntity containing Page of UserDTO objects matching the search query
     * 
     * Example request:
     * GET /api/users/search?query=john&page=0&size=20
     * 
     * Example response:
     * {
     *   "content": [
     *     {"id": 1, "username": "john_doe", "email": "john@example.com"},
     *     {"id": 5, "username": "johnny", "email": "johnny@example.com"}
     *   ],
     *   "totalElements": 2,
     *   "totalPages": 1
     * }
     */
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