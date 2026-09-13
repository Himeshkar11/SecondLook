-- M02: application role and profile foundation.
-- This migration does not create authentication or change historical IDs.

-- Keep legacy values temporarily so existing rows can be reviewed and mapped
-- explicitly before a later milestone removes compatibility values.
ALTER TABLE users
    ALTER COLUMN role SET DEFAULT 'OFFICER';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_users_role_valid'
          AND conrelid = 'users'::regclass
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT ck_users_role_valid
            CHECK (role IN ('BIDDER', 'OFFICER', 'admin', 'procurement_officer'));
    END IF;
END $$;

-- Fail rather than silently merge or delete existing bidder profiles.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM bidders
        GROUP BY user_id
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'M02 requires manual resolution: duplicate bidder profiles reference the same user_id';
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_bidders_user_id
    ON bidders(user_id);

CREATE TABLE IF NOT EXISTS officer_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_officer_profiles_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_officer_profiles_user_id
    ON officer_profiles(user_id);