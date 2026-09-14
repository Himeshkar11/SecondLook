-- Migration: 20260914_normalize_user_roles_and_tighten_constraint.sql
-- Closes role canonicalization drift between application layer and database layer.
-- 1. Normalizes all existing roles in public.users to canonical 'BIDDER' or 'OFFICER'.
-- 2. Tightens the ck_users_role_valid CHECK constraint to only permit ('BIDDER', 'OFFICER').
-- 3. Simplifies public.get_current_user_role() function to return UPPER(role).

-- Step 1: Normalize all existing user roles in public.users
UPDATE public.users
SET role = CASE
    WHEN UPPER(role) IN ('ADMIN', 'PROCUREMENT_OFFICER', 'OFFICER') THEN 'OFFICER'
    WHEN UPPER(role) = 'BIDDER' THEN 'BIDDER'
    ELSE 'OFFICER'
END;

-- Step 2: Tighten the ck_users_role_valid check constraint
ALTER TABLE public.users
    DROP CONSTRAINT IF EXISTS ck_users_role_valid;

ALTER TABLE public.users
    ADD CONSTRAINT ck_users_role_valid
    CHECK (role IN ('BIDDER', 'OFFICER'));

-- Step 3: Define / simplify public.get_current_user_role() for Supabase RLS policies
CREATE OR REPLACE FUNCTION public.get_current_user_role()
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT UPPER(role)
  FROM public.users
  WHERE auth_user_id = auth.uid()
  LIMIT 1;
$$;
