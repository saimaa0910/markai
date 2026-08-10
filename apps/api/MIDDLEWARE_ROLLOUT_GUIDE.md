# Sprint 8.3.1 - Middleware Rollout Guide
## Quick Reference for Applying Authentication Enforcement

**Status**: 2 of ~22 route files completed  
**Completed**: organizations.py, agents.py  
**Remaining**: See list below

---

## 🚀 Quick 2-Step Pattern

For EACH route file:

### Step 1: Add Import
Add this at the top of the file (after other `api.` imports):
```python
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1
```

### Step 2: Add to Each Protected Route
Add this as the FIRST dependency in each protected endpoint:
```python
@router.get("/endpoint")
def handler(
    _: None = Depends(enforce_all_auth_policies),  # ← ADD THIS FIRST
    current_user: User = Depends(get_current_user),
    ...
):
```

---

## ✅ Completed Files

1. ✅ `api/routes/organizations.py` - Organization management
2. ✅ `api/routes/agents.py` - Agent definitions and sessions

---

## ⏳ Remaining Files (Priority Order)

### High Priority (Core Business Logic)
3. ⏳ `api/routes/users.py` - User management
4. ⏳ `api/routes/campaigns.py` - Campaign management
5. ⏳ `api/routes/crm.py` - CRM operations
6. ⏳ `api/routes/workflows.py` - Workflow management
7. ⏳ `api/routes/integrations.py` - External integrations

### Medium Priority (Supporting Features)
8. ⏳ `api/routes/files.py` - File management
9. ⏳ `api/routes/analytics.py` - Analytics and reporting
10. ⏳ `api/routes/prompts.py` - Prompt management
11. ⏳ `api/routes/memory.py` - Memory management
12. ⏳ `api/routes/notifications.py` - Notification system

### AI/ML Routes
13. ⏳ `api/routes/ai.py` - AI operations (multiple sub-routers)
14. ⏳ `api/routes/generator.py` - Content generation
15. ⏳ `api/routes/chat.py` - Chat functionality

### Infrastructure Routes
16. ⏳ `api/routes/infrastructure.py` - Infrastructure management
17. ⏳ `api/routes/security.py` - Security operations
18. ⏳ `api/routes/observability.py` - Monitoring and observability
19. ⏳ `api/routes/sessions.py` - User sessions (existing)
20. ⏳ `api/routes/rbac.py` - Role-based access control
21. ⏳ `api/routes/audit.py` - Audit logging

---

## ❌ Routes to SKIP (Public or Special)

Do NOT add enforcement to:
* `api/routes/auth.py` - Public auth endpoints (login, register, etc.)
* Any route that has `/health` or `/docs` in the path
* Any route already handling auth internally

Specifically skip these endpoints:
* `POST /auth/login` - Must be public
* `POST /auth/register` - Must be public
* `POST /auth/logout` - Handles its own token
* `POST /auth/change-password` - Target endpoint for blocked users
* `POST /auth/password-reset/*` - Password recovery flow
* `POST /auth/email-verification/*` - Email verification
* `GET /health` - Health check
* `GET /docs` - API documentation
* `GET /openapi.json` - OpenAPI schema

---

## 📝 Examples

### Example 1: Simple GET Route
**Before**:
```python
@router.get("/campaigns")
def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    return get_campaigns(db, current_user.id)
```

**After**:
```python
@router.get("/campaigns")
def list_campaigns(
    _: None = Depends(enforce_all_auth_policies),  # ← ADDED
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    return get_campaigns(db, current_user.id)
```

### Example 2: POST Route with RoleChecker
**Before**:
```python
@router.post("/workflows")
def create_workflow(
    workflow_in: WorkflowCreate,
    membership: UserOrganization = Depends(active_member),
    db: Session = Depends(get_db),
) -> Any:
    return create(db, workflow_in, membership.organization_id)
```

**After**:
```python
@router.post("/workflows")
def create_workflow(
    workflow_in: WorkflowCreate,
    _: None = Depends(enforce_all_auth_policies),  # ← ADDED
    membership: UserOrganization = Depends(active_member),
    db: Session = Depends(get_db),
) -> Any:
    return create(db, workflow_in, membership.organization_id)
```

