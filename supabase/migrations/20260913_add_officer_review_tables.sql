-- Task 16: Officer Review Layer
-- Creates officer_reviews and requirement_reviews tables.

CREATE TABLE IF NOT EXISTS officer_reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id   UUID NOT NULL REFERENCES compliance_evaluations(id) ON DELETE CASCADE,
    reviewer_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    decision        VARCHAR(50) NOT NULL DEFAULT 'NO_DECISION',
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_officer_reviews_evaluation_id
    ON officer_reviews(evaluation_id);

CREATE TABLE IF NOT EXISTS requirement_reviews (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id               UUID NOT NULL REFERENCES officer_reviews(id) ON DELETE CASCADE,
    requirement_result_id   UUID NOT NULL REFERENCES requirement_evaluations(id) ON DELETE CASCADE,
    review_status           VARCHAR(50) NOT NULL DEFAULT 'NOT_REVIEWED',
    officer_comment         TEXT,
    reviewed_at             TIMESTAMPTZ,
    reviewed_by             UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_requirement_reviews_review_result
    ON requirement_reviews(review_id, requirement_result_id);
