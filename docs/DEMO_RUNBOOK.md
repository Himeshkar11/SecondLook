# Demo Runbook

## 1. Prerequisites

- Python 3.11+ available on the local machine
- Node.js 18+ available on the local machine
- A local or configured Supabase environment for the backend identity and storage flows
- A valid `.env` file created from `.env.example` with local placeholders
- Docker optional for local environment bootstrapping

Use placeholders such as:

- `SUPABASE_URL=<YOUR_SUPABASE_URL>`
- `SUPABASE_KEY=<YOUR_SUPABASE_KEY>`
- `VITE_SUPABASE_URL=<YOUR_SUPABASE_URL>`
- `VITE_SUPABASE_PUBLISHABLE_KEY=<YOUR_SUPABASE_KEY>`
- `DATABASE_URL=<YOUR_DATABASE_URL>`

Do not place real secrets in this document.

## 2. Environment variables

The backend settings file loads the root `.env` file. Use the values from `.env.example` and replace placeholders as needed.

Key values:

- `ENVIRONMENT=development`
- `API_BASE_URL=http://localhost:8000`
- `CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173`
- `DATABASE_URL=<YOUR_DATABASE_URL>`
- `SUPABASE_URL=<YOUR_SUPABASE_URL>`
- `SUPABASE_KEY=<YOUR_SUPABASE_KEY>`
- `VITE_SUPABASE_URL=<YOUR_SUPABASE_URL>`
- `VITE_SUPABASE_PUBLISHABLE_KEY=<YOUR_SUPABASE_KEY>`

## 3. Database requirements

- Standard PostgreSQL database backing the app is expected for full live behavior.
- If database credentials are unavailable, use the repository’s demo/test behavior only.
- No database RLS is claimed for the current architecture; backend enforcement remains the source of authorization.
- Live migration verification is blocked if credentials are unavailable.

## 4. Backend startup

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then confirm:

- `http://localhost:8000/health` returns app health
- `http://localhost:8000/docs` loads OpenAPI docs

## 5. Frontend startup

From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local Vite URL shown in the terminal, usually:

- `http://localhost:5173`

## 6. Safe demo account creation

This project supports a role-based signup flow using Supabase Auth plus application provisioning. Do not use real personal identities or credentials.

Recommended demo identities:

- Bidder: `demo.bidder@example.test`
- Officer: `demo.officer@example.test`

Use synthetic business names such as:

- `Demo Bidder Pvt Ltd`
- `Demo Procurement Office`

Never use real PAN, GSTIN, Aadhaar, bank details, or real legal identifiers.

## 7. Demo tender

Use a synthetic tender with a clear demo case such as:

- `DEMO-TENDER-001`
- Title: `Demo Secure Cloud Infrastructure Procurement`

This tender must include at least three requirements such as:

1. `GST verification` — PASS
2. `PAN verification` — PASS
3. `Optional security certification` — FAIL / PARTIAL / NOT_VERIFIED

This gives a clear explanation scenario while keeping the system informational and non-automated.

## 8. Bidder workflow

1. Sign up or sign in as a bidder.
2. Navigate to bidder workspace.
3. Browse tenders.
4. Open the demo tender.
5. Create a draft bid.
6. Upload a synthetic bid document.
7. Confirm the document is attached to the correct bid.
8. Review the compliance and evidence view.
9. Observe the score and explanation output.
10. Confirm a bidder cannot access another bidder’s data.

## 9. Document workflow

- Upload only synthetic PDFs or images.
- Use a generated demo document name such as `demo_proposal.pdf`.
- The backend stores the document in private storage.
- Metadata is recorded in the database.
- Access is mediated by backend authorization.

## 10. OCR/AI workflow

- Upload a demo document.
- OCR runs and records status.
- AI extraction runs after OCR and records structured extracted fields.
- The experience must remain informational and human-controlled.

## 11. Government verification demo behavior

