# Payment Service API

Payment processing and refunds service.

**Base URL:** `http://localhost:8084/api/payments`  
**Port:** 8084

## 🔐 Authentication Requirements

| Endpoint | Required Role |
|----------|---------------|
| Process payment | `ADMIN`, `USER` |
| Get payment by ID | `ADMIN`, `USER` |
| Get payment by transaction ID | `ADMIN`, `USER` |
| Get payments by order ID | `ADMIN`, `USER` |
| Get payments by user ID | `ADMIN`, `USER` |
| Refund payment | `ADMIN` |
| Get payments by status | `ADMIN` |

## 📋 Endpoints

### POST /api/payments

Process a new payment for an order.

**Authentication:** `ADMIN` or `USER` role required

**Request Body:**
```json
{
  "orderId": "order123",
  "userId": "user123",
  "amount": 99.99,
  "method": "CREDIT_CARD",
  "description": "Payment for order #order123"
}
```

**Validation Rules:**
- `orderId`: Required, non-blank
- `userId`: Required, non-blank
- `amount`: Required, must be greater than 0
- `method`: Optional (e.g., `CREDIT_CARD`, `DEBIT_CARD`, `PAYPAL`, `BANK_TRANSFER`)
- `description`: Optional

**Example (curl):**
```bash
curl -X POST http://localhost:8084/api/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "orderId": "order123",
    "userId": "user123",
    "amount": 99.99,
    "method": "CREDIT_CARD",
    "description": "Payment for order #order123"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "transactionId": "txn_abc123xyz789",
  "orderId": "order123",
  "userId": "user123",
  "amount": 99.99,
  "status": "SUCCESS",
  "method": "CREDIT_CARD",
  "description": "Payment for order #order123",
  "failureReason": null,
  "createdAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Validation failure
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Payment processing failed

---

### GET /api/payments/{id}

Retrieve a payment by its unique ID.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `id` (integer) - Payment ID

**Example (curl):**
```bash
curl -X GET http://localhost:8084/api/payments/1 \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "transactionId": "txn_abc123xyz789",
  "orderId": "order123",
  "userId": "user123",
  "amount": 99.99,
  "status": "SUCCESS",
  "method": "CREDIT_CARD",
  "description": "Payment for order #order123",
  "failureReason": null,
  "createdAt": "2024-01-15T10:30:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 404,
  "error": "Not Found",
  "message": "Payment not found with id: 1",
  "path": "/api/payments/1"
}
```

---

### GET /api/payments/transaction/{transactionId}

Retrieve a payment by transaction ID.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `transactionId` (string) - Transaction ID

**Example (curl):**
```bash
curl -X GET http://localhost:8084/api/payments/transaction/txn_abc123xyz789 \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "transactionId": "txn_abc123xyz789",
  "orderId": "order123",
  "userId": "user123",
  "amount": 99.99,
  "status": "SUCCESS",
  "method": "CREDIT_CARD",
  "description": "Payment for order #order123",
  "failureReason": null,
  "createdAt": "2024-01-15T10:30:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 404,
  "error": "Not Found",
  "message": "Payment not found with transactionId: txn_abc123xyz789",
  "path": "/api/payments/transaction/txn_abc123xyz789"
}
```

---

### GET /api/payments/order/{orderId}

Retrieve payments for a specific order.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `orderId` (string) - Order ID

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size
- `sort` (string, optional) - Sort field and direction

**Example (curl):**
```bash
curl -X GET "http://localhost:8084/api/payments/order/order123?page=0&size=20" \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 1,
      "transactionId": "txn_abc123xyz789",
      "orderId": "order123",
      "userId": "user123",
      "amount": 99.99,
      "status": "SUCCESS",
      "method": "CREDIT_CARD",
      "description": "Payment for order #order123",
      "failureReason": null,
      "createdAt": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "transactionId": "txn_def456uvw012",
      "orderId": "order123",
      "userId": "user123",
      "amount": 99.99,
      "status": "REFUNDED",
      "method": "CREDIT_CARD",
      "description": "Refund for order #order123",
      "failureReason": null,
      "createdAt": "2024-01-16T14:00:00Z"
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

### GET /api/payments/user/{userId}

Retrieve payments for a specific user.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `userId` (string) - User ID

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size
- `sort` (string, optional) - Sort field and direction

