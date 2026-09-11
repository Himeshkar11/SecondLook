Absolutely. Since **TASK 20 is now the integrated workflow**, the next stage should be the final production-style layer: **authentication + role-based authorization + frontend access control + final UI integration**.

I would treat this as **TASK 21 — Authentication, RBAC & Frontend Finalization** rather than mixing security changes into the previous tasks.

# 🔐 TASK 21 — Role-Based Authentication, Authorization & Final Frontend Integration

## 🎯 Objective

Turn the current working prototype into a proper multi-role procurement application.

The target architecture becomes:

```text
                    ┌─────────────────┐
                    │     LOGIN       │
                    └────────┬────────┘
                             ↓
                    Authentication
                             ↓
                       User Session
                             ↓
                    Role / Permissions
                             ↓
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
        PROCUREMENT       REVIEWER       ADMIN
          OFFICER
              │              │              │
              ↓              ↓              ↓
       Allowed Actions  Allowed Actions  System Admin
```

And every protected operation must be enforced on the **backend**.

Frontend hiding a button is **not security**.

---

# 👥 STEP 1 — Define Roles

Start with only three roles.

```text
PROCUREMENT_OFFICER
REVIEWER
ADMIN
```

### PROCUREMENT_OFFICER

Can:

```text
✓ View tenders
✓ View bidders
✓ Upload tender documents
✓ Upload bidder documents
✓ Start processing
✓ View OCR
✓ View AI extraction
✓ Review requirements
✓ Approve/reject requirements
✓ Start compliance evaluation
✓ View evidence
✓ Perform officer review
✓ Record officer decision
✓ View audit trail
```

### REVIEWER

Primarily read/review access:

```text
✓ View tenders
✓ View bidders
✓ View documents
✓ View OCR
✓ View AI extraction
✓ View compliance evaluations
✓ View evidence
✓ View audit trail

✕ Approve requirements
✕ Change officer decision
✕ Modify compliance results
✕ Delete documents
```

### ADMIN

System-management access:

```text
✓ Everything required for system administration
✓ User management
✓ Role assignment
✓ Configuration
✓ View audit logs
```

Do **not** give ADMIN unrestricted database access through the frontend.

---

# 🧱 STEP 2 — Authentication Architecture

Since you're already using **Supabase**, use Supabase Authentication rather than creating your own password system.

Target:

```text
React
 ↓
Supabase Auth
 ↓
Authenticated session
 ↓
JWT
 ↓
FastAPI
 ↓
JWT validation
 ↓
User identity
 ↓
Role lookup
 ↓
Authorization
```

Do **not** store passwords in your PostgreSQL tables.

Do **not** create:

```text
users.password
users.password_hash
```

if Supabase Auth is being used.

---

# 📁 STEP 3 — Files

First inspect the current authentication/security structure.

Create only where equivalent functionality does not already exist.

```text
backend/
└── app/
    └── auth/
        ├── __init__.py
        ├── dependencies.py
        ├── schemas.py
        ├── service.py
        └── router.py

frontend/
└── src/
    ├── auth/
    │   ├── AuthProvider.jsx
    │   ├── ProtectedRoute.jsx
    │   ├── roles.js
    │   └── authService.js
    │
    ├── pages/
    │   └── LoginPage.jsx
    │
    └── components/
        └── auth/
            ├── UserMenu.jsx
            └── RoleBadge.jsx
```

If existing authentication files exist, **reuse them**.

---

# 🗄️ STEP 4 — Application User Profile

Supabase Auth owns authentication.

Your application database should store application-specific information.

Conceptually:

```text
profiles
---------
id
email
full_name
role
is_active
created_at
updated_at
```

Where:

```text
id = Supabase Auth user ID
```

Roles:

```text
PROCUREMENT_OFFICER
REVIEWER
ADMIN
```

---

# 🔒 STEP 5 — Backend Authentication Dependency

Create reusable dependencies.

Conceptually:

```python
get_current_user()
```

and:

```python
require_role(...)
```

For example:

```text
GET /tenders
        ↓
get_current_user()
        ↓
authenticated?
        ↓
YES
        ↓
return data
```

For an officer-only operation:

