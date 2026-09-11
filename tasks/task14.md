# 🚀 TASK 14 — Expand Government Verification Sources

Assuming **TASK 13 passed**, we're ready for the next major expansion.

You currently have:

```text
GST ──► Government Verification
PAN ──► Government Verification
```

Now we turn the integration layer into the **multi-source verification framework** required by the SIH problem statement.

The key idea is **not** to build 8 unrelated integrations.

Instead:

```text
                    GovernmentProvider
                           │
       ┌───────┬───────────┼───────────┬──────────┐
       ▼       ▼           ▼           ▼          ▼
      GST     PAN        UDYAM       EPFO       ESIC
       │       │           │           │          │
       └───────┴───────────┴───────────┴──────────┘
                           │
                           ▼
                  Normalized Evidence
                           │
                           ▼
                  Compliance Engine
```

For this task:

### Real/ready integrations

* GST — preserve existing implementation
* PAN — preserve existing implementation

### New integrations

* Udyam/MSME
* EPFO
* ESIC
* Startup India
* NSIC
* Make in India / Local Content
* OEM Authorization
* Blacklisting/Debarment

These should initially use **deterministic mock/demo providers**, unless you already have an authorized official API integration available.

**Do not invent government APIs or scrape government websites.**

---

# 📋 EXACT VIBE-CODING PROMPT

