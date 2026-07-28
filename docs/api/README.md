# API Documentation

Comprehensive API documentation for the microservices architecture.

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Services](#services)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)

## 🌐 Overview

This documentation covers the REST APIs for all backend services in the microservices architecture.

### Base URLs

| Service | Base URL | Port |
|---------|----------|------|
| User Service | `/api/users` | 8081 |
| Order Service | `/api/orders` | 8082 |
| Weather MCP Service | `/api/weather` | 8083 |
| Payment Service | `/api/payments` | 8084 |

### Common Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes (for POST/PUT) | `application/json` |
| `Authorization` | Yes (for authenticated endpoints) | `Bearer <JWT_TOKEN>` |

### Common Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (0-indexed, default: 0) |
| `size` | integer | Page size (default: 10-20) |
| `sort` | string | Sort field and direction (e.g., `username,asc`) |

## 🔐 Authentication

All endpoints require JWT authentication unless otherwise specified.

### Obtaining a Token

```bash
curl -X POST http://localhost:8081/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "": "Password123"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600
}
```

### Using the Token

Include the JWT token in the `Authorization` header:

```bash
curl -X GET http://localhost:8081/api/users/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| `ADMIN` | Full access to all endpoints |
| `USER` | Limited access (own resources only) |

## 📚 Services

- **[User Service API](./user-service.md)** - User management and authentication
- **[Order Service API](./order-service.md)** - Order processing and management
- **[Payment Service API](./payment-service.md)** - Payment processing and refunds
- **[Weather MCP Service API](./weather-mcp-service.md)** - Weather information and alerts

## ❌ Error Codes

### HTTP Status Codes

| Code | Description | When |
|------|-------------|------|
| `200` | OK | Successful GET/PUT request |
| `201` | Created | Successful resource creation (POST) |
| `204` | No Content | Successful deletion (DELETE) |
| `400` | Bad Request | Invalid request data or validation failure |
| `401` | Unauthorized | Missing or invalid authentication token |
| `403` | Forbidden | Insufficient permissions for the resource |
| `404` | Not Found | Resource does not exist |
| `500` | Internal Server Error | Server error |

### Error Response Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 400,
  "error": "Bad Request",
  "message": "Username is required",
  "path": "/api/users"
}
```

### Validation Error Response

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 400,
  "errors": [
    {
      "field": "username",
      "message": "Username is required"
    },
    {
      "field": "email",
      "message": "Email should be valid"
    }
  ]
}
```

## 🚦 Rate Limiting

Rate limiting is applied per user/IP address:

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Standard API | 100 requests | 1 minute |
| Bulk operations | 10 requests | 1 minute |

### Rate Limit Headers

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

---

**Last Updated:** 2024-01-15  
**API Version:** 1.0.0