**Example (curl):**
```bash
curl -X GET "http://localhost:8084/api/payments/user/user123?page=0&size=20&sort=createdAt,desc" \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 5,
      "transactionId": "txn_ghi789rst345",
      "orderId": "order456",
      "userId": "user123",
      "amount": 250.00,
      "status": "SUCCESS",
      "method": "PAYPAL",
      "description": "Payment for order #order456",
      "failureReason": null,
      "createdAt": "2024-01-14T09:00:00Z"
    },
    {
      "id": 1,
      "transactionId": "txn_abc123xyz789",
      "orderId": "order123",
      "userId": "user123",
      "amount": 99.99,
      "status": "SUCCESS",
      "method": "CREDIT_CARD",
      "description": "Payment for order #order123",
      "failureReason": null,
      "createdAt": "2024-01-15T10:30:00Z"
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

---

### POST /api/payments/{id}/refund

Process a refund for a payment.

**Authentication:** `ADMIN` role required

**Path Parameters:**
- `id` (integer) - Payment ID

**Request Body:**
```json
{
  "amount": 99.99,
  "reason": "Customer requested refund"
}
```

**Validation Rules:**
- `amount`: Required, must be greater than 0
- `reason`: Optional

**Example (curl):**
```bash
curl -X POST http://localhost:8084/api/payments/1/refund \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "amount": 99.99,
    "reason": "Customer requested refund"
  }'
```

**Response (200 OK):**
```json
{
  "id": 2,
  "transactionId": "txn_refund123xyz789",
  "orderId": "order123",
  "userId": "user123",
  "amount": 99.99,
  "status": "REFUNDED",
  "method": "CREDIT_CARD",
  "description": "Refund for order #order123",
  "failureReason": null,
  "createdAt": "2024-01-16T14:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Validation failure or invalid refund amount
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Payment not found

---

### GET /api/payments/status/{status}

Retrieve payments filtered by status.

**Authentication:** `ADMIN` role required

**Path Parameters:**
- `status` (string) - Payment status

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size
- `sort` (string, optional) - Sort field and direction

**Example (curl):**
```bash
curl -X GET "http://localhost:8084/api/payments/status/SUCCESS?page=0&size=20" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 1,
      "transactionId": "txn_abc123xyz789",
      "orderId": "order123",
      "userId": "user123",
      "amount": 99.99,
      "status": "SUCCESS",
      "method": "CREDIT_CARD",
      "description": "Payment for order #order123",
      "failureReason": null,
      "createdAt": "2024-01-15T10:30:00Z"
    },
    {
      "id": 5,
      "transactionId": "txn_ghi789rst345",
      "orderId": "order456",
      "userId": "user123",
      "amount": 250.00,
      "status": "SUCCESS",
      "method": "PAYPAL",
      "description": "Payment for order #order456",
      "failureReason": null,
      "createdAt": "2024-01-14T09:00:00Z"
    }
  ],
  "totalElements": 50,
  "totalPages": 3,
  "number": 0,
  "size": 20,
  "numberOfElements": 20,
  "first": true,
  "last": false,
  "empty": false
}
```

**Error Responses:**
- `400 Bad Request` - Invalid status value

## 📊 PaymentDTO Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique payment identifier |
| `transactionId` | string | Unique transaction identifier |
| `orderId` | string | Associated order ID |
| `userId` | string | User ID who made the payment |
| `amount` | decimal | Payment amount |
| `status` | string | Payment status (see below) |
| `method` | string | Payment method (see below) |
| `description` | string | Payment description |
| `failureReason` | string | Reason for payment failure (if failed) |
| `createdAt` | string (ISO 8601) | Creation timestamp |

### Payment Status Values

| Status | Description |
|--------|-------------|
| `PENDING` | Payment initiated, awaiting processing |
| `PROCESSING` | Payment being processed |
| `SUCCESS` | Payment completed successfully |
| `FAILED` | Payment failed |
| `REFUNDED` | Payment refunded |
| `CANCELLED` | Payment cancelled |

### Payment Method Values

| Method | Description |
|--------|-------------|
| `CREDIT_CARD` | Credit card payment |
| `DEBIT_CARD` | Debit card payment |
| `PAYPAL` | PayPal payment |
| `BANK_TRANSFER` | Bank transfer payment |
| `CRYPTOCURRENCY` | Cryptocurrency payment |

## 🔒 Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `400` | `Order ID is required` | Missing orderId field |
| `400` | `User ID is required` | Missing userId field |
| `400` | `Amount is required` | Missing amount field |
| `400` | `Amount must be greater than 0` | Invalid amount |
| `400` | `Refund amount is required` | Missing refund amount |
| `400` | `Refund amount must be greater than 0` | Invalid refund amount |
| `400` | `Invalid refund amount` | Refund exceeds original payment |
| `400` | `Invalid status value` | Status not in allowed values |
| `401` | `Unauthorized` | Missing or invalid JWT token |
| `403` | `Access Denied` | Insufficient role permissions |
| `404` | `Payment not found` | Payment ID does not exist |
| `500` | `Payment processing failed` | Internal payment gateway error |

---

**Last Updated:** 2024-01-15  
**Service Version:** 1.0.0