```text
TASK 14 — MULTI-SOURCE GOVERNMENT VERIFICATION EXPANSION

TASK 13 has been completed successfully.

The application currently supports:

Tender
    ↓
Approved Requirements
    ↓
Bidder
    ↓
Documents
    ↓
OCR
    ↓
AI Extraction
    ↓
GST/PAN Government Verification
    ↓
Evidence Resolver
    ↓
Compliance Engine
    ↓
Requirement Results
    ↓
Compliance Report

Now expand the GOVERNMENT VERIFICATION FRAMEWORK to support the additional verification sources required by the SIH problem statement.

--------------------------------------------------
CORE PURPOSE
--------------------------------------------------

The platform should support a common verification architecture for:

1. GST
2. PAN
3. UDYAM / MSME
4. EPFO
5. ESIC
6. STARTUP INDIA
7. NSIC
8. MAKE IN INDIA / LOCAL CONTENT
9. OEM AUTHORIZATION
10. BLACKLISTING / DEBARMENT

GST and PAN already exist.

Do NOT rewrite them.

For the additional sources, initially implement deterministic DEMO/MOCK providers.

The architecture must allow real authorized providers/APIs to be added later without changing:

- ComplianceEngine
- EvidenceResolver
- frontend
- tender requirement structure

--------------------------------------------------
CRITICAL RULE
--------------------------------------------------

Never invent a government API.

Never scrape government websites.

Never bypass authentication.

Never claim a mock result is a real government verification.

The UI must clearly distinguish:

DEMO / MOCK SOURCE

from:

REAL GOVERNMENT SOURCE

--------------------------------------------------
DO NOT IMPLEMENT
--------------------------------------------------

Do NOT implement:

- unauthorized government API access
- web scraping
- credential bypass
- fake government claims
- final bidder approval
- final bidder rejection
- bid award
- automatic disqualification
- procurement recommendation
- risk scoring
- new OCR system
- new AI provider
- new ComplianceEngine
- new EvidenceResolver

Reuse existing architecture.

--------------------------------------------------
STEP 1 — INSPECT EXISTING INTEGRATION FRAMEWORK
--------------------------------------------------

Inspect:

backend/app/integrations/**
backend/app/verification/**
backend/app/services/**
backend/app/models/**
backend/app/schemas/**
backend/app/api/**
backend/app/workers/**
backend/tests/**
supabase/migrations/**

Inspect:

- GovernmentProvider
- GST provider
- PAN provider
- GovernmentVerificationService
- EvidenceResolver
- ComplianceEngine
- verification database schema
- configuration system
- existing tests
- existing demo data

Reuse existing abstractions.

Do not create another provider interface.

--------------------------------------------------
STEP 2 — PROVIDER REGISTRY
--------------------------------------------------

Create or extend a centralized provider registry.

Conceptually:

GovernmentProviderRegistry

It should map:

source
    ↓
provider

Example:

GST
    → GSTProvider

PAN
    → PANProvider

UDYAM
    → DemoUdyamProvider

EPFO
    → DemoEPFOProvider

ESIC
    → DemoESICProvider

STARTUP_INDIA
    → DemoStartupIndiaProvider

NSIC
    → DemoNSICProvider

MAKE_IN_INDIA
    → DemoMakeInIndiaProvider

OEM
    → DemoOEMProvider

BLACKLIST
    → DemoBlacklistProvider

The rest of the application should ask:

get_provider(source)

rather than importing providers directly.

--------------------------------------------------
STEP 3 — COMMON RESPONSE FORMAT
--------------------------------------------------

Every provider must return the same normalized response format.

Conceptually:

{
  "source": "UDYAM",
  "provider": "demo",
  "status": "FOUND",
  "identifier": "UDYAM-XX-00-0000000",
  "data": {},
  "retrieved_at": "...",
  "is_demo": true
}

Do not allow each provider to invent a completely different response contract.

--------------------------------------------------
STEP 4 — PROVIDER CAPABILITIES
--------------------------------------------------

Providers should expose their capabilities.

Conceptually:

source
identifier_type
supported_fields
is_demo
supports_lookup

Example:

UDYAM:

identifier:
udyam_number

fields:

enterprise_name
enterprise_type
major_activity
registration_date
status

This will make future integrations easier.

--------------------------------------------------
STEP 5 — UDYAM PROVIDER
--------------------------------------------------

Implement:

DemoUdyamProvider

Use fictional data.

Example:

Identifier:

UDYAM-TN-00-0000001

Response:

{
  "udyam_number": "UDYAM-TN-00-0000001",
  "enterprise_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "enterprise_type": "Micro",
  "major_activity": "Services",
  "registration_date": "2024-04-12",
  "status": "ACTIVE",
  "state": "Tamil Nadu"
}

Also implement deterministic:

NOT_FOUND

case.

--------------------------------------------------
STEP 6 — EPFO PROVIDER
--------------------------------------------------

Implement:

DemoEPFOProvider

Use fictional data.

Example:

Identifier:

EPFO-DEMO-000001

Response:

{
  "registration_number": "EPFO-DEMO-000001",
  "establishment_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "status": "ACTIVE",
  "registration_date": "2024-01-01"
}

Support:

FOUND
NOT_FOUND
UNAVAILABLE

Do not claim this is live EPFO data.

--------------------------------------------------
STEP 7 — ESIC PROVIDER
--------------------------------------------------

Implement:

DemoESICProvider

Example:

{
  "registration_number": "ESIC-DEMO-000001",
  "establishment_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "status": "ACTIVE",
  "registration_date": "2024-01-01"
}

Support:

FOUND
NOT_FOUND
UNAVAILABLE

--------------------------------------------------
STEP 8 — STARTUP INDIA PROVIDER
--------------------------------------------------

Implement:

DemoStartupIndiaProvider

Example:

{
  "recognition_number": "DPIIT-DEMO-000001",
  "entity_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "status": "ACTIVE",
  "recognition_date": "2024-04-12"
}

Support:

FOUND
NOT_FOUND
UNAVAILABLE

Clearly label the provider:

DEMO

--------------------------------------------------
STEP 9 — NSIC PROVIDER
--------------------------------------------------

Implement:

DemoNSICProvider

Example:

{
  "certificate_number": "NSIC-DEMO-000001",
  "enterprise_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "status": "ACTIVE",
  "valid_until": "2027-04-12"
}

Support:

FOUND
NOT_FOUND
UNAVAILABLE

--------------------------------------------------
STEP 10 — MAKE IN INDIA PROVIDER
--------------------------------------------------

Implement:

DemoMakeInIndiaProvider

This source may verify local content/manufacturing information.

Example:

{
  "certificate_number": "MII-DEMO-000001",
  "entity_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "local_content_percentage": 65,
  "product_category": "Industrial Equipment",
  "country_of_origin": "India",
  "status": "VALID"
}

Do NOT assume a universal local-content threshold.

The tender requirement will specify the threshold later.

The provider only returns evidence.

--------------------------------------------------
STEP 11 — OEM AUTHORIZATION PROVIDER
--------------------------------------------------

Implement:

DemoOEMProvider

Example:

{
  "authorization_id": "OEM-DEMO-000001",
  "oem_name": "ABC ORIGINAL EQUIPMENT MANUFACTURER",
  "authorized_bidder": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "product_category": "Industrial Equipment",
  "valid_until": "2027-12-31",
  "status": "VALID"
}

This is a demonstration evidence source.

Do not represent it as a government API.

--------------------------------------------------
STEP 12 — BLACKLIST / DEBARMENT PROVIDER
--------------------------------------------------

Implement:

DemoBlacklistProvider

Example:

{
  "entity_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "listed": false,
  "status": "CLEAR",
  "checked_at": "..."
}

Negative example:

{
  "listed": true,
  "status": "LISTED"
}

Important:

This is an evidence source only.

Do not automatically reject the bidder.

--------------------------------------------------
STEP 13 — SOURCE METADATA
--------------------------------------------------

Every verification result should record:

source
provider
is_demo
identifier
status
retrieved_at

For demo providers:

is_demo = true

For real providers:

is_demo = false

This is critical for the SIH demonstration.

--------------------------------------------------
STEP 14 — CONFIGURATION
--------------------------------------------------

Providers must be selectable through configuration.

Example:

GST_PROVIDER=demo
PAN_PROVIDER=demo
UDYAM_PROVIDER=demo
EPFO_PROVIDER=demo
ESIC_PROVIDER=demo
STARTUP_INDIA_PROVIDER=demo
NSIC_PROVIDER=demo
MAKE_IN_INDIA_PROVIDER=demo
OEM_PROVIDER=demo
BLACKLIST_PROVIDER=demo

Use the existing configuration system.

Do not hard-code provider selection in business logic.

--------------------------------------------------
STEP 15 — REAL PROVIDER PLACEHOLDERS
--------------------------------------------------

For sources where no authorized API is currently configured:

Create an integration-ready provider abstraction only.

Do NOT create fake HTTP calls.

Do NOT invent URLs.

For example:

UDYAM_PROVIDER=demo

works now.

A future implementation may support:

UDYAM_PROVIDER=official

without changing:

EvidenceResolver
ComplianceEngine
API
Frontend

--------------------------------------------------
STEP 16 — VERIFICATION SERVICE
--------------------------------------------------

Extend the existing GovernmentVerificationService.

It should support:

verify(source, identifier)

rather than:

verify_gst(...)
verify_pan(...)
verify_udyam(...)
etc.

Provider-specific logic remains inside the provider.

--------------------------------------------------
STEP 17 — IDENTIFIER TYPES
--------------------------------------------------

Create a normalized identifier mapping.

Example:

GST:
GSTIN

PAN:
PAN

UDYAM:
UDYAM_NUMBER

EPFO:
EPFO_REGISTRATION

ESIC:
ESIC_REGISTRATION

STARTUP_INDIA:
DPIIT_RECOGNITION

NSIC:
NSIC_CERTIFICATE

MAKE_IN_INDIA:
MII_CERTIFICATE

OEM:
OEM_AUTHORIZATION

BLACKLIST:
ENTITY_NAME or supported identifier

Do not force identifiers where a source legitimately works through another lookup mechanism.

--------------------------------------------------
STEP 18 — NORMALIZED DATA
--------------------------------------------------

The verification service should return:

{
  "source": "UDYAM",
  "status": "FOUND",
  "identifier": "UDYAM-TN-00-0000001",
  "data": {
    "enterprise_name": "...",
    "enterprise_type": "Micro",
    "status": "ACTIVE"
  },
  "provider": "demo",
  "is_demo": true
}

The Compliance Engine must continue consuming normalized evidence.

--------------------------------------------------
STEP 19 — COMPLIANCE ENGINE COMPATIBILITY
--------------------------------------------------

Do NOT modify ComplianceEngine architecture.

It should receive evidence from all providers using the existing normalized evidence format.

Example requirement:

UDYAM status == ACTIVE

Evidence:

UDYAM provider

Result:

PASS

Another:

Enterprise type == Micro

Result:

PASS

--------------------------------------------------
STEP 20 — NEW REQUIREMENT EXAMPLES
--------------------------------------------------

Add demo requirements for:

UDYAM:

"Bidder must have an active Udyam registration."

Rule:

STATUS_EQUALS

field:

status

expected:

ACTIVE

EPFO:

"Bidder must have active EPFO registration."

Rule:

STATUS_EQUALS

field:

status

expected:

ACTIVE

ESIC:

"Bidder must have active ESIC registration."

Rule:

STATUS_EQUALS

field:

status

expected:

ACTIVE

STARTUP INDIA:

"Bidder must hold valid DPIIT recognition."

Rule:

STATUS_EQUALS

field:

status

expected:

ACTIVE

NSIC:

"Bidder must hold valid NSIC certification."

Rule:

STATUS_EQUALS

field:

status

expected:

ACTIVE

--------------------------------------------------
STEP 21 — MAKE IN INDIA RULE
--------------------------------------------------

Create a demo requirement:

"Minimum local content must be 50%."

Rule:

FIELD_GREATER_THAN_OR_EQUAL

field:

local_content_percentage

expected:

50

If the ComplianceEngine currently does not support numeric comparison:

extend it minimally.

Add:

FIELD_GREATER_THAN_OR_EQUAL

Do not create a separate rule engine.

Example:

Government/demo evidence:

65%

Tender requirement:

50%

Expected:

PASS

Evidence:

40%

Expected:

FAIL

--------------------------------------------------
STEP 22 — OEM RULE
--------------------------------------------------

Create a demo requirement:

"Bidder must be authorized by the OEM."

Rule:

FIELD_EQUALS

field:

status

expected:

VALID

The provider should return:

VALID

or:

INVALID

Expected evaluation:

PASS / FAIL

--------------------------------------------------
STEP 23 — BLACKLIST RULE
--------------------------------------------------

Create a demo requirement:

"Bidder must not be listed/debarred."

Rule:

FIELD_EQUALS

field:

status

expected:

CLEAR

If provider returns:

CLEAR

Expected:

PASS

If:

LISTED

Expected:

FAIL

Do not automatically reject bidder.

--------------------------------------------------
STEP 24 — UDYAM TEST
--------------------------------------------------

Use:

UDYAM-TN-00-0000001

Expected:

FOUND

Status:

ACTIVE

Requirement:

status == ACTIVE

Expected:

PASS

--------------------------------------------------
STEP 25 — EPFO TEST
--------------------------------------------------

Use:

EPFO-DEMO-000001

Expected:

ACTIVE

Requirement:

status == ACTIVE

Expected:

PASS

--------------------------------------------------
STEP 26 — ESIC TEST
--------------------------------------------------

Use:

ESIC-DEMO-000001

Expected:

ACTIVE

Requirement:

status == ACTIVE

Expected:

PASS

--------------------------------------------------
STEP 27 — STARTUP INDIA TEST
--------------------------------------------------

Use:

DPIIT-DEMO-000001

Expected:

ACTIVE

Requirement:

status == ACTIVE

Expected:

PASS

--------------------------------------------------
STEP 28 — NSIC TEST
--------------------------------------------------

Use:

NSIC-DEMO-000001

Expected:

ACTIVE

Requirement:

status == ACTIVE

Expected:

PASS

--------------------------------------------------
STEP 29 — MAKE IN INDIA TEST
--------------------------------------------------

Provider:

local_content_percentage = 65

Requirement:

local_content_percentage >= 50

Expected:

PASS

Change provider data:

40

Expected:

FAIL

--------------------------------------------------
STEP 30 — OEM TEST
--------------------------------------------------

Provider:

status = VALID

Requirement:

status == VALID

Expected:

PASS

Change:

status = INVALID

Expected:

FAIL

--------------------------------------------------
STEP 31 — BLACKLIST TEST
--------------------------------------------------

Provider:

status = CLEAR

Requirement:

status == CLEAR

Expected:

PASS

Change:

status = LISTED

Expected:

FAIL

Do not reject bidder automatically.

--------------------------------------------------
STEP 32 — NOT FOUND
--------------------------------------------------

Every demo provider should have a deterministic NOT_FOUND case.

Example:

UDYAM:

UDYAM-NOTFOUND-000001

Expected:

NOT_FOUND

Requirement result:

NOT_VERIFIED

unless existing rule semantics explicitly define another outcome.

--------------------------------------------------
STEP 33 — UNAVAILABLE
--------------------------------------------------

Create deterministic provider failure modes where appropriate.

Example:

UDYAM provider:

UNAVAILABLE

Expected:

verification status:

SOURCE_ERROR / UNAVAILABLE

Compliance result:

NOT_VERIFIED

Do not silently convert source failure into PASS or FAIL.

--------------------------------------------------
STEP 34 — PROVIDER REGISTRY TEST
--------------------------------------------------

Test:

get_provider("GST")
get_provider("PAN")
get_provider("UDYAM")
get_provider("EPFO")
get_provider("ESIC")
get_provider("STARTUP_INDIA")
get_provider("NSIC")
get_provider("MAKE_IN_INDIA")
get_provider("OEM")
get_provider("BLACKLIST")

All must resolve to the correct configured provider.

--------------------------------------------------
STEP 35 — UNKNOWN SOURCE
--------------------------------------------------

Attempt:

get_provider("UNKNOWN")

Expected:

controlled error.

Do not silently return a random provider.

--------------------------------------------------
STEP 36 — FRONTEND
--------------------------------------------------

Update the verification UI to display the new sources.

Example:

Government / External Verification

GST
✓ Verified

PAN
✓ Verified

UDYAM
✓ Verified
DEMO

EPFO
✓ Verified
DEMO

ESIC
✓ Verified
DEMO

Startup India
✓ Verified
DEMO

NSIC
✓ Verified
DEMO

Make in India
✓ Verified
DEMO

OEM Authorization
✓ Verified
DEMO

Blacklisting
✓ Clear
DEMO

Clearly label demo providers.

Do NOT make the interface imply these are live government API calls.

--------------------------------------------------
STEP 37 — SOURCE DETAILS
--------------------------------------------------

Clicking/opening a verification result should show:

Source
Provider
Demo/Real
Identifier
Verification timestamp
Returned fields
Verification status

Example:

Source:
UDYAM

Provider:
Demo Provider

Mode:
DEMO

Identifier:
UDYAM-TN-00-0000001

Status:
FOUND

Data:

Enterprise:
ABC TECHNOLOGIES PRIVATE LIMITED

Type:
Micro

Status:
ACTIVE

--------------------------------------------------
STEP 38 — API
--------------------------------------------------

Extend the existing government verification API.

Conceptually:

POST /api/v1/documents/{document_id}/verify

should determine the document's source/type and use the appropriate provider.

If the existing API already works this way, extend it.

Also support retrieving verification:

GET /api/v1/documents/{document_id}/verification

Do not create one unrelated API endpoint per provider unless the existing architecture requires it.

--------------------------------------------------
STEP 39 — BULK VERIFICATION
--------------------------------------------------

Do NOT implement a complex bulk verification system yet.

However, ensure the provider architecture does not prevent future parallel verification.

Independent sources should eventually be able to run concurrently.

For example:

GST
PAN
UDYAM
EPFO
ESIC

can be verified independently.

Do not implement unnecessary concurrency if the current worker architecture is synchronous.

--------------------------------------------------
STEP 40 — RATE LIMITING / SAFETY
--------------------------------------------------

Real providers may have rate limits.

Do not implement aggressive retry loops.

Respect the provider abstraction.

If rate limiting exists in the current architecture, reuse it.

Do not create infinite retries.

--------------------------------------------------
STEP 41 — DATABASE
--------------------------------------------------

Do not create separate verification tables for every provider.

Reuse the existing verification storage.

The database should store:

verification_id
bidder_id
document_id where applicable
source
provider
is_demo
identifier
status
government_data
retrieved_at
created_at
completed_at
error

Use JSONB for provider-specific returned data.

--------------------------------------------------
STEP 42 — AUDITABILITY
--------------------------------------------------

Every verification must be traceable.

Example:

Compliance Evaluation
        ↓
Requirement
        ↓
Verification ID
        ↓
Source
        ↓
Provider
        ↓
Identifier
        ↓
Retrieved Data
        ↓
Timestamp

A procurement officer must be able to see where the evidence came from.

--------------------------------------------------
STEP 43 — SECURITY
--------------------------------------------------

Verify:

- provider credentials stay backend-only
- API keys never reach React
- identifiers are validated
- bidder ownership is validated
- document ownership is validated
- tender/bidder relationships are validated
- verification cannot be created for arbitrary unrelated entities

Do not expose sensitive internal provider configuration.

--------------------------------------------------
STEP 44 — TESTING
--------------------------------------------------

Create tests for:

1. Provider registry.
2. GST provider still works.
3. PAN provider still works.
4. Udyam provider.
5. EPFO provider.
6. ESIC provider.
7. Startup India provider.
8. NSIC provider.
9. Make in India provider.
10. OEM provider.
11. Blacklist provider.
12. Provider configuration.
13. Unknown provider.
14. Udyam NOT_FOUND.
15. EPFO NOT_FOUND.
16. ESIC NOT_FOUND.
17. Startup India NOT_FOUND.
18. NSIC NOT_FOUND.
19. Make in India numeric comparison.
20. OEM authorization.
21. Blacklist clear.
22. Blacklist listed.
23. Provider unavailable.
24. Normalized response.
25. is_demo metadata.
26. Verification persistence.
27. EvidenceResolver compatibility.
28. ComplianceEngine compatibility.
29. API.
30. Security relationship validation.

No external real government API calls in tests.

--------------------------------------------------
STEP 45 — FULL DEMO TEST
--------------------------------------------------

Create/use a fictional bidder:

ABC TECHNOLOGIES PRIVATE LIMITED

Demo evidence:

GST:
ACTIVE
Tamil Nadu

PAN:
ACTIVE

UDYAM:
ACTIVE
Micro

EPFO:
ACTIVE

ESIC:
ACTIVE

Startup India:
ACTIVE

NSIC:
ACTIVE

Make in India:
65%

OEM:
VALID

Blacklist:
CLEAR

Run a compliance evaluation with approved requirements.

Expected:

All applicable demo requirements:

PASS

--------------------------------------------------
STEP 46 — FAILURE DEMO
--------------------------------------------------

Change:

Make in India:

65%
→
40%

Requirement:

minimum 50%

Expected:

Make in India requirement:

FAIL

All unrelated requirements remain unchanged.

--------------------------------------------------
STEP 47 — BLACKLIST DEMO
--------------------------------------------------

Change:

Blacklist:

CLEAR
→
LISTED

Expected:

Blacklisting requirement:

FAIL

The system must NOT automatically set:

bidder = REJECTED

--------------------------------------------------
STEP 48 — DEMO LABELING
--------------------------------------------------

Every mock result shown to the officer must clearly indicate:

DEMO

Do not use language such as:

"Government verified"

if the source is only mock data.

Use:

"Demo verification"

or:

"Demo provider"

--------------------------------------------------
STEP 49 — PRESERVE EXISTING FEATURES
--------------------------------------------------

Verify:

- Tenders
- Tender Details
- Bidders
- Bidder Details
- Document Upload
- OCR
- AI Extraction
- GST
- PAN
- Tender Requirements
- Compliance Engine
- Compliance Evaluation
- Supabase

continue working.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Allowed:

backend/app/integrations/**
backend/app/verification/**
backend/app/services/**
backend/app/models/**
backend/app/schemas/**
backend/app/api/**
backend/app/workers/**
backend/tests/**
supabase/migrations/**

Frontend:

frontend/src/pages/**
frontend/src/components/**
frontend/src/services/**

Only modify directly related files.

Do NOT rewrite:

backend/app/ocr/**

Do NOT rewrite the existing AI architecture.

Do NOT rewrite the existing ComplianceEngine.

Do NOT rewrite existing GST/PAN providers.

Do NOT create duplicate provider interfaces.

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

[ ] Existing GST provider still works
[ ] Existing PAN provider still works
[ ] Provider registry exists
[ ] UDYAM provider exists
[ ] EPFO provider exists
[ ] ESIC provider exists
[ ] Startup India provider exists
[ ] NSIC provider exists
[ ] Make in India provider exists
[ ] OEM provider exists
[ ] Blacklist provider exists
[ ] All demo providers are deterministic
[ ] All demo providers expose FOUND
[ ] All demo providers expose NOT_FOUND
[ ] Appropriate providers expose UNAVAILABLE
[ ] Normalized response exists
[ ] Provider metadata exists
[ ] is_demo is stored
[ ] Provider selection is configurable
[ ] Credentials remain backend-only
[ ] No API endpoints were invented
[ ] No scraping was implemented
[ ] UDYAM verification works
[ ] EPFO verification works
[ ] ESIC verification works
[ ] Startup India verification works
[ ] NSIC verification works
[ ] Make in India verification works
[ ] OEM verification works
[ ] Blacklist verification works
[ ] Numeric local-content rule works
[ ] ComplianceEngine consumes all normalized evidence
[ ] EvidenceResolver works with new sources
[ ] NOT_FOUND becomes NOT_VERIFIED where appropriate
[ ] SOURCE_ERROR is handled
[ ] Verification results are persisted
[ ] Audit references exist
[ ] Frontend displays sources
[ ] Demo sources are clearly labeled
[ ] Tests pass
[ ] Full demo test passes
[ ] Make in India failure test passes
[ ] Blacklist failure test passes
[ ] Existing GST/PAN tests pass
[ ] Existing OCR works
[ ] Existing AI works
[ ] Existing compliance evaluation works

--------------------------------------------------
CRITICAL PRINCIPLE
--------------------------------------------------

TASK 14 creates a COMMON MULTI-SOURCE VERIFICATION FRAMEWORK.

Do NOT create ten independent systems.

Everything must follow:

GovernmentProvider
       ↓
Normalized Verification
       ↓
EvidenceResolver
       ↓
ComplianceEngine
       ↓
Requirement Result

The Compliance Engine must not care whether evidence came from:

GST
PAN
UDYAM
EPFO
ESIC
Startup India
NSIC
Make in India
OEM
Blacklist

It only consumes normalized evidence.

--------------------------------------------------
STOP AFTER TASK 14
--------------------------------------------------

Do NOT implement TASK 15 automatically.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. Existing provider framework reused.
3. Provider registry.
4. GST status.
5. PAN status.
6. UDYAM provider.
7. EPFO provider.
8. ESIC provider.
9. Startup India provider.
10. NSIC provider.
11. Make in India provider.
12. OEM provider.
13. Blacklist provider.
14. Provider configuration.
15. Demo/real distinction.
16. Normalized response.
17. Database changes.
18. EvidenceResolver compatibility.
19. ComplianceEngine compatibility.
20. API changes.
21. Frontend changes.
22. Tests executed.
23. Test results.
24. Full demo result.
25. Make in India failure result.
26. Blacklist failure result.
27. NOT_FOUND result.
28. SOURCE_ERROR result.
29. Security validation.
30. Confirmation no automatic bidder decision exists.
31. Confirmation no government scraping/API fabrication exists.
32. Confirmation existing GST/PAN functionality remains intact.

STOP.
```

