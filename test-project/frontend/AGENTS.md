# FRONTEND KNOWLEDGE BASE

**Generated:** 2026-07-28  
**Type:** React 18 + TypeScript + Vite SPA

## OVERVIEW

Single-page application with 6 pages, React Router v6, axios API client, and JWT authentication.

## STRUCTURE

```
frontend/
├── package.json             # React 18, Vite, TypeScript
├── vite.config.ts     # Vite configuration
├── tsconfig.json            # TypeScript config
├── index.html               # Entry HTML
└── src/
    ├── main.tsx             # React entry point
    ├── App.tsx              # Root component + router
    ├── pages/               # 6 page components
    │   ├── HomePage.tsx
    │   ├── LoginPage.tsx
    │   ├── SignupPage.tsx
    │   ├── DashboardPage.tsx
    │   ├── OrdersPage.tsx
    │   └── WeatherPage.tsx
    ├── components/          # Reusable components
    ├── context/             # React context providers
    │   └── AuthContext.tsx  # JWT auth state
    ├── api/                 # API client
    │   └── client.ts        # Axios instance + interceptors
    ├── hooks/               # Custom hooks
    ├── types/               # TypeScript interfaces
    └── styles/              # CSS modules
```

## WHERE TO LOOK

| Concern | Location |
|---------|----------|
| Page components | `src/pages/` |
| Reusable UI | `src/components/` |
| Auth logic | `src/context/AuthContext.tsx` |
| API calls | `src/api/client.ts` |
| Type definitions | `src/types/` |
| Custom hooks | `src/hooks/` |
| Styles | `src/styles/` or `*.module.css` |

## CODE MAP

| Symbol | File | Purpose |
|--------|------|---------|
| `AuthProvider` | `src/context/AuthContext.tsx` | JWT auth state management |
| `useAuth` | `src/context/AuthContext.tsx` | Auth context hook |
| `api` | `src/api/client.ts` | Axios instance with interceptors |
| `ProtectedRoute` | `src/components/ProtectedRoute.tsx` | Auth-guarded routes |
| Pages | `src/pages/*.tsx` | 6 route components |

## CONVENTIONS

- **Components:** Functional components with hooks (no components)
- **Styling:** CSS modules (`*.module.css`)
- **Types:** TypeScript interfaces in `src/types/` or inline
- **API calls:** Axios with request/response interceptors
- **Auth:** JWT stored in localStorage, auto-injected via axios interceptor
- **Routing:** React Router v6 with nested routes

## ANTI-PATTERNS (FRONTEND)

- ⚠️ No linters configured (missing .eslintrc, .prettierrc)
- ⚠️ No .editorconfig for consistent formatting
- ⚠️ JWT in localStorage (vulnerable to XSS - httpOnly cookies preferred)
- ⚠️ No error boundary components
- ⚠️ No loading skeletons (potential layout shift)
- ⚠️ No React Query or SWR (manual fetch state management)

## UNIQUE STYLES

- Axios interceptors handle auth token injection globally
- Protected routes wrap authenticated pages
- Weather page integrates with backend MCP service
- Orders page displays user order history from order-service

## COMMANDS

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Type check
npx tsc --noEmit

# Preview production build
npm run preview
```

## NOTES

- **React version:** 18.x with concurrent features available
- **TypeScript:** Strict mode enabled
- **Vite:** Fast HMR, ESBuild-based bundling
- **API base URL:** Configured via `import.meta.env.VITE_API_URL`
- **Auth flow:** Login → JWT stored → interceptor adds `Authorization: Bearer {token}`
- **No SSR:** Pure client-side rendering