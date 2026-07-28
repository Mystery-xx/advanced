# Project Rules: Test Project

**Stack:** Spring Boot 2.7.18 + React 18 + TypeScript + Vite  
**Database:** PostgreSQL 15  
**Orchestration:** Docker Compose

---

## 1. Architecture Overview

### Backend Microservices (Spring Boot 2.7.18, Java 11)

| Service | Port | Purpose | Key Entities |
|---------|------|---------|--------------|
| `user-service` | 8081 | User management, authentication, JWT | `User`, `Role` |
| `order-service` | 8082 | Order processing | `Order`, `OrderItem`, `OrderStatus` |
| `payment-service` | 8083 | Payment handling, transactions | `Payment`, `Transaction` |
| `weather-mcp-service` | 8084 | Weather API, MCP integration | Stateless (external API) |

### Frontend (React 18 + TypeScript + Vite)

- **Port:** 3000
- **Router:** React Router v6
- **State:** React Context + hooks
- **API Client:** Axios with interceptors
- **Pages:** Home, Login, Signup, Dashboard, Orders, Weather

### Database

- **PostgreSQL 15** via Docker Compose
- **Database:** `testdb`
- **User:** `testuser` / `testpass`
- **Port:** 5432

---

## 2. Backend Patterns

### 2.1 Layered Architecture

```
Controller → Service (Interface + Impl) → Repository → Entity
```

**Example Flow:**
```
UserController (REST) → UserServiceImpl (Business Logic) → UserRepository (JPA) → User (Entity)
```

### 2.2 Controller Layer

- `@RestController` with `@RequestMapping`
- Use `@Valid` on `@RequestBody` parameters
- Return `ResponseEntity<T>` for HTTP control
- Add `@PreAuthorize` for security
- Use `@Slf4j` for logging
- Use `@Tag` for Swagger documentation

**Good Example - UserController.java:**
```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "User Management", description = "APIs for managing users")
public class UserController {

    private final UserService userService;

    @PostMapping
    @Operation(summary = "Create a new user")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UserDTO> createUser(@Valid @RequestBody CreateUserRequest request) {
        log.info("POST /api/users - Creating user: {}", request.getUsername());
        UserDTO createdUser = userService.createUser(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdUser);
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<UserDTO> getUserById(@PathVariable Long id) {
        return userService.getUserById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}
```

### 2.3 Service Layer

- Interface defines contract
- Implementation uses `@Service`, `@Transactional`
- Throw `IllegalArgumentException` for business errors
- Return `Optional<T>` or `Page<T>` for queries

**Good Example - UserService.java (Interface):**
```java
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
```

**Good Example - UserServiceImpl.java:**
```java
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
}
```

### 2.4 DTOs with Static Factory

- Request DTOs: `{Entity}Request` with `@Valid` annotations
- Response DTOs: `{Entity}DTO` with `fromEntity()` static method
- Use Lombok `@Data`, `@Builder`

**Good Example - CreateUserRequest.java:**
```java
@Data
public class CreateUserRequest {
    @NotBlank(message = "Username is required")
    @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
    private String username;

    @NotBlank(message = "Email is required")
    @Email(message = "Email should be valid")
    private String email;

    @NotBlank(message = "Password is required")
    @Size(min = 8, message = "Password must be at least 8 characters")
    private String password;

    private String role;
}
```

**Good Example - UserDTO.java:**
```java
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
```

### 2.5 Repository Layer

- Extend `JpaRepository<Entity, ID>`
- Use method naming for derived queries
- Use `@Query` for custom JPQL
- Return `Optional<T>`, `Page<T>`, or `List<T>`

