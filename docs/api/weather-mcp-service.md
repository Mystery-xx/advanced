# Weather MCP Service API

Weather information and alerts service with MCP (Model Context Protocol) integration.

**Base URL:** `http://localhost:8083/api/weather`  
**Port:** 8083

## 🔐 Authentication Requirements

| Endpoint | Required Role |
|----------|---------------|
| Get current weather | `ADMIN`, `USER` |
| Create weather alert | `ADMIN`, `USER` |
| Get user alerts | `ADMIN`, `USER` |
| Deactivate alert | `ADMIN`, `USER` |
| Get all alerts | `ADMIN` |

## 📋 Endpoints

### GET /api/weather/current/{city}

Retrieve current weather information for a city.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `city` (string) - City name

**Example (curl):**
```bash
curl -X GET http://localhost:8083/api/weather/current/London \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "city": "London",
  "country": "United Kingdom",
  "temperature": 15.5,
  "description": "Partly cloudy",
  "humidity": 72,
  "windSpeed": 12.3,
  "timestamp": 1705315800000
}
```

**Response Fields:**
- `city` (string) - City name
- `country` (string) - Country name
- `temperature` (decimal) - Temperature in Celsius
- `description` (string) - Weather description
- `humidity` (decimal) - Humidity percentage
- `windSpeed` (decimal) - Wind speed in km/h
- `timestamp` (integer) - Unix timestamp in milliseconds

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Weather service unavailable

---

### POST /api/weather/alert

Create a new weather alert for a user.

**Authentication:** `ADMIN` or `USER` role required

**Request Body:**
```json
{
  "userId": "user123",
  "city": "London",
  "temperatureThreshold": 30.0,
  "alertType": "HIGH_TEMPERATURE"
}
```

**Validation Rules:**
- `userId`: Required, non-blank
- `city`: Required, non-blank
- `temperatureThreshold`: Required, must be a valid number
- `alertType`: Optional (e.g., `HIGH_TEMPERATURE`, `LOW_TEMPERATURE`, `SEVERE_WEATHER`)

**Example (curl):**
```bash
curl -X POST http://localhost:8083/api/weather/alert \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "userId": "user123",
    "city": "London",
    "temperatureThreshold": 30.0,
    "alertType": "HIGH_TEMPERATURE"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "userId": "user123",
  "city": "London",
  "temperatureThreshold": 30.0,
  "alertType": "HIGH_TEMPERATURE",
  "active": true,
  "createdAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Validation failure
- `401 Unauthorized` - Missing or invalid token

---

### GET /api/weather/alert/user/{userId}

Retrieve all active weather alerts for a user.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `userId` (string) - User ID

**Example (curl):**
```bash
curl -X GET http://localhost:8083/api/weather/alert/user/user123 \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "userId": "user123",
    "city": "London",
    "temperatureThreshold": 30.0,
    "alertType": "HIGH_TEMPERATURE",
    "active": true,
    "createdAt": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "userId": "user123",
    "city": "Paris",
    "temperatureThreshold": 5.0,
    "alertType": "LOW_TEMPERATURE",
    "active": true,
    "createdAt": "2024-01-15T11:00:00Z"
  }
]
```

**Response (200 OK - No alerts):**
```json
[]
```

---

### POST /api/weather/alert/{id}/deactivate

Deactivate a weather alert.

**Authentication:** `ADMIN` or `USER` role required

**Path Parameters:**
- `id` (integer) - Alert ID

**Example (curl):**
```bash
curl -X POST http://localhost:8083/api/weather/alert/1/deactivate \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "userId": "user123",
  "city": "London",
  "temperatureThreshold": 30.0,
  "alertType": "HIGH_TEMPERATURE",
  "active": false,
  "createdAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Alert not found

---

### GET /api/weather/alert

Retrieve all weather alerts with pagination.

**Authentication:** `ADMIN` role required

**Query Parameters:**
- `page` (integer, default: 0) - Page number
- `size` (integer, default: 20) - Page size
- `sort` (string, optional) - Sort field and direction

