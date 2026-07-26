package com.example.userservice.service;

import com.example.userservice.dto.UserDTO;
import com.example.userservice.dto.CreateUserRequest;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.Optional;

public interface UserService {

    UserDTO createUser(CreateUserRequest request);

    Optional<UserDTO> getUserById(Long id);

    Page<UserDTO> getAllUsers(Pageable pageable);

    Optional<UserDTO> getUserByUsername(String username);

    UserDTO updateUser(Long id, CreateUserRequest request);

    void deleteUser(Long id);

    Page<UserDTO> getUsersByRole(String role, Pageable pageable);

    Page<UserDTO> searchUsers(String query, Pageable pageable);
}