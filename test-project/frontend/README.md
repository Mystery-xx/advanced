# Frontend - React 18 + TypeScript + Vite

Single-page application with React 18, TypeScript, and Vite for the test-project microservices demo.

## Setup

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd test-project/frontend
npm install
```

### Environment Configuration

The application requires environment variables to configure the API base URL.

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Update the `.env` file with your environment-specific configuration:

```env
VITE_API_BASE_URL=http://localhost:8080/api
```

### Environment-Specific Configurations

The project includes pre-configured environment files for different stages:

- `.env.development` - Local development (default)
- `.env.staging` - Staging environment
- `.env.production` - Production environment

To use a specific environment:

```bash
# Development (default)
npm run dev

# Staging
npm run dev -- --mode staging

# Production build
npm run build -- --mode production
```

### Available Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_BASE_URL` | Yes | Base URL for backend API | `http://localhost:8080/api` |

## Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Type check
npx tsc --noEmit

# Lint
npm run lint

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── main.tsx              # Application entry point
├── App.tsx               # Root component with routing
├── config.ts             # Centralized configuration
├── pages/                # Page components
│   ├── HomePage.tsx
│   ├── LoginPage.tsx
│   ├── SignupPage.tsx
│   ├── DashboardPage.tsx
│   ├── OrdersPage.tsx
│   ├── UsersPage.tsx
│   ├── AdminPage.tsx
│   └── WeatherPage.tsx
├── components/           # Reusable UI components
├── hooks/                # Custom React hooks
├── services/             # API services
│   └── api.ts            # Axios-based API client
├── context/              # React Context providers
└── types/                # TypeScript type definitions
```

## API Configuration

The API client is configured in `src/config.ts` and `src/services/api.ts`:

- **Base URL**: Configured via `VITE_API_BASE_URL` environment variable
- **Timeout**: 30 seconds
- **Headers**: JSON content-type by default
- **Auth**: JWT tokens automatically injected via axios interceptors

### Centralized Config (`src/config.ts`)

```typescript
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
};

export const ENDPOINTS = {
  AUTH: { /* ... */ },
  USERS: { /* ... */ },
  ORDERS: { /* ... */ },
  WEATHER: { /* ... */ },
  ADMIN: { /* ... */ },
};
```

## Authentication

The application uses JWT-based authentication:

1. User logs in via `/login`
2. JWT token stored in `localStorage`
3. Token automatically injected in API requests via axios interceptor
4. 401 responses trigger automatic logout and redirect to login

## Features

- **React 18** with concurrent features
- **TypeScript** strict mode
- **React Router v6** for navigation
- **Axios** for HTTP requests with interceptors
- **Protected routes** for authenticated pages
- **Environment-based configuration**
- **6 pages**: Home, Login, Signup, Dashboard, Orders, Users, Admin, Weather

## Backend Integration

The frontend connects to 4 backend microservices:

| Service | Port | Purpose |
|---------|------|---------|
| user-service | 8081 | User management |
| order-service | 8082 | Order processing |
| payment-service | 8083 | Payment handling |
| weather-mcp-service | 8084 | Weather API |

When running with Docker Compose, all services are accessible via `http://localhost:8080/api`.

## Testing

```bash
# Run E2E tests from project root
cd test-project
node ../run-ui-tests.js
```

## Troubleshooting

### API Connection Issues

1. Ensure backend services are running
2. Check `VITE_API_BASE_URL` in `.env`
3. Verify CORS is configured in backend

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```