**Example (curl):**
```bash
curl -X GET "http://localhost:8083/api/weather/alert?page=0&size=20&sort=createdAt,desc" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Response (200 OK):**
```json
{
  "content": [
    {
      "id": 5,
      "userId": "user789",
      "city": "New York",
      "temperatureThreshold": 35.0,
      "alertType": "HIGH_TEMPERATURE",
      "active": true,
      "createdAt": "2024-01-15T12:00:00Z"
    },
    {
      "id": 4,
      "userId": "user456",
      "city": "Tokyo",
      "temperatureThreshold": 0.0,
      "alertType": "LOW_TEMPERATURE",
      "active": true,
      "createdAt": "2024-01-15T11:30:00Z"
    },
    {
      "id": 3,
      "userId": "user456",
      "city": "Berlin",
      "temperatureThreshold": 25.0,
      "alertType": "HIGH_TEMPERATURE",
      "active": false,
      "createdAt": "2024-01-15T11:15:00Z"
    },
    {
      "id": 2,
      "userId": "user123",
      "city": "Paris",
      "temperatureThreshold": 5.0,
      "alertType": "LOW_TEMPERATURE",
      "active": true,
      "createdAt": "2024-01-15T11:00:00Z"
    },
    {
      "id": 1,
      "userId": "user123",
      "city": "London",
      "temperatureThreshold": 30.0,
      "alertType": "HIGH_TEMPERATURE",
      "active": true,
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ],
  "totalElements": 25,
  "totalPages": 2,
  "number": 0,
  "size": 20,
  "numberOfElements": 20,
  "first": true,
  "last": false,
  "empty": false
}
```

## 📊 WeatherAlertDTO Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique alert identifier |
| `userId` | string | User ID who owns the alert |
| `city` | string | City name for the alert |
| `temperatureThreshold` | decimal | Temperature threshold value |
| `alertType` | string | Alert type (see below) |
| `active` | boolean | Alert active status |
| `createdAt` | string (ISO 8601) | Creation timestamp |

### Alert Type Values

| Type | Description |
|------|-------------|
| `HIGH_TEMPERATURE` | Alert when temperature exceeds threshold |
| `LOW_TEMPERATURE` | Alert when temperature falls below threshold |
| `SEVERE_WEATHER` | Alert for severe weather conditions |

## 📊 WeatherResponse Schema

| Field | Type | Description |
|-------|------|-------------|
| `city` | string | City name |
| `country` | string | Country name |
| `temperature` | decimal | Temperature in Celsius |
| `description` | string | Weather description |
| `humidity` | decimal | Humidity percentage (0-100) |
| `windSpeed` | decimal | Wind speed in km/h |
| `timestamp` | integer | Unix timestamp in milliseconds |

## 🔒 Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `400` | `User ID is required` | Missing userId field |
| `400` | `City is required` | Missing city field |
| `400` | `Temperature threshold is required` | Missing temperatureThreshold field |
| `401` | `Unauthorized` | Missing or invalid JWT token |
| `403` | `Access Denied` | Insufficient role permissions |
| `404` | `Alert not found` | Alert ID does not exist |
| `500` | `Weather service unavailable` | External weather API error |

## 🌤️ Example Weather Data

### Sunny Day
```json
{
  "city": "Los Angeles",
  "country": "United States",
  "temperature": 28.5,
  "description": "Sunny",
  "humidity": 45,
  "windSpeed": 8.2,
  "timestamp": 1705315800000
}
```

### Rainy Day
```json
{
  "city": "Seattle",
  "country": "United States",
  "temperature": 12.3,
  "description": "Heavy rain",
  "humidity": 88,
  "windSpeed": 15.7,
  "timestamp": 1705315800000
}
```

### Snowy Day
```json
{
  "city": "Moscow",
  "country": "Russia",
  "temperature": -8.5,
  "description": "Light snow",
  "humidity": 75,
  "windSpeed": 20.1,
  "timestamp": 1705315800000
}
```

## 🚨 Example Alert Configurations

### High Temperature Alert
```json
{
  "userId": "user123",
  "city": "Phoenix",
  "temperatureThreshold": 40.0,
  "alertType": "HIGH_TEMPERATURE"
}
```

### Low Temperature Alert
```json
{
  "userId": "user456",
  "city": "Anchorage",
  "temperatureThreshold": -20.0,
  "alertType": "LOW_TEMPERATURE"
}
```

### Severe Weather Alert
```json
{
  "userId": "user789",
  "city": "Miami",
  "temperatureThreshold": 0.0,
  "alertType": "SEVERE_WEATHER"
}
```

---

**Last Updated:** 2024-01-15  
**Service Version:** 1.0.0