**Good Example - UserRepository.java:**
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByUsername(String username);

    Optional<User> findByEmail(String email);

    Page<User> findByRole(User.Role role, Pageable pageable);

    @Query("SELECT u FROM User u WHERE LOWER(u.username) LIKE LOWER(CONCAT('%', :query, '%')) " +
            "OR LOWER(u.email) LIKE LOWER(CONCAT('%', :query, '%'))")
    Page<User> search(@Param("query") String query, Pageable pageable);

    boolean existsByUsername(String username);

    boolean existsByEmail(String email);
}
```

### 2.6 Entity Layer

- Use `@Entity`, `@Table` with indexes
- Validation annotations on fields
- Lombok `@Data`, `@Builder`, `@NoArgsConstructor`, `@AllArgsConstructor`
- `@CreationTimestamp`, `@UpdateTimestamp` for auditing
- Enum with `@Enumerated(EnumType.STRING)`

**Good Example - User.java:**
```java
@Entity
@Table(name = "users", indexes = {
    @Index(name = "idx_user_email", columnList = "email"),
    @Index(name = "idx_user_role", columnList = "role")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "Username is required")
    @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
    @Column(nullable = false, unique = true, length = 50)
    private String username;

    @NotBlank(message = "Email is required")
    @Email(message = "Email should be valid")
    @Column(nullable = false, unique = true, length = 100)
    private String email;

    @NotBlank(message = "Password is required")
    @Size(min = 8, message = "Password must be at least 8 characters")
    @Column(nullable = false)
    private String password;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private Role role = Role.USER;

    @Column(nullable = false)
    @Builder.Default
    private Boolean enabled = true;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private Instant updatedAt;

    public enum Role {
        USER,
        ADMIN
    }
}
```

**Good Example - Order.java:**
```java
@Entity
@Table(name = "orders", indexes = {
    @Index(name = "idx_order_user_id", columnList = "user_id"),
    @Index(name = "idx_order_status", columnList = "status"),
    @Index(name = "idx_order_created_at", columnList = "created_at")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "User ID is required")
    @Column(name = "user_id", nullable = false, length = 50)
    private String userId;

    @NotNull(message = "Total amount is required")
    @DecimalMin(value = "0.0", inclusive = false, message = "Total amount must be greater than 0")
    @Column(name = "total_amount", nullable = false, precision = 10, scale = 2)
    private BigDecimal totalAmount;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private OrderStatus status = OrderStatus.PENDING;

    @Column(length = 255)
    private String shippingAddress;

    @Column(columnDefinition = "TEXT")
    private String items;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private Instant updatedAt;

    public enum OrderStatus {
        PENDING,
        CONFIRMED,
        PROCESSING,
        SHIPPED,
        DELIVERED,
        CANCELLED,
        REFUNDED
    }
}
```

### 2.7 Security

- Use `@PreAuthorize` on controller methods
- Roles: `USER`, `ADMIN`
- JWT tokens for authentication
- Password encoding with `PasswordEncoder`

---

## 3. Frontend Patterns

### 3.1 Functional Components with Hooks

- Use `useState`, `useEffect`, `useCallback`
- No class components
- Export as `default function ComponentName`

**Good Example - LoginPage.tsx:**
```tsx
import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface FormErrors {
  email?: string;
  password?: string;
}

function validateEmail(email: string): string | undefined {
  if (!email) return 'Email is required';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Invalid email format';
  return undefined;
}

