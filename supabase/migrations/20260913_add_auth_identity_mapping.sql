-- M03A: map Supabase Auth identities to existing application users.
-- This is additive and preserves historical application user UUIDs and foreign keys.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS auth_user_id UUID;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_auth_user_id
    ON users(auth_user_id)
    WHERE auth_user_id IS NOT NULL;

COMMENT ON COLUMN users.auth_user_id IS
    'Supabase Auth user UUID; nullable until an application user is explicitly linked.';