---

# 🧪 Manual testing checklist

Once the vibe coder finishes, I'd test these **in this order**.

### 1. Udyam

Use:

```text
UDYAM-TN-00-0000001
```

Expected:

```text
UDYAM
✓ FOUND
✓ ACTIVE
DEMO
```

Then run:

```text
Udyam status == ACTIVE
```

Expected:

```text
PASS
```

---

### 2. EPFO + ESIC

Use:

```text
EPFO-DEMO-000001
ESIC-DEMO-000001
```

Expected:

```text
EPFO    ACTIVE    PASS
ESIC    ACTIVE    PASS
```

---

### 3. Startup India + NSIC

Expected:

```text
Startup India    ACTIVE    PASS
NSIC             ACTIVE    PASS
```

---

### 4. Make in India

This one is particularly useful for the demo.

Government/demo evidence:

```text
Local Content = 65%
```

Tender requirement:

```text
Minimum = 50%
```

Expected:

```text
65 >= 50
     ↓
PASS
```

Change it to:

```text
40%
```

Expected:

```text
40 >= 50
     ↓
FAIL
```

---

### 5. Blacklisting

Start with:

```text
CLEAR
```

Expected:

```text
Blacklisting
✓ PASS
```

Change to:

```text
LISTED
```

Expected:

