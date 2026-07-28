package com.example.userservice.service.impl;

import com.example.userservice.dto.CreateUserRequest;
import com.example.userservice.dto.UserDTO;
import com.example.userservice.entity.User;
import com.example.userservice.repository.UserRepository;
import com.example.userservice.service.UserService;
import com.example.userservice.util.PasswordUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    @Transactional
    public UserDTO createUser(CreateUserRequest request) {
        log.info("Creating user with username: {}", request.getUsername());

        PasswordUtil.validatePassword(request.getPassword());

        if (userRepository.existsByUsername(request.getUsername())) {
            throw new IllegalArgumentException("Username already exists: " + request.getUsername());
        }

        if (userRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("Email already exists: " + request.getEmail());
        }

        User.Role role = User.Role.USER;
        if (request.getRole() != null) {
            try {
                role = User.Role.valueOf(request.getRole().toUpperCase());
            } catch (IllegalArgumentException e) {
                throw new IllegalArgumentException("Invalid role: " + request.getRole());
            }
        }

        User user = User.builder()
            .username(request.getUsername())
            .email(request.getEmail())
            .password(passwordEncoder.encode(request.getPassword()))
            .role(role)
            .enabled(true)
            .build();

        User savedUser = userRepository.save(user);
        log.info("User created with id: {}", savedUser.getId());

        return UserDTO.fromEntity(savedUser);
    }

    @Override
    public Optional<UserDTO> getUserById(Long id) {
        log.debug("Getting user by id: {}", id);
        return userRepository.findById(id).map(UserDTO::fromEntity);
    }

    @Override
    public Page<UserDTO> getAllUsers(Pageable pageable) {
        log.debug("Getting all users with pagination: {}", pageable);
        return userRepository.findAll(pageable).map(UserDTO::fromEntity);
    }

    @Override
    public Optional<UserDTO> getUserByUsername(String username) {
        log.debug("Getting user by username: {}", username);
        return userRepository.findByUsername(username).map(UserDTO::fromEntity);
    }

    @Override
    @Transactional
    public UserDTO updateUser(Long id, CreateUserRequest request) {
        log.info("Updating user with id: {}", id);

        User user = userRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("User not found with id: " + id));

        if (!request.getUsername().equals(user.getUsername()) && userRepository.existsByUsername(request.getUsername())) {
            throw new IllegalArgumentException("Username already exists: " + request.getUsername());
        }

        if (!request.getEmail().equals(user.getEmail()) && userRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("Email already exists: " + request.getEmail());
        }

        user.setUsername(request.getUsername());
        user.setEmail(request.getEmail());

        if (request.getRole() != null) {
            try {
                user.setRole(User.Role.valueOf(request.getRole().toUpperCase()));
            } catch (IllegalArgumentException e) {
                throw new IllegalArgumentException("Invalid role: " + request.getRole());
            }
        }

        User updatedUser = userRepository.save(user);
        log.info("User updated with id: {}", updatedUser.getId());

        return UserDTO.fromEntity(updatedUser);
    }

    @Override
    @Transactional
    public void deleteUser(Long id) {
        log.info("Deleting user with id: {}", id);

        if (!userRepository.existsById(id)) {
            throw new IllegalArgumentException("User not found with id: " + id);
        }

        userRepository.deleteById(id);
        log.info("User deleted with id: {}", id);
    }

    @Override
    public Page<UserDTO> getUsersByRole(String role, Pageable pageable) {
        log.debug("Getting users by role: {}", role);
        User.Role userRole = User.Role.valueOf(role.toUpperCase());
        return userRepository.findByRole(userRole, pageable).map(UserDTO::fromEntity);
    }

    @Override
    public Page<UserDTO> searchUsers(String query, Pageable pageable) {
        log.debug("Searching users with query: {}", query);
        return userRepository.search(query, pageable).map(UserDTO::fromEntity);
    }
}