function validatePassword(password: string): string | undefined {
  if (!password) return 'Password is required';
  if (password.length < 6) return 'Password must be at least 6 characters';
  return undefined;
}

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setApiError('');

    const emailErr = validateEmail(email);
    const passErr = validatePassword(password);
    setErrors({ email: emailErr, password: passErr });

    if (emailErr || passErr) return;

    setLoading(true);
    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch {
      setApiError('Invalid credentials. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Sign In</h1>
        <p className="auth-subtitle">Welcome back to Test App</p>

        {apiError && <div className="alert alert-error">{apiError}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={errors.email ? 'input-error' : ''}
              placeholder="you@example.com"
              autoComplete="email"
            />
            {errors.email && <span className="field-error">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={errors.password ? 'input-error' : ''}
              placeholder="••••••••"
              autoComplete="current-password"
            />
            {errors.password && <span className="field-error">{errors.password}</span>}
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="auth-footer">
          Don't have an account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}
```

### 3.2 TypeScript Interfaces (No `any`)

- Define all types in `src/types/index.ts`
- Use interfaces for API responses
- Use union types for enums

**Good Example - types/index.ts:**
```typescript
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'USER' | 'ADMIN';
  active: boolean;
  createdAt: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface Order {
  id: string;
  userId: string;
  product: string;
  quantity: number;
  status: 'PENDING' | 'CONFIRMED' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED';
  total: number;
  createdAt: string;
}

export interface CreateOrderRequest {
  product: string;
  quantity: number;
  total: number;
}

export interface WeatherData {
  city: string;
  temperature: number;
  humidity: number;
  windSpeed: number;
  description: string;
  icon: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  content: T[];
  totalPages: number;
  totalElements: number;
  currentPage: number;
}
```

### 3.3 Axios Interceptor for Bearer Token

- Create axios instance with base URL
- Request interceptor adds `Authorization: Bearer {token}`
- Response interceptor handles 401 (clear token, redirect to login)

**Good Example - api.ts:**
```typescript
import axios from 'axios';
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Order,
  CreateOrderRequest,
  WeatherData,
  PaginatedResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (data: LoginRequest) =>
  api.post<AuthResponse>('/auth/login', data).then((r) => r.data);

export const register = (data: RegisterRequest) =>
  api.post<AuthResponse>('/auth/register', data).then((r) => r.data);

export const getCurrentUser = () =>
  api.get<User>('/auth/me').then((r) => r.data);

// Users
export const getUsers = (page = 0, size = 10) =>
  api.get<PaginatedResponse<User>>('/users', { params: { page, size } }).then((r) => r.data);

export const getUser = (id: string) =>
  api.get<User>(`/users/${id}`).then((r) => r.data);

export const createUser = (data: { name: string; email: string; password: string; role?: string }) =>
  api.post<User>('/users', data).then((r) => r.data);

export const updateUser = (id: string, data: Partial<User>) =>
  api.put<User>(`/users/${id}`, data).then((r) => r.data);

export const deleteUser = (id: string) =>
  api.delete(`/users/${id}`).then((r) => r.data);

// Orders
export const getOrders = (page = 0, size = 10) =>
  api.get<PaginatedResponse<Order>>('/orders', { params: { page, size } }).then((r) => r.data);

export const getOrder = (id: string) =>
  api.get<Order>(`/orders/${id}`).then((r) => r.data);

export const createOrder = (data: CreateOrderRequest) =>
  api.post<Order>('/orders', data).then((r) => r.data);

// Weather
export const getWeather = (city: string) =>
  api.get<WeatherData>('/weather', { params: { city } }).then((r) => r.data);

export default api;
```

### 3.4 useAuth Context for Auth State

- `AuthProvider` wraps the app
- `useAuth()` hook provides auth state and methods
- Store token and user in localStorage

**Good Example - useAuth.tsx:**
```tsx
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { User, LoginRequest, RegisterRequest } from '../types';
import { login as apiLogin, register as apiRegister } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('auth_user');
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth_token'));

  const login = useCallback(async (data: LoginRequest) => {
    try {
      const response = await apiLogin(data);
      setToken(response.token);
      setUser(response.user);
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('auth_user', JSON.stringify(response.user));
    } catch {
      // Fallback mock for development without backend running
      const mockUser: User = {
        id: '1',
        name: data.email.split('@')[0],
        email: data.email,
        role: data.email.includes('admin') ? 'ADMIN' : 'USER',
        active: true,
        createdAt: new Date().toISOString(),
      };
      const mockToken = 'mock-jwt-token-' + Date.now();
      setToken(mockToken);
      setUser(mockUser);
      localStorage.setItem('auth_token', mockToken);
      localStorage.setItem('auth_user', JSON.stringify(mockUser));
    }
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    try {
      const response = await apiRegister(data);
      setToken(response.token);
      setUser(response.user);
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('auth_user', JSON.stringify(response.user));
    } catch {
      const mockUser: User = {
        id: Date.now().toString(),
        name: data.name,
        email: data.email,
        role: 'USER',
        active: true,
        createdAt: new Date().toISOString(),
      };
      const mockToken = 'mock-jwt-token-' + Date.now();
      setToken(mockToken);
      setUser(mockUser);
      localStorage.setItem('auth_token', mockToken);
      localStorage.setItem('auth_user', JSON.stringify(mockUser));
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isAdmin: user?.role === 'ADMIN',
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
```

### 3.5 ProtectedRoute and AdminRoute Guards

- `ProtectedRoute`: Requires authentication
- `AdminRoute`: Requires ADMIN role
- Redirect to `/login` or `/` if not authorized

**Good Example - ProtectedRoute.tsx:**
```tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { ReactNode } from 'react';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

export function AdminRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isAdmin } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
```

---

## 4. Naming Conventions

### Backend (Java)

| Pattern | Convention | Example |
|---------|------------|---------|
| Package | `com.example.{service}` | `com.example.userservice` |
| Controller | `{Entity}Controller` | `UserController`, `OrderController` |
| Service Interface | `{Entity}Service` | `UserService`, `OrderService` |
| Service Implementation | `{Entity}ServiceImpl` | `UserServiceImpl`, `OrderServiceImpl` |
| Repository | `{Entity}Repository` | `UserRepository`, `OrderRepository` |
| Entity | `{Entity}` | `User`, `Order`, `Payment` |
| Request DTO | `{Action}{Entity}Request` or `{Entity}Request` | `CreateUserRequest`, `UpdateOrderRequest` |
| Response | `{}DTO` or `{Entity}Response` | `UserDTO`, `OrderResponse` |
| Config | `{Feature}Config` | `SecurityConfig`, `CorsConfig` |
| Exception | `{Type}Exception` | `UserNotFoundException`, `InvalidPaymentException` |

### Frontend (TypeScript/React)

| Pattern | Convention | Example |
|---------|------------|---------|
| Component files | PascalCase | `LoginPage.tsx`, `UsersPage.tsx` |
| Component names | PascalCase | `function LoginPage`, `export default UsersPage` |
| Hook files | camelCase with `use` prefix | `useAuth.tsx`, `useOrders.ts` |
| Type files | `index.ts` in `types/` | `types/index.ts` |
| API files | camelCase | `api.ts`, `client.ts` |
| CSS files | kebab-case | `login-page.css`, `users-page.module.css` |
| Utility files | camelCase | `formatDate.ts`, `validateEmail.ts` |

---

## 5. Good Code Examples (From Actual Codebase)

### Example 1: Backend Controller (UserController.java)

See section 2.2 for the example with:
- `Valid` on request body
- `@PreAuthorize` for role-based access
- `@Operation` for Swagger docs
- Proper logging with `@Slf4j`
- `ResponseEntity` for HTTP control

### Example 2: Service with DTO (UserServiceImpl.java + UserDTO.java)

See sections 2.3 and 2.4 for complete examples showing:
- Interface + Implementation pattern
- `@Transactional` for database operations
- `fromEntity()` static factory in DTO
- Validation and business logic
- Proper exception throwing

### Example 3: Frontend Component (LoginPage.tsx)

See section 3.1 for complete example showing:
- Functional component with hooks
- Form validation
- Error handling
- TypeScript interfaces
- useAuth hook integration

### Example 4: Axios Interceptor (api.ts)

See section 3.3 for complete example showing:
- Axios instance creation
- Request interceptor for auth token
- Response interceptor for 401 handling
- Typed API methods

### Example 5: JPA Entity (User.java, Order.java)

See section 2.6 for complete examples showing:
- Entity annotations with indexes
- Validation constraints
- Lombok annotations
- Enum types
- Timestamp auditing

---

## 6. Anti-Patterns to Avoid

### 6.1 Missing @Valid on Controller

**BAD:**
```java
@PostMapping
public ResponseEntity<UserDTO> createUser(@RequestBody CreateUserRequest request) {
    // No validation - invalid data can reach service layer
}
```

**GOOD:**
```java
@PostMapping
public ResponseEntity<UserDTO> createUser(@Valid @RequestBody CreateUserRequest) {
    // Validation happens automatically
}
```

### 6.2 Direct localStorage Access in Frontend

**BAD:**
```tsx
// Scattered localStorage access throughout components
const token = localStorage.getItem('auth_token');
const user = JSON.parse(localStorage.getItem('auth_user') || '{}');
```

**GOOD:**
```tsx
// Use useAuth context
const { token, user, login, logout } = useAuth();
```

### 6.3 Empty Catch Blocks

**BAD:**
```typescript
try {
  await apiCall();
} catch {
  // Silent failure - no error handling
}
```

**GOOD:**
```typescript
try {
  await apiCall();
} catch (error) {
  setApiError('Failed to load data. Please try again.');
  log.error('API call failed:', error);
}
```

### 6.4 Using `any` in TypeScript

**BAD:**
```typescript
function processData(data: any): any {
  return data.result;
}
```

**GOOD:**
```typescript
interface ProcessResult {
  result: string;
  timestamp: string;
}

function processData(data: ProcessInput): ProcessResult {
  return data.result;
}
```

### 6.5 Hardcoded Values Instead of Properties

**BAD:**
```java
@RestController
@RequestMapping("/api/v1/users")  // Hardcoded version
public class UserController {
    private static final int MAX_PAGE_SIZE = 100;  // Hardcoded constant
}
```

**GOOD:**
```java
// application.properties
# api.version=v1
# pagination.max-size=100

@RestController
@RequestMapping("${api.version}/users")
public class UserController {
    @Value("${pagination.max-size}")
    private int maxPageSize;
}
```

---

## 7. File Templates

### 7.1 Backend Controller Template

```java
package com.example.{service}.controller;

import com.example.{service}.dto.{Entity}Request;
import com.example.{service}.dto.{Entity}DTO;
import com.example.{service}.service.{Entity}Service;
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
@RequestMapping("/api/{endpoint}")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "{Entity} Management", description = "APIs for managing {entity}s")
public class {Entity}Controller {

    private final {Entity}Service {entity}Service;

    @PostMapping
    @Operation(summary = "Create a new {entity}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<{Entity}DTO> create{Entity}(@Valid @RequestBody {Entity}Request request) {
        log.info("POST /api/{endpoint} - Creating {entity}: {}", request.get{IdField}());
        {Entity}DTO created = {entity}Service.create{Entity}(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get {entity} by ID")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<{Entity}DTO> get{Entity}ById(
            @Parameter(description = "{Entity} ID") @PathVariable Long id) {
        log.info("GET /api/{endpoint}/{} - Retrieving {entity}", id);
        return {entity}Service.get{Entity}ById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    @Operation(summary = "Get all {entity}s")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<{Entity}DTO>> getAll{Entity}s(
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("GET /api/{endpoint} - Retrieving all {entity}s");
        return ResponseEntity.ok({entity}Service.getAll{Entity}s(pageable));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update {entity}")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public ResponseEntity<{Entity}DTO> update{Entity}(
            @Parameter(description = "{Entity} ID") @PathVariable Long id,
            @Valid @RequestBody {Entity}Request request) {
        log.info("PUT /api/{endpoint}/{} - Updating {entity}", id);
        try {
            {Entity}DTO updated = {entity}Service.update{Entity}(id, request);
            return ResponseEntity.ok(updated);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete {entity}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> delete{Entity}(
            @Parameter(description = "{Entity} ID") @PathVariable Long id) {("DELETE //{endpoint}/{} {entity);
        try {
            {entity}Service.delete{Entity}(id);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }
}
```

### 7.2 Frontend Page Component Template

```tsx
import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { {Entity} } from '../types';
import { get{Entity}s, create{Entity}, update{Entity}, delete{Entity} } from '../services/api';

interface {Entity}Form {
  // Form fields
  name: string;
  email: string;
}

const emptyForm: {Entity}Form = { name: '', email: '' };

interface FormErrors {
  name?: string;
  email?: string;
}

export default function {Entity}Page() {
  const [{Entity}s, set{Entity}s] = useState<{Entity}[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing{Entity}, setEditing{Entity}] = useState<{Entity} | null>(null);
  const [form, setForm] = useState<{Entity}Form>(emptyForm);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const fetch{Entity}s = async () => {
    setLoading(true);
    try {
      const data = await get{Entity}s();
      set{Entity}s(data.content);
    } catch {
      setError('Failed to load {entity}s');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch{Entity}s(); }, []);

  const openCreate = () => {
    setEditing{Entity}(null);
    setForm(emptyForm);
    setFormErrors({});
    setShowModal(true);
  };

  const openEdit = ({entity}: {Entity}) => {
    setEditing{Entity}({entity});
    setForm({ name: {entity}.name, email: {entity}.email });
    setFormErrors({});
    setShowModal(true);
  };

  const validate = (): boolean => {
    const errs: FormErrors = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!form.email.trim()) errs.email = 'Email is required';
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    setError('');
    try {
      if (editing{Entity}) {
        const updated = await update{Entity}(editing{Entity}.id, form);
        set{Entity}s((prev) => prev.map((u) => (u.id === editing{Entity}.id ? updated : u)));
      } else {
        const created = await create{Entity}(form);
        set{Entity}s((prev) => [...prev, created]);
      }
      setShowModal(false);
    } catch {
      setError('Failed to save {entity}');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this {entity}?')) return;
    try {
      await delete{Entity}(id);
      set{Entity}s((prev) => prev.filter((u) => u.id !== id));
    } catch {
      setError('Failed to delete {entity}');
    }
  };

  if (loading) return <div className="page-loading">Loading {entity}s...</div>;

  return (
    <div className="page">
      <div className="page-header">
        <h1>{Entity}s</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ New {Entity}</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="table-responsive">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {{Entity}s.map(({entity}) => (
              <tr key={{entity}.id}>
                <td>{{entity}.name}</td>
                <td>{{entity}.email}</td>
                <td className="actions-cell">
                  <button className="btn btn-sm btn-outline" onClick={() => openEdit({entity})}>Edit</button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete({entity}.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editing{Entity} ? 'Edit' : 'Create'} {Entity}</h2>
            <form onSubmit={handleSubmit} noValidate>
              <div className="form-group">
                <label>Name</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className={formErrors.name ? 'input-error' : ''}
                />
                {formErrors.name && <span className="field-error">{formErrors.name}</span>}
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className={formErrors.email ? 'input-error' : ''}
                />
                {formErrors.email && <span className="field-error">{formErrors.email}</span>}
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 8. Quick Commands

### Backend

```bash
# Run all services (build first)
cd test-project/backend && mvn clean install
cd test-project/backend/user-service && mvn spring-boot:run

# Run individual service
cd test-project/backend/{service} && mvn spring-boot:run

# Build all services
cd test-project/backend && mvn clean package

# Run tests with coverage (user-service, order-service only)
cd test-project/backend/user-service && mvn test jacoco:report allure:serve

# Generate JARs
cd test-project/backend && mvn package
```

### Frontend

```bash
cd test-project/frontend

# Install dependencies
npm install

# Development server (port 3000)
npm run dev

# Build for production
npm run build

# Type check
npx tsc --noEmit

# Preview production build
npm run preview
```

### Docker Compose

```bash
cd test-project

# Start all services + PostgreSQL
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Ports Summary

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend (Docker) | 8080 | http://localhost:8080 |
| user-service | 8081 | http://localhost:8081 |
| order-service | 8082 | http://localhost:8082 |
| payment-service | 8083 | http://localhost:8083 |
| weather-mcp-service | 8084 | http://localhost:8084 |
| PostgreSQL | 5432 | localhost:5432 |

---

## 9. Known Issues

| Issue | Description | Impact | Workaround |
|-------|-------------|--------|------------|
| **Spring Boot Version Mismatch** | Root POM claims 3.4.1 (Java 17), but backend services use 2.7.18 (Java 11) | Build confusion, potential compatibility issues | Use Java 11 for backend development; ignore root POM version |
| **Dockerfile Only Deploys user-service** | Dockerfile builds all 4 modules but only deploys user-service JAR | Other 3 services not available in Docker deployment | Run services individually with `mvn spring-boot:run` or fix Dockerfile |
| **Inconsistent Test Coverage** | JaCoCo/Allure only in user-service and order-service | payment-service and weather-mcp-service lack coverage reports | Add JaCoCo/Allure plugins to missing service POMs |
| **No Shared Common Module** | Each service is independent with code duplication | Maintenance overhead, inconsistent implementations | Consider creating a `common` module for shared DTOs, utilities |
| **BDD Steps Not Implemented** | `journeys/*.feature` files exist but `journeys/steps/` is empty | BDD tests cannot execute | Implement Cucumber step definitions or remove feature files |
| **CI/CD Path Mismatch** | CI expects `journeys/playwright-test` but runner is at root `run-ui-tests.js` | CI pipeline may fail | Update CI config to point to correct test runner path |
| **No Linters Configured** | Missing `.eslintrc`, `.prettierrc`, `.editorconfig` | Inconsistent code formatting | Add ESLint, Prettier, EditorConfig configurations |
| **JWT in localStorage** | Frontend stores JWT in localStorage (vulnerable to XSS) | Security risk | Consider httpOnly cookies for production |
| **No Inter-Service Circuit Breaker** | Services call each other via REST without resilience | Cascading failures possible | Add Resilience4j circuit breakers |
| **No Service Discovery** | Hardcoded service URLs | Difficult to scale, deploy | Add Eureka or Consul for service discovery |
| **No Centralized Logging** | Each service logs independently | Hard to trace requests across services | Add ELK stack or similar centralized logging |
| **Weather Service is Stateless** | No database, only external API calls | Cannot persist weather history locally | Add caching or local storage for weather data |

---

## 10. Project Structure Reference

```
test-project/
├── backend/
│   ├── pom.xml                          # Parent POM (Spring Boot 2.7.18)
│   ├── user-service/                    # Port 8081
│   │   ├── pom.xml                      # JaCoCo + Allure configured
│   │   └── src/main/java/com/example/userservice/
│   │       ├── controller/              # UserController.java
│   │       ├── service/
│   │       │   ├── UserService.java     # Interface
│   │       │   └── impl/
│   │       │       └── UserServiceImpl.java
│   │       ├── repository/              # UserRepository.java
│   │       ├── entity/                  # User.java, Role.java
│   │       ├── dto/                     # UserDTO.java, CreateUserRequest.java
│   │       └── config/                  # SecurityConfig.java
│   ├── order-service/                   # Port 8082
│   │   ├── pom.xml                      # JaCoCo + Allure configured
│   │   └── src/main/java/com/example/orderservice/
│   │       ├── entity/                  # Order.java, OrderItem.java
│   │       └── ...
│   ├── payment-service/                 # Port 8083
│   │   ├── pom.xml                      # No JaCoCo/Allure
│   │   └── src/main/java/com/example/paymentservice/
│   │       └── ...
│   └── weather-mcp-service/             # Port 8084
│       ├── pom.xml                      # No JaCoCo/Allure
│       └── src/main/java/com/example/weathermcpservice/
│           └── ...
├── frontend/
│   ├── package.json                     # React 18, Vite, TypeScript
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx                     # Entry point
│       ├── App.tsx                      # Root component + router
│       ├── pages/
│       │   ├── HomePage.tsx
│       │   ├── LoginPage.tsx
│       │   ├── SignupPage.tsx
│       │   ├── DashboardPage.tsx
│       │   ├── OrdersPage.tsx
│       │   └── WeatherPage.tsx
│       ├── components/
│       │   └── ProtectedRoute.tsx
│       ├── context/
│       │   └── AuthContext.tsx
│       ├── hooks/
│       │   └── useAuth.tsx
│       ├── services/
│       │   └── api.ts
│       └── types/
│           └── index.ts
├── journeys/
│   ├── *.feature                        # BDD feature files
│   └── steps/                           # EMPTY - step definitions missing
├── docker-compose.yaml                  # PostgreSQL + backend + frontend
└── run-ui-tests.js                      # Playwright E2E runner
```

---

## Quick Reference Card

### Backend Annotations

| Annotation | Purpose |
|------------|---------|
| `@RestController` | REST API controller |
| `@RequestMapping` | Base URL path |
| `@Valid` | Trigger JSR-303 validation |
| `@PreAuthorize` | Security role check |
| `@Service` | Business logic layer |
| `@Transactional` | Database transaction |
| `@Repository` | JPA repository interface |
| `@Entity` | JPA entity class |
| `@Data` | Lombok getter/setter/toString |
| `@Builder` | Lombok builder pattern |

### Frontend Hooks

| Hook | Purpose |
|------|---------|
| `useState` | Component state |
| `useEffect` | Side effects, data fetching |
| `useCallback` | Memoized callback |
| `useNavigate` | React Router navigation |
| `useLocation` | Current route location |
| `useAuth` | Authentication context |

### Common Patterns

| Pattern | Backend | Frontend |
|---------|---------|----------|
| Create | `POST /api/{entity}` | `api.post()` |
| Read One | `GET /api/{entity}/{id}` | `api.get()` |
| Read All | `GET /api/{entity}?page=0&size=20` | `api.get()` with pagination |
| Update | `PUT /api/{entity}/{id}` | `api.put()` |
| Delete | `DELETE /api/{entity}/{id}` | `api.delete()` |

---

**Last Updated:** 2026-07-28  
**Maintained By:** Development Team