This project includes demo government providers. They are synthetic/mock providers and must be clearly shown as such.

Use the documented demo behavior to explain:

- Data is mock verification, not live government verification.
- Verification is evidence used by officers and bidders for review.
- Verification does not automatically qualify, reject, award, or disqualify a bidder.

## 12. Compliance evaluation

After the document and verification pipeline is complete:

- the evaluation executes
- requirement results are generated
- score is produced
- PASS / FAIL / PARTIAL / NOT_VERIFIED values are shown
- explanations are available for each requirement

The score remains informational only and must not trigger automatic award or disqualification.

## 13. Expected score and explanation

For a deterministic demo scenario, expect:

- some requirements to pass
- one requirement to be problematic
- the explanation to show the reason clearly
- the score to reflect the canonical compliance results from the evaluation engine
- no automatic procurement decision to be made

## 14. Officer workflow

1. Sign in as an officer.
2. Open the officer dashboard.
3. View the demo tender and bidder activity.
4. Review requirement results and evidence.
5. Open the requirement review flow.
6. Approve or reject the specific requirement after human review.
7. Inspect the bidder bid and compliance view.
8. Record an explicit officer decision.
9. Confirm audit events remain preserved.

## 15. What to show judges

- Landing page and role-aware flow
- bidder workspace and compliance view
- officer dashboard and tender workflow
- document upload and evidence traceability
- compliance explanation and score
- explicit officer review and decision flow
- secure RBAC behavior

## 16. Current signup behavior: email confirmation disabled

SecondLook uses normal Supabase Auth for signup and login. For the current demo/development configuration, Supabase email confirmation is intentionally disabled so that signup can return an authenticated session immediately without a verification email step.

This means:

- signup uses the standard Supabase Auth signup call;
- the app expects the returned Supabase session immediately;
- no custom email-confirmation waiting screen or confirmation-token flow is part of the product;
- authorization remains enforced independently through backend RBAC and the canonical `BIDDER`/`OFFICER` roles;
- do not claim email verification is supported when it is intentionally disabled.

If Supabase still returns HTTP 429 `over_email_send_rate_limit` after the project email confirmation setting is disabled, treat it as a provider-side blocker and stop without adding a bypass. Do not record or commit real credentials or passwords in this document or in the repository.

## 17. Known limitations

- Officer authorization is currently global for canonical `OFFICER` users because there is no officer-to-tender assignment model.
- No database RLS is claimed as the primary authorization layer.
- Browser automation and live database verification may be blocked by environment setup.
- Some demo or mock providers are intentionally synthetic and not live government APIs.
- Live signup is temporarily blocked by Supabase email rate limiting until the provider allows fresh signups again.

## 18. Troubleshooting

If the app does not start:

- confirm `.env` values are set
- confirm Python dependencies are installed
- confirm Node dependencies are installed
- confirm Supabase URL and key are valid
- confirm `DATABASE_URL` is set if the backend depends on live DB access

If signup or login fails:

- confirm the Supabase identity is active
- confirm the application user is linked to the Auth identity
- confirm the role is canonical or legacy-compatible as expected

If document processing fails:

- confirm the document type is supported
- confirm the file extension and MIME type are allowed
- confirm private storage configuration is valid

If the officer dashboard is empty:

- confirm the officer user exists and is active
- confirm the demo tender is present
- confirm the app is using the current backend with the expected DB seed/state

## 19. Reset / reseed instructions

If the project includes a supabase seed or migration reset workflow, run the project’s documented reset steps before a demo. Otherwise, reset the local database and local app state before the next live demo.

Use identity and data designed for demo purposes only.

## 20. Demo freeze status

This project is demonstration-focused and should be treated as a frozen product at the end of the milestone. Do not add new features, and do not change the architecture during a demo pass. Record any future improvement ideas in `docs/HANDOFF.md` under `FUTURE IMPROVEMENTS`.
