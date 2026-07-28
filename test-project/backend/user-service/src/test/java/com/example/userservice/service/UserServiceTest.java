package com.example.userservice.service;

import com.example.userservice.dto.CreateUserRequest;
import com.example.userservice.dto.UserDTO;
import com.example.userservice.entity.User;
import com.example.userservice.repository.UserRepository;
import com.example.userservice.service.impl.UserServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.times;

@ExtendWith(MockitoExtension.class)
@DisplayName("UserService Unit Tests")
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private UserServiceImpl userService;

    private User testUser;
    private UserDTO testUserDTO;
    private CreateUserRequest createRequest;

    @BeforeEach
    void setUp() {
        testUser = User.builder()
            .id(1L)
            .username("testuser")
            .email("test@example.com")
            .password("encodedPassword")
            .role(User.Role.USER)
            .enabled(true)
            .createdAt(Instant.now())
            .updatedAt(Instant.now())
            .build();

        testUserDTO = UserDTO.builder()
            .id(1L)
            .username("testuser")
            .email("test@example.com")
            .role("USER")
            .enabled(true)
            .createdAt(testUser.getCreatedAt())
            .updatedAt(testUser.getUpdatedAt())
            .build();

        createRequest = new CreateUserRequest();
        createRequest.setUsername("testuser");
        createRequest.setEmail("test@example.com");
        createRequest.setPassword("rawPassword123");
        createRequest.setRole("USER");
    }

    @Test
    @DisplayName("getAllUsers should return paginated users with default parameters (page=0, size=10)")
    void getAllUsers_WithDefaultPagination_ShouldReturnFirstPage() {
        // Given
        Pageable pageable = PageRequest.of(0, 10);
        List<User> users = Arrays.asList(testUser);
        Page<User> userPage = new org.springframework.data.domain.PageImpl<>(users, pageable, users.size());

        given(userRepository.findAll(pageable)).willReturn(userPage);

        // When
        Page<UserDTO> result = userService.getAllUsers(pageable);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getContent()).hasSize(1);
        assertThat(result.getContent().get(0).getUsername()).isEqualTo("testuser");
        assertThat(result.getTotalElements()).isEqualTo(1);
        assertThat(result.getTotalPages()).isEqualTo(1);
        assertThat(result.getNumber()).isEqualTo(0);
        assertThat(result.getSize()).isEqualTo(10);
    }

    @Test
    @DisplayName("getAllUsers should return paginated users with custom page and size")
    void getAllUsers_WithCustomPagination_ShouldReturnCorrectPage() {
        // Given
        Pageable pageable = PageRequest.of(1, 5);
        List<User> users = Arrays.asList(
            createUser(2L, "user2", "user2@example.com"),
            createUser(3L, "user3", "user3@example.com")
        );
        Page<User> userPage = new org.springframework.data.domain.PageImpl<>(users, pageable, 12L);

        given(userRepository.findAll(pageable)).willReturn(userPage);

        // When
        Page<UserDTO> result = userService.getAllUsers(pageable);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getContent()).hasSize(2);
        assertThat(result.getTotalElements()).isEqualTo(12);
        assertThat(result.getTotalPages()).isEqualTo(3);
        assertThat(result.getNumber()).isEqualTo(1);
        assertThat(result.getSize()).isEqualTo(5);
        assertThat(result.isFirst()).isFalse();
        assertThat(result.hasNext()).isTrue();
    }

    @Test
    @DisplayName("getAllUsers should return sorted users when sort parameter is provided")
    void getAllUsers_WithSort_ShouldReturnSortedUsers() {
        // Given
        Pageable pageable = PageRequest.of(0, 10, Sort.by(Sort.Direction.ASC, "username"));
        List<User> users = Arrays.asList(
            createUser(1L, "alice", "alice@example.com"),
            createUser(2L, "bob", "bob@example.com"),
            createUser(3L, "charlie", "charlie@example.com")
        );
        Page<User> userPage = new org.springframework.data.domain.PageImpl<>(users, pageable, users.size());

        given(userRepository.findAll(pageable)).willReturn(userPage);

        // When
        Page<UserDTO> result = userService.getAllUsers(pageable);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getContent()).hasSize(3);
        assertThat(result.getContent().get(0).getUsername()).isEqualTo("alice");
        assertThat(result.getContent().get(1).getUsername()).isEqualTo("bob");
        assertThat(result.getContent().get(2).getUsername()).isEqualTo("charlie");
        assertThat(result.getSort()).isEqualTo(Sort.by(Sort.Direction.ASC, "username"));
    }

    @Test
    @DisplayName("getAllUsers should return sorted users by multiple fields")
    void getAllUsers_WithMultiFieldSort_ShouldReturnCorrectlySortedUsers() {
        // Given
        Pageable pageable = PageRequest.of(0, 10, Sort.by(Sort.Direction.ASC, "role").and(Sort.by(Sort.Direction.ASC, "username")));
        List<User> users = Arrays.asList(
            createUserWithRole(3L, "charlie", "ADMIN"),
            createUserWithRole(1L, "alice", "USER"),
            createUserWithRole(2L, "bob", "USER")
        );
        Page<User> userPage = new org.springframework.data.domain.PageImpl<>(users, pageable, users.size());

        given(userRepository.findAll(pageable)).willReturn(userPage);

        // When
        Page<UserDTO> result = userService.getAllUsers(pageable);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getContent()).hasSize(3);
        assertThat(result.getContent().get(0).getRole()).isEqualTo("ADMIN");
        assertThat(result.getContent().get(1).getRole()).isEqualTo("USER");
        assertThat(result.getContent().get(2).getRole()).isEqualTo("USER");
    }

    @Test
    @DisplayName("getAllUsers should return empty page when no users exist")
    void getAllUsers_WhenNoUsersExist_ShouldReturnEmptyPage() {
        // Given
        Pageable pageable = PageRequest.of(0, 10);
        Page<User> userPage = new org.springframework.data.domain.PageImpl<>(Arrays.asList(), pageable, 0L);

        given(userRepository.findAll(pageable)).willReturn(userPage);

        // When
        Page<UserDTO> result = userService.getAllUsers(pageable);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getContent()).isEmpty();
        assertThat(result.getTotalElements()).isEqualTo(0);
        assertThat(result.getTotalPages()).isEqualTo(0);
        assertThat(result.hasContent()).isFalse();
    }

    @Test
    @DisplayName("getAllUsers should return pagination metadata correctly")
    void getAllUsers_WithPagination_ShouldReturnCorrectMetadata() {
        // Given
        Pageable pageable = PageRequest.of(2, 5);
        List<User> users = Arrays.asList(
            createUser(11L, "user11", "user11@example.com"),
            createUser(12L, "user12", "user12@example.com")
        );
        Page<User> userPage = new org.springframework.data.domain.PageImpl<>(users, pageable, 25L);

        given(userRepository.findAll(pageable)).willReturn(userPage);

        // When
        Page<UserDTO> result = userService.getAllUsers(pageable);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getContent()).hasSize(2);
        assertThat(result.getTotalElements()).isEqualTo(25);
        assertThat(result.getTotalPages()).isEqualTo(5);
        assertThat(result.getNumber()).isEqualTo(2);
        assertThat(result.getSize()).isEqualTo(5);
        assertThat(result.isFirst()).isFalse();
        assertThat(result.hasNext()).isTrue();
    }

    @Test
    @DisplayName("createUser should create and return user")
    void createUser_WithValidRequest_ShouldCreateUser() {
        // Given
        given(userRepository.existsByUsername("testuser")).willReturn(false);
        given(userRepository.existsByEmail("test@example.com")).willReturn(false);
        given(passwordEncoder.encode("rawPassword123")).willReturn("encodedPassword");
        given(userRepository.save(any(User.class))).willReturn(testUser);

        // When
        UserDTO result = userService.createUser(createRequest);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getUsername()).isEqualTo("testuser");
        assertThat(result.getEmail()).isEqualTo("test@example.com");
        verify(userRepository, times(1)).save(any(User.class));
    }

    @Test
    @DisplayName("createUser should throw exception when username exists")
    void createUser_WhenUsernameExists_ShouldThrowException() {
        // Given
        given(userRepository.existsByUsername("testuser")).willReturn(true);

        // When & Then
        assertThatThrownBy(() -> userService.createUser(createRequest))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Username already exists");
    }

    @Test
    @DisplayName("createUser should throw exception when email exists")
    void createUser_WhenEmailExists_ShouldThrowException() {
        // Given
        given(userRepository.existsByUsername("testuser")).willReturn(false);
        given(userRepository.existsByEmail("test@example.com")).willReturn(true);

        // When & Then
        assertThatThrownBy(() -> userService.createUser(createRequest))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Email already exists");
    }

    @Test
    @DisplayName("getUserById should return user when exists")
    void getUserById_WhenUserExists_ShouldReturnUser() {
        // Given
        given(userRepository.findById(1L)).willReturn(Optional.of(testUser));

        // When
        Optional<UserDTO> result = userService.getUserById(1L);

        // Then
        assertThat(result).isPresent();
        assertThat(result.get().getId()).isEqualTo(1L);
        assertThat(result.get().getUsername()).isEqualTo("testuser");
    }

    @Test
    @DisplayName("getUserById should return empty when user not found")
    void getUserById_WhenUserNotFound_ShouldReturnEmpty() {
        // Given
        given(userRepository.findById(999L)).willReturn(Optional.empty());

        // When
        Optional<UserDTO> result = userService.getUserById(999L);

        // Then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("deleteUser should delete user when exists")
    void deleteUser_WhenUserExists_ShouldDelete() {
        // Given
        given(userRepository.existsById(1L)).willReturn(true);

        // When
        userService.deleteUser(1L);

        // Then
        verify(userRepository, times(1)).deleteById(1L);
    }

    @Test
    @DisplayName("deleteUser should throw exception when user not found")
    void deleteUser_WhenUserNotFound_ShouldThrowException() {
        // Given
        given(userRepository.existsById(999L)).willReturn(false);

        // When & Then
        assertThatThrownBy(() -> userService.deleteUser(999L))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("User not found");
    }

    @Test
    @DisplayName("getUsersByRole should return paginated users filtered by role")
    void getUsersByRole_WithValidRole_ShouldReturnFilteredUsers() {
        // Given
        Pageable pageable = PageRequest.of(0, 10);
        List<User> users = Arrays.asList(
            createUserWithRole(1L, "admin1", "ADMIN"),
            createUserWithRole(2L, "admin2", "ADMIN")
        );
        Page<User> userPage = new org.springframework.data.domain.PageImpl<>(users, pageable, users.size());

        given(userRepository.findByRole(User.Role.ADMIN, pageable)).willReturn(userPage);

        // When
        Page<UserDTO> result = userService.getUsersByRole("ADMIN", pageable);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getContent()).hasSize(2);
        assertThat(result.getContent().get(0).getRole()).isEqualTo("ADMIN");
        assertThat(result.getContent().get(1).getRole()).isEqualTo("ADMIN");
    }

    @Test
    @DisplayName("searchUsers should return paginated users matching query")
    void searchUsers_WithValidQuery_ShouldReturnMatchingUsers() {
        // Given
        Pageable pageable = PageRequest.of(0, 10);
        List<User> users = Arrays.asList(
            createUser(1L, "john", "john@example.com"),
            createUser(2L, "johnny", "johnny@example.com")
        );
        Page<User> userPage = new org.springframework.data.domain.PageImpl<>(users, pageable, users.size());

        given(userRepository.search("john", pageable)).willReturn(userPage);

        // When
        Page<UserDTO> result = userService.searchUsers("john", pageable);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getContent()).hasSize(2);
        assertThat(result.getContent().get(0).getUsername()).containsIgnoringCase("john");
    }

    // Helper methods
    private User createUser(Long id, String username, String email) {
        return User.builder()
            .id(id)
            .username(username)
            .email(email)
            .password("password")
            .role(User.Role.USER)
            .enabled(true)
            .createdAt(Instant.now())
            .updatedAt(Instant.now())
            .build();
    }

    private User createUserWithRole(Long id, String username, String role) {
        return User.builder()
            .id(id)
            .username(username)
            .email(username + "@example.com")
            .password("password")
            .role(User.Role.valueOf(role))
            .enabled(true)
            .createdAt(Instant.now())
            .updatedAt(Instant.now())
            .build();
    }
}