### Example 3: Multiple Routes in One File
```python
# Add import ONCE at top
from api.middleware.auth_enforcement import enforce_all_auth_policies

# Add to EACH protected route
@router.get("/items")
def list_items(
    _: None = Depends(enforce_all_auth_policies),
    ...
):
    pass

@router.post("/items")
def create_item(
    _: None = Depends(enforce_all_auth_policies),
    ...
):
    pass

@router.get("/items/{id}")
def get_item(
    _: None = Depends(enforce_all_auth_policies),
    ...
):
    pass
```

---

## ⚡ Bulk Rollout Strategy

### Option A: One File at a Time (Safer)
1. Pick a file from the list
2. Add import
3. Add enforcement to all protected routes
4. Test the file's endpoints
5. Commit
6. Move to next file

### Option B: Batch by Feature Area (Faster)
1. Do all CRM routes together
2. Test CRM functionality
3. Do all AI routes together
4. Test AI functionality
5. Etc.

### Option C: All at Once (Fastest, Riskiest)
1. Add import to all files
2. Add enforcement to all protected routes
3. Comprehensive testing
4. Single commit

**Recommendation**: Use **Option A** for production systems

---

## 🧪 Testing Each File

### Quick Test Pattern
```bash
# 1. Start server
python -m uvicorn api.main:app --reload

# 2. Set user to require password change
psql -d eaimos -c "UPDATE users SET change_password_required=true WHERE email='test@example.com';"

# 3. Get auth token
TOKEN=$(curl -X POST http://localhost:8000/v1/auth/login \
  -d "username=test@example.com&password=password" \
  | jq -r '.access_token')

# 4. Test the protected route (should get 403)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/YOUR_ROUTE_HERE

# Expected response:
# {"error": "password_change_required", "message": "..."}

# 5. Clear the flag
psql -d eaimos -c "UPDATE users SET change_password_required=false WHERE email='test@example.com';"

# 6. Test again (should work normally)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/YOUR_ROUTE_HERE
```

---

## 🚨 Common Issues

### Issue 1: Import Error
**Error**: `ImportError: cannot import name 'enforce_all_auth_policies'`  
**Solution**: Check that `api/middleware/auth_enforcement.py` exists

### Issue 2: Circular Import
**Error**: `ImportError: circular import`  
**Solution**: Move import inside function or use `TYPE_CHECKING`

### Issue 3: User Dependency Conflict
**Error**: `TypeError: get_current_user() got multiple values for argument 'current_user'`  
**Solution**: Enforcement must come BEFORE `current_user` dependency

### Issue 4: Route Still Accessible When Blocked
**Error**: Route doesn't return 403 when it should  
**Solution**: 
* Check enforcement is actually added to the route
* Check enforcement is BEFORE other dependencies
* Check server restarted after changes

---

## 📈 Progress Tracking

As you complete each file, update this checklist:

```markdown
## Rollout Progress

- [x] organizations.py (2 routes)
- [x] agents.py (10+ routes)
- [ ] users.py
- [ ] campaigns.py
- [ ] crm.py
- [ ] workflows.py
- [ ] integrations.py
- [ ] files.py
- [ ] analytics.py
- [ ] prompts.py
- [ ] memory.py
- [ ] notifications.py
- [ ] ai.py
- [ ] generator.py
- [ ] chat.py
- [ ] infrastructure.py
- [ ] security.py
- [ ] observability.py
- [ ] sessions.py
- [ ] rbac.py
- [ ] audit.py

**Completion**: 2/22 files (9%)
```

---

## ✅ Final Checklist

Before marking rollout complete:

- [ ] All route files updated
- [ ] No import errors
- [ ] Server starts successfully
- [ ] At least one manual test per file
- [ ] No regression in existing functionality
- [ ] Documentation updated
- [ ] Code committed and pushed

---

**Estimated Time**: 
* Per file: 5-10 minutes
* Total: 2-3 hours for all 20 remaining files

**Best Practice**: Do 5 files per day over 4 days, with testing after each batch
