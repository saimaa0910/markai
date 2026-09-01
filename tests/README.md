# Global Integration & E2E Test Suite

Enterprise end-to-end and integration tests for the EAIMOS platform.

## Test Structure
- `e2e/auth.spec.ts`: Authentication, login, invalid credentials, registration validation, and session boundaries.
- `e2e/organization.spec.ts`: Organization context, IAM settings, and member management.
- `e2e/app-navigation.spec.ts`: Landing page, legal compliance, and developer documentation routes.
- `e2e/error-states.spec.ts`: Custom 404 handler, maintenance mode, and error privacy boundaries.

## Execution
Run Playwright browser tests:
```bash
npm run test:e2e
```

View interactive UI:
```bash
npm run test:e2e:ui
```