```text
Blacklisting
✗ FAIL
```

But **the bidder must not become automatically rejected**.

---

# 🔥 What TASK 14 gives you

Your system now has a scalable provider architecture:

```text
                    ┌──────────────┐
                    │   BIDDER     │
                    └──────┬───────┘
                           ↓
                    DOCUMENT EVIDENCE
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
         GST              PAN             UDYAM
          ↓                ↓                ↓
        EPFO             ESIC          STARTUP INDIA
          ↓                ↓                ↓
        NSIC          MAKE IN INDIA          OEM
          ↓                ↓                ↓
                    BLACKLIST
                           │
                           ▼
                ┌────────────────────┐
                │ NORMALIZED EVIDENCE│
                └──────────┬─────────┘
                           ↓
                  ┌─────────────────┐
                  │ EVIDENCE RESOLVER│
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ COMPLIANCE ENGINE│
                  └────────┬────────┘
                           ↓
                  REQUIREMENT RESULTS
                           ↓
                    COMPLIANCE REPORT
```

And most importantly, **you don't have to rewrite your application when you eventually get access to another official API**.

You can conceptually change:

```text
UDYAM_PROVIDER=demo
```

to:

```text
UDYAM_PROVIDER=official
```

while the rest of the pipeline remains:

```text
Provider
   ↓
Normalized Evidence
   ↓
EvidenceResolver
   ↓
ComplianceEngine
   ↓
Report
```

That is the architecture I'd want to demonstrate to the SIH judges: **mock sources today, replaceable authorized integrations tomorrow, with the compliance logic completely independent of the data source.**

**TASK 15 should now focus on the Document Intelligence/Audit Evidence layer—making every PASS/FAIL/NOT_VERIFIED result visually traceable back to the exact bidder document, OCR text, extracted field, government response, rule, and source location.**