```text
POST /requirements/{id}/approve
        ↓
get_current_user()
        ↓
require_role(PROCUREMENT_OFFICER, ADMIN)
        ↓
allow / reject
```

---

# 🚨 STEP 6 — Authorization Must Be Backend-Enforced

This is critical.

For example:

```http
POST /api/v1/requirements/{id}/approve
```

must reject a reviewer.

Expected:

```text
REVIEWER
   ↓
403 FORBIDDEN
```

even if they manually call the API.

Similarly:

```http
PATCH /api/v1/compliance/evaluations/{id}/review/decision
```

must not be available to a read-only reviewer.

---

# 🛡️ STEP 7 — Permission Matrix

Create a centralized permission map.

Example:

| Action              | Officer | Reviewer | Admin |
| ------------------- | ------: | -------: | ----: |
| View tender         |       ✅ |        ✅ |     ✅ |
| View bidder         |       ✅ |        ✅ |     ✅ |
| Upload documents    |       ✅ |        ❌ |     ✅ |
| View OCR            |       ✅ |        ✅ |     ✅ |
| View AI extraction  |       ✅ |        ✅ |     ✅ |
| Approve requirement |       ✅ |        ❌ |     ✅ |
| Reject requirement  |       ✅ |        ❌ |     ✅ |
| Run evaluation      |       ✅ |        ❌ |     ✅ |
| View evidence       |       ✅ |        ✅ |     ✅ |
| Officer review      |       ✅ |        ❌ |     ✅ |
| Officer decision    |       ✅ |        ❌ |     ✅ |
| View audit          |       ✅ |        ✅ |     ✅ |
| User management     |       ❌ |        ❌ |     ✅ |

Keep this centralized rather than scattering role checks throughout the application.

---

# 🧪 STEP 8 — Backend Authorization Tests

These tests are mandatory.

### Unauthenticated request

```text
No JWT
 ↓
GET /api/v1/tenders
 ↓
401 Unauthorized
```

### Reviewer attempts approval

```text
REVIEWER
 ↓
POST /requirements/123/approve
 ↓
403 Forbidden
```

### Officer approval

```text
PROCUREMENT_OFFICER
 ↓
POST /requirements/123/approve
 ↓
200
```

### Reviewer attempts officer decision

```text
REVIEWER
 ↓
PATCH /compliance/.../review/decision
 ↓
403
```

### Admin

```text
ADMIN
 ↓
Allowed administrative operation
```

---

# 🔑 STEP 9 — Login Page

Create a simple login page.

```text
┌────────────────────────────────────┐
│                                    │
│       Government Procurement       │
│       Compliance Platform          │
│                                    │
│ Email                              │
│ ┌────────────────────────────────┐ │
│ │ officer@example.com            │ │
│ └────────────────────────────────┘ │
│                                    │
│ Password                           │
│ ┌────────────────────────────────┐ │
│ │ •••••••••••                    │ │
│ └────────────────────────────────┘ │
│                                    │
│          [ Sign In ]               │
│                                    │
│ Secure Government Procurement      │
│ Compliance System                 │
└────────────────────────────────────┘
```

No flashy login animation.

---

# 🧭 STEP 10 — Frontend Protected Routes

The frontend should understand:

```text
authenticated?
role?
```

For example:

```text
/tenders
```

requires authentication.

```text
/admin/users
```

requires:

```text
ADMIN
```

```text
/requirements/:id
```

may require:

```text
PROCUREMENT_OFFICER
ADMIN
```

depending on the operation.

---

# 👁️ STEP 11 — Hide Unauthorized Actions

For a reviewer:

Instead of:

```text
[Approve Requirement]
[Reject Requirement]
```

show:

```text
Requirement is available for review.
```

Or simply omit mutation buttons.

But remember:

> This is only UX. Backend authorization remains mandatory.

---

# 👤 STEP 12 — User Menu

Add a small user menu to the main layout:

```text
┌─────────────────────────────┐
│ Himesh                      │
│ PROCUREMENT OFFICER         │
│                             │
│ Profile                     │
│ Logout                      │
└─────────────────────────────┘
```

Do not expose sensitive authentication details.

---

# 🏷️ STEP 13 — Role Badge

Show:

```text
PROCUREMENT OFFICER
```

or:

```text
REVIEWER
```

or:

