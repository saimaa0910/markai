# Sprint 1: Authentication, Organizations, Users, and RBAC - Implementation Plan

This plan details the implementation of user identity management, multi-tenancy, and Role-Based Access Control (RBAC).

## Proposed Changes

### 1. Database Schema
- **`users`**: Email (unique indexed), password hash, full name, and active status.
- **`organizations`**: Name and unique slug.
- **`user_organizations`**: Link table mapping users to organizations with a role enum (`OWNER`, `ADMIN`, `MEMBER`, `GUEST`).

### 2. Security and Hashing
- Direct password hashing using the `bcrypt` library (avoiding deprecated passlib wrap-checking issues under Python 3.13).
- JWT generation (access and refresh tokens).

### 3. API Endpoints (v1)
- `POST /auth/register`: Create user and instantiate a default organization.
- `POST /auth/login`: Return JWT credentials.
- `POST /auth/refresh`: Rotate active sessions.
- `GET /users/me`: Return authenticated profile.
- `POST /organizations/`: Setup new tenants.
- `GET /organizations/`: List user's tenant memberships.

### 4. Frontend Integration
- Zustand global store (`store/auth.ts`) managing active tokens and session profiles.
- Form screens: `/auth/login` and `/auth/register` using React Hook Form + Zod.
- Multi-tenant workspace dashboard `/dashboard`.
