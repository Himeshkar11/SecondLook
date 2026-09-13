import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from './AuthContext.jsx';
import PageContainer from '../components/layout/PageContainer.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Loading from '../components/common/Loading.jsx';

/**
 * Centralized Route Guard for Milestone 05.
 *
 * Rules:
 * 1. While auth/role is resolving, render a stable loading screen (no premature redirect flicker).
 * 2. If unauthenticated, redirect to /login.
 * 3. If authenticated with an unresolved/invalid role, render a safe role-unavailable notice (never default).
 * 4. If authenticated with wrong role, redirect to the user's role-appropriate home (/bidder or /officer).
 * 5. If role matches, render route children or Outlet.
 */
export default function ProtectedRoute({ allowedRoles, children }) {
  const { isAuthenticated, role, isAuthResolving, identityError, signOut } = useAuth();
  const location = useLocation();

  // 1. Authentication or application identity is still resolving
  if (isAuthResolving) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
        }}
      >
        <Loading message="Verifying security credentials &amp; role..." size="lg" />
      </div>
    );
  }

  // 2. Unauthenticated -> redirect to /login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 3. Authenticated, but role is missing, null, unknown, or identity unlinked
  if (!role) {
    return (
      <PageContainer
        title="Role Unavailable"
        subtitle="Application Identity Resolution"
        maxWidth="640px"
      >
        <EmptyState
          title="Role Not Configured or Unavailable"
          description={
            identityError ||
            'Your authenticated account is not assigned an active canonical role (BIDDER or OFFICER). Access to privileged workspaces is restricted. Please sign out and sign in with an authorized account.'
          }
          actionLabel="Sign out"
          onAction={() => signOut()}
        />
      </PageContainer>
    );
  }

  // 4. Role mismatch: wrong role navigation
  if (allowedRoles && !allowedRoles.includes(role)) {
    const roleHome = role === 'BIDDER' ? '/bidder' : '/officer';
    return <Navigate to={roleHome} replace />;
  }

  // 5. Authorized -> render content
  return children ? children : <Outlet />;
}