```text
ADMIN
```

near the user's name.

This makes the demo immediately understandable.

---

# 🧭 STEP 14 — Final Navigation

Update the sidebar/navigation based on role.

### Officer

```text
Dashboard
Tenders
Bidders
Requirements
Compliance
Documents
Audit
```

### Reviewer

```text
Dashboard
Tenders
Bidders
Compliance
Documents
Audit
```

### Admin

```text
Dashboard
Tenders
Bidders
Users
System
Audit
```

Don't create three completely different applications.

Use:

```text
same application
+
role-based capabilities
```

---

# 🎨 STEP 15 — Final Frontend Cleanup

Now that the major workflows exist, perform a **frontend consistency pass**.

Do not redesign the entire application.

Standardize:

### Buttons

```text
Primary
Secondary
Danger
Disabled
```

### Status badges

```text
PASS
FAIL
PARTIAL
NOT VERIFIED
PROCESSING
COMPLETED
AI SUGGESTED
APPROVED
REJECTED
```

### Cards

Use the same:

```text
padding
border
radius
heading hierarchy
```

throughout the application.

---

# 📱 STEP 16 — Responsive Layout

Make the existing application usable at:

```text
Desktop
Laptop
Tablet
```

At smaller widths:

```text
Sidebar
 ↓
collapsible navigation
```

Tables should horizontally scroll rather than break the entire layout.

Do not spend this task making a dedicated mobile application.

---

# ⏳ STEP 17 — Loading / Error / Empty States

Every major page should have consistent states.

### Loading

```text
Loading tender information...
```

### Empty

```text
No bidders have been added to this tender.
```

### Error

```text
Unable to load tender information.

[Retry]
```

Avoid raw:

```text
500 Internal Server Error
Traceback...
```

in the UI.

---

# 🔐 STEP 18 — Session Handling

Frontend should handle:

```text
Login
 ↓
Session
 ↓
Refresh
 ↓
Session restored
```

If the session expires:

```text
API
 ↓
401
 ↓
Clear session
 ↓
Redirect /login
```

Do not leave the application in a broken authenticated-looking state.

---

# 🚪 STEP 19 — Logout

Implement:

```text
User Menu
 ↓
Logout
 ↓
Supabase session terminated
 ↓
Local application state cleared
 ↓
/login
```

After logout:

```text
GET /tenders
```

should return:

```text
401
```

---

# 🧪 STEP 20 — Full RBAC Manual Test

Create demo users:

```text
officer@demo.local
reviewer@demo.local
admin@demo.local
```

with roles:

```text
PROCUREMENT_OFFICER
REVIEWER
ADMIN
```

### Officer

Login.

Verify:

```text
✓ Requirements
✓ Approve
✓ Reject
✓ Compliance evaluation
✓ Officer review
```

works.

---

### Reviewer

Logout.

Login as reviewer.

Verify:

```text
✓ View tender
✓ View bidder
✓ View evidence
✓ View audit

✕ Approve requirement
✕ Reject requirement
✕ Officer decision
```

Attempt the API manually.

Expected:

```text
403
```

🔥 This is especially important for your demo.

---

### Admin

Login as admin.

Verify administrative functions.

---

# 🧪 STEP 21 — Security Tests

Test:

```text
No token
Invalid token
Expired token
Valid token + wrong role
Valid token + correct role
Inactive user
```

Expected:

```text
401 → authentication problem

403 → authenticated but insufficient permission
```

Do not confuse these.

---

# 🧪 STEP 22 — Final End-to-End Test

Run the complete system as:

```text
PROCUREMENT_OFFICER
```

Workflow:

```text
Login
 ↓
Dashboard
 ↓
Open Tender
 ↓
Upload Tender Document
 ↓
OCR
 ↓
AI Requirement Extraction
 ↓
Approve Requirement
 ↓
Open Bidder
 ↓
Upload Bidder Document
 ↓
OCR
 ↓
AI Extraction
 ↓
Government Verification
 ↓
Compliance Evaluation
 ↓
Evidence
 ↓
Officer Review
 ↓
Officer Decision
 ↓
Audit Trail
```

Then logout.

Login as:

```text
REVIEWER
```

Verify the reviewer can inspect the entire result but cannot modify protected decisions.

