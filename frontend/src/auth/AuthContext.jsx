import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../api/client.js';
import { supabase, supabaseAuthConfigured } from './supabaseClient.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [applicationUser, setApplicationUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
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
      const { data, error } = await supabase.auth.getSession();
      if (!isMounted) return;
      if (error) {
        setIdentityError('Unable to restore the authentication session.');
      }
      setSession(data?.session ?? null);
      setUser(data?.session?.user ?? null);
      setIsLoading(false);
    };

    loadSession();
    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!isMounted) return;
      setSession(nextSession ?? null);
      setUser(nextSession?.user ?? null);
      if (!nextSession) {
        setApplicationUser(null);
        setIdentityError(null);
      }
      setIsLoading(false);
    });

    return () => {
      isMounted = false;
      subscription.subscription.unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (!session?.access_token) {
      setApplicationUser(null);
      return undefined;
    }

    let isMounted = true;
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
      }
    };

    loadApplicationUser();
    return () => {
      isMounted = false;
    };
  }, [session]);

  const value = useMemo(() => ({
    session,
    user,
    applicationUser,
    isLoading,
    isConfigured: supabaseAuthConfigured,
    configurationError,
    identityError,
    async signIn(email, password) {
      if (!supabase) throw new Error('Authentication is not configured for this environment.');
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw new Error('Authentication failed. Check your email and password.');
      return data;
    },
    async signUp({ email, password, role, fullName, legalName, registrationNumber, gstNumber, panNumber }) {
      if (!supabase) throw new Error('Authentication is not configured for this environment.');
      const { data, error } = await supabase.auth.signUp({ email, password });
      if (error) {
        if (error.code === 'user_already_exists' || error.status === 422) {
          throw new Error('An account with this email already exists.');
        }
        throw new Error('Unable to create the authentication account. Please try again.');
      }

      if (!data.session) {
        throw new Error('Check your email to confirm the account. Application profile setup requires a confirmed session.');
      }

      try {
        return await apiClient('/api/v1/auth/provision', {
          method: 'POST',
          headers: { Authorization: `Bearer ${data.session.access_token}` },
          body: JSON.stringify({
            role,
            full_name: fullName,
            legal_name: legalName || null,
            registration_number: registrationNumber || null,
            gst_number: gstNumber || null,
            pan_number: panNumber || null,
          }),
        });
      } catch (provisionError) {
        await supabase.auth.signOut();
        throw new Error(provisionError.message || 'Unable to create your application profile. Please try again.');
      }
    },
    async signOut() {
      if (!supabase) return;
      const { error } = await supabase.auth.signOut();
      if (error) throw new Error('Unable to sign out. Please try again.');
    },
  }), [applicationUser, configurationError, identityError, isLoading, session, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
