# Order Service API

Order processing and management service.

**Base URL:** `http://localhost:8082/api/orders`  
**Port:** 8082

## 🔐 Authentication Requirements

| Endpoint | Required Role |
|----------|---------------|
| Create order | `ADMIN`, `USER` |
| Get order by ID | `ADMIN`, `USER` |
| Get all orders | `ADMIN` |
| Get orders by user ID | `ADMIN`, `USER` |
| Update order status | `ADMIN` |
| Cancel order | `ADMIN`, `USER` |
| Get orders by status | `ADMIN` |
| Get order history | `ADMIN`, `USER` |

## 📋 Endpoints

### POST /api/orders

Create a new order.

**Authentication:** `ADMIN` or `USER` role required

**Request Body:**
```json
{
  "userId": "user123",
  "totalAmount": 99.99,
  "shippingAddress": "123 Main St, City, Country",
  "items": "[{\"productId\": 1, \"quantity\": 2, \"price\": 49.99}]"
}
```

**Validation Rules:**
- `userId`: Required, non-blank
- `totalAmount`: Required, must be greater than 0
- `shippingAddress`: Optional
- `items`: Optional, JSON string representation of order items

**Example (curl):**
```bash
curl -X POST http://localhost:8082/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "userId": "user123",
    "totalAmount": 99.99,
    "shippingAddress": "123 Main St, City, Country",
    "items": "[{\"productId\": 1, \"quantity\": 2, \"price\": 49.99}]"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "userId": "user123",
  "totalAmount": 99.99,
  "status": "PENDING",
  "shippingAddress": "123 Main St, City, Country",
  "items": "[{\"productId\": 1, \"quantity\": 2, \"price\": 49.99}]",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Validation failure
- `401 Unauthorized` - Missing or invalid token

---

### GET /api/orders/{id}

Retrieve an order by its unique ID.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `id` (integer) - Order ID

**Example (curl):**
```bash
curl -X GET http://localhost:8082/api/orders/1 \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "userId": "user123",
  "totalAmount": 99.99,
  "status": "PENDING",
  "shippingAddress": "123 Main St, City, Country",
  "items": "[{\"productId\": 1, \"quantity\": 2, \"price\": 49.99}]",
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
  "message": "Order not found with id: 1",
  "path": "/api/orders/1"
}
```

---

### GET /api/orders

Retrieve all orders with pagination support.

**Authentication:** `ADMIN` role required

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size
- `sort` (string, optional) - Sort field and direction

**Example (curl):**
```bash
curl -X GET "http://localhost:8082/api/orders?page=0&size=20&sort=createdAt,desc" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 5,
      "userId": "user456",
      "totalAmount": 250.00,
      "status": "SHIPPED",
      "shippingAddress": "456 Oak Ave, Town",
      "items": "[{\"productId\": 3, \"quantity\": 1, \"price\": 250.00}]",
      "createdAt": "2024-01-14T09:00:00Z",
      "updatedAt": "2024-01-14T15:00:00Z"
    },
    {
      "id": 4,
      "userId": "user123",
      "totalAmount": 75.50,
      "status": "DELIVERED",
      "shippingAddress": "123 Main St, City",
      "items": "[{\"productId\": 2, \"quantity\": 3, \"price\": 25.17}]",
      "createdAt": "2024-01-13T14:30:00Z",
      "updatedAt": "2024-01-14T10:00:00Z"
    }
  ],
  "totalElements": 100,
  "totalPages": 5,
  "number": 0,
  "size": 20,
  "numberOfElements": 20,
  "first": true,
  "last": false,
  "empty": false
}
```

---

### GET /api/orders/user/{userId}

Retrieve orders for a specific user.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `userId` (string) - User ID

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size
- `sort` (string, optional) - Sort field and direction

**Example (curl):**
```bash
curl -X GET "http://localhost:8082/api/orders/user/user123?page=0&size=20" \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 1,
      "userId": "user123",
      "totalAmount": 99.99,
      "status": "PENDING",
      "shippingAddress": "123 Main St, City",
      "items": "[{\"productId\": 1, \"quantity\": 2, \"price\": 49.99}]",
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    },
    {
      "id": 4,
      "userId": "user123",
      "totalAmount": 75.50,
      "status": "DELIVERED",
      "shippingAddress": "123 Main St, City",
      "items": "[{\"productId\": 2, \"quantity\": 3, \"price\": 25.17}]",
      "createdAt": "2024-01-13T14:30:00Z",
      "updatedAt": "2024-01-14T10:00:00Z"
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

---

### PUT /api/orders/{id}/status

Update the status of an existing order.

**Authentication:** `ADMIN` role required

**Path Parameters:**
- `id` (integer) - Order ID

**Request Body:**
```json
{
  "status": "CONFIRMED"
}
```

**Valid Status Values:**
- `PENDING` - Order created, awaiting confirmation
- `CONFIRMED` - Order confirmed by seller
- `SHIPPED` - Order shipped to customer
- `DELIVERED` - Order delivered to customer
- `CANCELLED` - Order cancelled

**Example (curl):**
```bash
curl -X PUT http://localhost:8082/api/orders/1/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "status": "CONFIRMED"
  }'
```

**Response (200 OK):**
```json
{
  "id": 1,
  "userId": "user123",
  "totalAmount": 99.99,
  "status": "CONFIRMED",
  "shippingAddress": "123 Main St, City",
  "items": "[{\"productId\": 1, \"quantity\": 2, \"price\": 49.99}]",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T11:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid status value
- `404 Not Found` - Order not found

---

### POST /api/orders/{id}/cancel

Cancel an existing order.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `id` (integer) - Order ID

**Example (curl):**
```bash
curl -X POST http://localhost:8082/api/orders/1/cancel \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "userId": "user123",
  "totalAmount": 99.99,
  "status": "CANCELLED",
  "shippingAddress": "123 Main St, City",
  "items": "[{\"productId\": 1, \"quantity\": 2, \"price\": 49.99}]",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T12:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Order cannot be cancelled (e.g., already shipped)
- `404 Not Found` - Order not found

---

### GET /api/orders/status/{status}

Retrieve orders filtered by status.

**Authentication:** `ADMIN` role required

**Path Parameters:**
- `status` (string) - Order status

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size
- `sort` (string, optional) - Sort field and direction

**Example (curl):**
```bash
curl -X GET "http://localhost:8082/api/orders/status/PENDING?page=0&size=20" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 1,
      "userId": "user123",
      "totalAmount": 99.99,
      "status": "PENDING",
      "shippingAddress": "123 Main St, City",
      "items": "[{\"productId\": 1, \"quantity\": 2, \"price\": 49.99}]",
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    },
    {
      "id": 6,
      "userId": "user789",
      "totalAmount": 150.00,
      "status": "PENDING",
      "shippingAddress": "789 Pine Rd, Village",
      "items": "[{\"productId\": 4, \"quantity\": 1, \"price\": 150.00}]",
      "createdAt": "2024-01-15T11:00:00Z",
      "updatedAt": "2024-01-15T11:00:00Z"
    }
  ],
  "totalElements": 15,
  "totalPages": 1,
  "number": 0,
  "size": 20,
  "numberOfElements": 15,
  "first": true,
  "last": true,
  "empty": false
}
```

**Error Responses:**
- `400 Bad Request` - Invalid status value

---

### GET /api/orders/{id}/history

Retrieve the status change history for an order.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `id` (integer) - Order ID

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size

**Example (curl):**
```bash
curl -X GET "http://localhost:8082/api/orders/1/history?page=0&size=20" \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 1,
      "orderId": 1,
      "previousStatus": null,
      "newStatus": "PENDING",
      "changedAt": "2024-01-15T10:30:00Z",
      "changedBy": "user123"
    },
    {
      "id": 2,
      "orderId": 1,
      "previousStatus": "PENDING",
      "newStatus": "CONFIRMED",
      "changedAt": "2024-01-15T11:00:00Z",
      "changedBy": "admin"
    },
    {
      "id": 3,
      "orderId": 1,
      "previousStatus": "CONFIRMED",
      "newStatus": "SHIPPED",
      "changedAt": "2024-01-15T14:00:00Z",
      "changedBy": "admin"
    }
  ],
  "totalElements": 3,
  "totalPages": 1,
  "number": 0,
  "size": 20,
  "numberOfElements": 3,
  "first": true,
  "last": true,
  "empty": false
}
```

## 📊 OrderDTO Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique order identifier |
| `userId` | string | User ID who placed the order |
| `totalAmount` | decimal | Total order amount |
| `status` | string | Order status (see below) |
| `shippingAddress` | string | Shipping address |
| `items` | string | JSON string of order items |
| `createdAt` | string (ISO 8601) | Creation timestamp |
| `updatedAt` | string (ISO 8601) | Last update timestamp |

### Order Status Values

| Status | Description |
|--------|-------------|
| `PENDING` | Order created, awaiting confirmation |
| `CONFIRMED` | Order confirmed by seller |
| `SHIPPED` | Order shipped to customer |
| `DELIVERED` | Order delivered to customer |
| `CANCELLED` | Order cancelled |

## 🔒 Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `400` | `User ID is required` | Missing userId field |
| `400` | `Total amount is required` | Missing totalAmount field |
| `400` | `Total amount must be greater than 0` | Invalid amount |
| `400` | `Status is required` | Missing status field |
| `400` | `Invalid status value` | Status not in allowed values |
| `400` | `Order cannot be cancelled` | Order in non-cancellable state |
| `401` | `Unauthorized` | Missing or invalid JWT token |
| `403` | `Access Denied` | Insufficient role permissions |
| `404` | `Order not found` | Order ID does not exist |

---

**Last Updated:** 2024-01-15  
**Service Version:** 1.0.0