---

# 🚨 STEP 23 — Do Not Weaken Existing Architecture

This task must **not** turn your application into:

```text
React
 ↓
Supabase directly
```

for protected business operations.

Keep:

```text
React
 ↓
FastAPI
 ↓
Authorization
 ↓
Services
 ↓
Repository
 ↓
Supabase
```

Authentication can use Supabase Auth, but business authorization remains enforced by FastAPI.

---

# 📋 COPY THIS DIRECTLY TO YOUR VIBE CODER

```text
TASK 21 — Authentication, RBAC & Final Frontend Integration.

Assume TASKS 01–20 are fully implemented and working.

OBJECTIVE:

Add secure authentication, backend-enforced role-based authorization, protected frontend routes, role-based UI capabilities, and a final frontend consistency pass.

AUTHENTICATION:

Use existing Supabase Authentication.

Do NOT create custom password storage.

Do NOT store user passwords in PostgreSQL.

Architecture:

React
↓
Supabase Auth
↓
Authenticated session/JWT
↓
FastAPI
↓
JWT validation
↓
Application profile/role
↓
Authorization
↓
Service
↓
Repository
↓
Supabase

ROLES:

PROCUREMENT_OFFICER
REVIEWER
ADMIN

PROFILE:

Use application profile data linked to Supabase Auth user ID.

Fields:

id
email
full_name
role
is_active
created_at
updated_at

BACKEND:

Create/reuse:

backend/app/auth/
    __init__.py
    dependencies.py
    schemas.py
    service.py
    router.py

Implement reusable:

get_current_user()

and centralized role/permission checking.

Authorization MUST be enforced server-side.

PERMISSIONS:

PROCUREMENT_OFFICER:

Can:
- view tenders
- view bidders
- upload tender documents
- upload bidder documents
- process documents
- review requirements
- approve/reject requirements
- run compliance evaluation
- view evidence
- perform officer review
- record officer decision
- view audit

REVIEWER:

Can:
- view tenders
- view bidders
- view documents
- view OCR
- view AI extraction
- view compliance
- view evidence
- view audit

Cannot:
- approve requirements
- reject requirements
- modify officer decision
- modify compliance results
- delete protected documents

ADMIN:

Can perform system administration and required management operations.

CENTRALIZE permissions.

Do not scatter hardcoded role checks throughout the application.

AUTHENTICATION RESPONSES:

No/invalid/expired authentication:
401 Unauthorized

Authenticated but insufficient permission:
403 Forbidden

FRONTEND:

Create/reuse:

frontend/src/auth/
    AuthProvider.jsx
    ProtectedRoute.jsx
    roles.js
    authService.js

frontend/src/pages/LoginPage.jsx

frontend/src/components/auth/
    UserMenu.jsx
    RoleBadge.jsx

Do not duplicate existing authentication functionality.

LOGIN:

Build a simple professional government-portal login page.

No flashy animations.

PROTECTED ROUTES:

Require authentication for all application pages.

Admin routes require ADMIN.

Mutation actions require appropriate role.

FRONTEND AUTHORIZATION:

Hide or disable unauthorized actions based on role.

BUT:

Frontend visibility is NOT security.

Backend must independently reject unauthorized API requests.

USER MENU:

Show:
- user name
- role
- logout

LOGOUT:

Supabase sign out
↓
clear application auth state
↓
redirect to /login

SESSION:

Restore existing session on refresh.

Handle expired session.

401 from API:
clear auth state
redirect to /login

ROLE-BASED NAVIGATION:

Officer:
Dashboard
Tenders
Bidders
Requirements
Compliance
Documents
Audit

Reviewer:
Dashboard
Tenders
Bidders
Compliance
Documents
Audit

Admin:
Dashboard
Tenders
Bidders
Users
System
Audit

Do not create separate applications for each role.

FRONTEND FINALIZATION:

Standardize:
- buttons
- status badges
- cards
- typography
- spacing
- loading states
- error states
- empty states

Use existing minimalist government design.

Status colors:

PASS = green
FAIL = red
PARTIAL = orange
NOT_VERIFIED = orange
PROCESSING = blue
COMPLETED = green
AI_SUGGESTED = orange
APPROVED = green
REJECTED = red

Responsive:
- desktop
- laptop
- tablet

Tables may horizontally scroll on narrow screens.

Do not create a separate mobile app.

SECURITY:

Do not bypass FastAPI for protected business operations.

Maintain:

React
↓
FastAPI
↓
Authorization
↓
Services
↓
Repositories
↓
Supabase

Do not expose Supabase service-role credentials to the frontend.

Do not place privileged secrets in VITE/public frontend environment variables.

TESTS:

Backend:

1. No token → 401
2. Invalid token → 401
3. Expired token → 401
4. Reviewer approval attempt → 403
5. Reviewer officer-decision attempt → 403
6. Officer approval → success
7. Officer compliance evaluation → success
8. Admin privileged operation → success
9. Inactive user → rejected
10. Correct role + correct permission → success

Frontend:

1. Unauthenticated user redirected to login
2. Session restored after refresh
3. Reviewer does not see mutation controls
4. Officer sees officer controls
5. Admin sees admin navigation
6. Logout redirects to login
7. Expired session handled correctly
8. Loading states
9. Error states
10. Empty states

MANUAL TEST:

Create demo accounts:

officer@demo.local
role = PROCUREMENT_OFFICER

reviewer@demo.local
role = REVIEWER

admin@demo.local
role = ADMIN

Login as officer.

Verify:

Requirements approval works.
Compliance evaluation works.
Officer review works.
Officer decision works.

Logout.

Login as reviewer.

Verify:

Tender viewing works.
Bidder viewing works.
Evidence viewing works.
Audit viewing works.

Verify:

Approve requirement is unavailable.
Officer decision is unavailable.

Attempt the protected API directly as reviewer.

Expected:
403 Forbidden

Logout.

Login as admin.

Verify administrative capabilities.

FINAL END-TO-END:

As PROCUREMENT_OFFICER:

Login
→ Dashboard
→ Tender
→ Tender Document
→ OCR
→ AI Requirement Extraction
→ Requirement Approval
→ Bidder
→ Bidder Document
→ OCR
→ AI Extraction
→ Government Verification
→ Compliance Evaluation
→ Evidence
→ Officer Review
→ Officer Decision
→ Audit

Logout.

Login as REVIEWER.

Verify complete result is viewable but protected mutations are forbidden.

STRICT SCOPE:

Do not rewrite:
- OCR
- AI
- Government
- Compliance
- Evidence
- Review
- Dashboard
- Requirement processing

Reuse existing implementations.

Do not introduce:
- custom password storage
- direct privileged Supabase frontend access
- automatic qualification
- automatic rejection
- automatic award
- new compliance logic

At the end report:

1. Files created
2. Files modified
3. Authentication implementation
4. Roles implemented
5. Permission matrix
6. Protected APIs
7. Protected frontend routes
8. Database changes
9. Security tests
10. Frontend tests
11. Manual RBAC results
12. Full end-to-end result

STOP AFTER TASK 21.
```

