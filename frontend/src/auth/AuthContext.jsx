import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../api/client.js';
import { supabase, supabaseAuthConfigured } from './supabaseClient.js';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const waitForSupabaseSession = async (timeoutMs = 10000) => {
    if (!supabase) return null;
    const deadline = Date.now() + timeoutMs;

    while (Date.now() < deadline) {
      const { data } = await supabase.auth.getSession();
      if (data?.session?.access_token) {
        return data.session;
      }
      await new Promise((resolve) => setTimeout(resolve, 200));
    }

    return null;
  };

  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [applicationUser, setApplicationUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRoleLoading, setIsRoleLoading] = useState(false);
  const [configurationError, setConfigurationError] = useState(null);
  const [identityError, setIdentityError] = useState(null);

  useEffect(() => {
    if (!supabase) {
      setConfigurationError('Authentication is not configured for this environment.');
      setIsLoading(false);
      return undefined;
    }

    let isMounted = true;
    const loadSession = async () => {
      try {
        const { data, error } = await supabase.auth.getSession();
        if (!isMounted) return;
        if (error) {
          setIdentityError('Unable to restore the authentication session.');
        }
        const initialSession = data?.session ?? null;
        setSession(initialSession);
        setUser(initialSession?.user ?? null);
        if (!initialSession) {
          setIsLoading(false);
        }
      } catch {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadSession();
    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!isMounted) return;
      setSession(nextSession ?? null);
      setUser(nextSession?.user ?? null);
      if (!nextSession) {
        setApplicationUser(null);
        setIdentityError(null);
        setIsLoading(false);
        setIsRoleLoading(false);
      }
    });

    return () => {
      isMounted = false;
      subscription?.subscription?.unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (!session?.access_token) {
      setApplicationUser(null);
      setIsRoleLoading(false);
      setIsLoading(false);
      return undefined;
    }

    let isMounted = true;
    setIsRoleLoading(true);
    const loadApplicationUser = async () => {
      try {
        const identity = await apiClient('/api/v1/auth/me', {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (isMounted) {
          setApplicationUser(identity);
          setIdentityError(null);
        }
      } catch (error) {
        if (isMounted) {
          setApplicationUser(null);
          setIdentityError(error.message || 'Authenticated identity is not linked to this application.');
        }
      } finally {
        if (isMounted) {
          setIsRoleLoading(false);
          setIsLoading(false);
        }
      }
    };

    loadApplicationUser();
    return () => {
      isMounted = false;
    };
  }, [session]);

  const role = useMemo(() => {
    const rawRole = applicationUser?.role;
    if (rawRole === 'BIDDER' || rawRole === 'OFFICER') {
      return rawRole;
    }
    return null;
  }, [applicationUser]);

  const isAuthResolving = isLoading || isRoleLoading;
  const isAuthenticated = Boolean(session && user);

  const value = useMemo(() => ({
    session,
    user,
    applicationUser,
    role,
    isLoading,
    isRoleLoading,
    isAuthResolving,
    isAuthenticated,
    isConfigured: supabaseAuthConfigured,
    configurationError,
    identityError,
    async signIn(email, password) {
      if (!supabase) throw new Error('Authentication is not configured for this environment.');
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw new Error('Authentication failed. Check your email and password.');

      const activeSession = data.session ?? await waitForSupabaseSession();
      if (!activeSession) {
        throw new Error('Authentication succeeded but the session is not ready yet. Please try again.');
      }

      return { ...data, session: activeSession };
    },
    async signUp({ email, password, role: signupRole, fullName, legalName, registrationNumber, gstNumber, panNumber }) {
      if (!supabase) throw new Error('Authentication is not configured for this environment.');
      if (signupRole !== 'BIDDER' && signupRole !== 'OFFICER') {
        throw new Error('Invalid account type selected.');
      }
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            role: signupRole,
            full_name: fullName,
            legal_name: legalName || null,
            registration_number: registrationNumber || null,
            gst_number: gstNumber || null,
            pan_number: panNumber || null,
          },
        },
      });
      if (error) {
        if (error.code === 'user_already_exists' || error.status === 422) {
          throw new Error('An account with this email already exists.');
        }
        throw new Error('Unable to create the authentication account. Please try again.');
      }

      if (data.user && !data.session) {
        return {
          user: data.user,
          session: null,
          requiresEmailConfirmation: true,
        };
      }

      const activeSession = data.session ?? await waitForSupabaseSession();
      if (!activeSession) {
        throw new Error('Signup completed but no authenticated session was returned. Please try again.');
      }

      try {
        const provisionedUser = await apiClient('/api/v1/auth/provision', {
          method: 'POST',
          headers: { Authorization: `Bearer ${activeSession.access_token}` },
          body: JSON.stringify({
            role: signupRole,
            full_name: fullName,
            legal_name: legalName || null,
            registration_number: registrationNumber || null,
            gst_number: gstNumber || null,
            pan_number: panNumber || null,
          }),
        });
        return {
          ...provisionedUser,
          requiresEmailConfirmation: false,
        };
      } catch (provisionError) {
        await supabase.auth.signOut();
        throw new Error(provisionError.message || 'Unable to create your application profile. Please try again.');
      }
    },
    async signOut() {
      if (supabase) {
        try {
          await supabase.auth.signOut();
        } catch {
          // Proceed with local state cleanup
        }
      }
      setSession(null);
      setUser(null);
      setApplicationUser(null);
      setIdentityError(null);
      setIsLoading(false);
      setIsRoleLoading(false);
    },
  }), [
    applicationUser,
    configurationError,
    identityError,
    isAuthResolving,
    isAuthenticated,
    isLoading,
    isRoleLoading,
    role,
    session,
    user,
  ]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
