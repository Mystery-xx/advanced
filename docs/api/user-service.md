# User Service API

User management and authentication service.

**Base URL:** `http://localhost:8081/api/users`  
**Port:** 8081

## 🔐 Authentication Requirements

| Endpoint | Required Role |
|----------|---------------|
| Create user | `ADMIN` |
| Get user by ID | `ADMIN`, `USER` |
| Get all users | `ADMIN` |
| Get user by username | `ADMIN`, `USER` |
| Update user | `ADMIN`, `USER` |
| Delete user | `ADMIN` |
| Get users by role | `ADMIN` |
| Search users | `ADMIN` |

## 📋 Endpoints

### POST /api/users

Create a new user.

**Authentication:** `ADMIN` role required

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securePassword123",
  "role": "USER"
}
```

**Validation Rules:**
- `username`: Required, 3-50 characters
- `email`: Required, valid email format
- `password`: Required, minimum 8 characters
- `role`: Optional (default: `USER`)

**Example (curl):**
```bash
curl -X POST http://localhost:8081/api/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securePassword123",
    "role": "USER"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "USER",
  "enabled": true,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Validation failure
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions

---

### GET /api/users/{id}

Retrieve a user by their unique ID.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `id` (integer) - User ID

**Example (curl):**
```bash
curl -X GET http://localhost:8081/api/users/1 \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "USER",
  "enabled": true,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 404,
  "error": "Not Found",
  "message": "User not found with id: 1",
  "path": "/api/users/1"
}
```

---

### GET /api/users

Retrieve all users with pagination support.

**Authentication:** `ADMIN` role required

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 10) - Page size
- `sort` (string, optional) - Sort field and direction

**Example (curl):**
```bash
curl -X GET "http://localhost:8081/api/users?page=0&size=10&sort=username,asc" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "ADMIN",
      "enabled": true,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "USER",
      "enabled": true,
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    }
  ],
  "totalElements": 50,
  "totalPages": 5,
  "number": 0,
  "size": 10,
  "numberOfElements": 10,
  "first": true,
  "last": false,
  "empty": false
}
```

---

### GET /api/users/username/{username}

Retrieve a user by their username.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `username` (string) - Username

**Example (curl):**
```bash
curl -X GET http://localhost:8081/api/users/username/john_doe \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "USER",
  "enabled": true,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

---

### PUT /api/users/{id}

Update an existing user.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `id` (integer) - User ID

**Request Body:**
```json
{
  "username": "john_updated",
  "email": "john.updated@example.com",
  "password": "newSecurePassword123",
  "role": "ADMIN"
}
```

**Example (curl):**
```bash
curl -X PUT http://localhost:8081/api/users/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "username": "john_updated",
    "email": "john.updated@example.com",
    "password": "newSecurePassword123",
    "role": "ADMIN"
  }'
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "john_updated",
  "email": "john.updated@example.com",
  "role": "ADMIN",
  "enabled": true,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T11:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Validation failure
- `404 Not Found` - User not found

---

### DELETE /api/users/{id}

Delete a user by their ID.

**Authentication:** `ADMIN` role required

**Path Parameters:**
- `id` (integer) - User ID

**Example (curl):**
```bash
curl -X DELETE http://localhost:8081/api/users/1 \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Response (204 No Content):**
```
(empty body)
```

**Error Responses:**
- `404 Not Found` - User not found

---

### GET /api/users/role/{role}

Retrieve users filtered by role.

**Authentication:** `ADMIN` role required

**Path Parameters:**
- `role` (string) - Role (`USER` or `ADMIN`)

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size

**Example (curl):**
```bash
curl -X GET "http://localhost:8081/api/users/role/ADMIN?page=0&size=20" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 1,
      "username": "admin1",
      "email": "admin1@example.com",
      "role": "ADMIN",
      "enabled": true,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    },
    {
      "id": 3,
      "username": "admin2",
      "email": "admin2@example.com",
      "role": "ADMIN",
      "enabled": true,
      "createdAt": "2024-01-02T00:00:00Z",
      "updatedAt": "2024-01-02T00:00:00Z"
    }
  ],
  "totalElements": 5,
  "totalPages": 1,
  "number": 0,
  "size": 20,
  "numberOfElements": 5,
  "first": true,
  "last": true,
  "empty": false
}
```

**Error Responses:**
- `400 Bad Request` - Invalid role value

---

### GET /api/users/search

Search users by username or email.

**Authentication:** `ADMIN` role required

**Query Parameters:**
- `query` (string, required) - Search query
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size

**Example (curl):**
```bash
curl -X GET "http://localhost:8081/api/users/search?query=john&page=0&size=20" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "USER",
      "enabled": true,
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    },
    {
      "id": 5,
      "username": "johnny",
      "email": "johnny@example.com",
      "role": "USER",
      "enabled": true,
      "createdAt": "2024-01-16T10:30:00Z",
      "updatedAt": "2024-01-16T10:30:00Z"
    }
  ],
  "totalElements": 2,
  "totalPages": 1,
  "number": 0,
  "size": 20,
  "numberOfElements": 2,
  "first": true,
  "last": true,
  "empty": false
}
```

## 📊 UserDTO Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique user identifier |
| `username` | string | Username (3-50 characters) |
| `email` | string | Email address |
| `role` | string | User role (`USER` or `ADMIN`) |
| `enabled` | boolean | Account enabled status |
| `createdAt` | string (ISO 8601) | Creation timestamp |
| `updatedAt` | string (ISO 8601) | Last update timestamp |

## 🔒 Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `400` | `Username is required` | Missing username field |
| `400` | `Username must be between 3 and 50 characters` | Username length validation |
| `400` | `Email is required` | Missing email field |
| `400` | `Email should be valid` | Invalid email format |
| `400` | `Password is required` | Missing password field |
| `400` | `Password must be at least 8 characters` | Password length validation |
| `400` | `Invalid role value` | Role must be USER or ADMIN |
| `401` | `Unauthorized` | Missing or invalid JWT token |
| `403` | `Access Denied` | Insufficient role permissions |
| `404` | `User not found` | User ID does not exist |

---

**Last Updated:** 2024-01-15  
**Service Version:** 1.0.0