## 🏁 Result after TASK 21

Your project will finally have the complete structure:

```text
                 ┌──────────────┐
                 │    LOGIN     │
                 └──────┬───────┘
                        ↓
                  SUPABASE AUTH
                        ↓
                  USER + ROLE
                        ↓
                ┌───────┴────────┐
                │                │
             FASTAPI          REACT
                │                │
          AUTHORIZATION     ROLE-BASED UI
                │                │
                └───────┬────────┘
                        ↓
                     TENDER
                        ↓
                 DOCUMENTS
                        ↓
                       OCR
                        ↓
                  AI EXTRACTION
                        ↓
               REQUIREMENT REVIEW
                        ↓
                 OFFICER APPROVAL
                        ↓
             GOVERNMENT VERIFICATION
                        ↓
                 COMPLIANCE ENGINE
                        ↓
                    EVIDENCE
                        ↓
                 OFFICER REVIEW
                        ↓
                OFFICER DECISION
                        ↓
                 AUDIT TRAIL
```

**One particularly important thing:** don't let the vibe coder treat “role-based authentication” as merely hiding frontend buttons. The real SIH-grade security demonstration is **Reviewer manually calls `POST /approve` → FastAPI returns `403`**, while the Procurement Officer succeeds. That proves the authorization boundary actually exists.
