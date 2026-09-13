import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout.jsx';
import ProtectedRoute from './auth/ProtectedRoute.jsx';
import { useAuth } from './auth/AuthContext.jsx';
import Loading from './components/common/Loading.jsx';

import DashboardPage from './pages/DashboardPage.jsx';
import TendersPage from './pages/TendersPage.jsx';
import TenderDetailPage from './pages/TenderDetailPage.jsx';
import BiddersPage from './pages/BiddersPage.jsx';
import BidderDetailPage from './pages/BidderDetailPage.jsx';
import DocumentsPage from './pages/DocumentsPage.jsx';
import VerificationPage from './pages/VerificationPage.jsx';
import AuditPage from './pages/AuditPage.jsx';
import SettingsPage from './pages/SettingsPage.jsx';
import PlaceholderPage from './pages/PlaceholderPage.jsx';
import TenderWorkflowPage from './pages/TenderWorkflowPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import SignupPage from './pages/SignupPage.jsx';
import BidderWorkspacePage from './pages/bidder/BidderWorkspacePage.jsx';
import BidderProfilePage from './pages/bidder/BidderProfilePage.jsx';
import BidderTendersPage from './pages/bidder/BidderTendersPage.jsx';
import BidderPlaceholderPage from './pages/bidder/BidderPlaceholderPage.jsx';

const LandingPage = React.lazy(() => import('./pages/LandingPage.jsx'));

/**
 * RootRoute: Resolves initial entry point based on authentication & role state.
 * Prevents premature redirect flicker during auth resolution.
 * - Authenticated: routes directly to role workspace (/bidder or /officer)
 * - Visitor: renders the public SecondLook landing page
 */
function RootRoute() {
  const { isAuthenticated, role, isAuthResolving } = useAuth();

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

  if (!isAuthenticated) {
    return (
      <React.Suspense
        fallback={
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '60vh',
            }}
          >
            <Loading message="Loading SecondLook..." size="lg" />
          </div>
        }
      >
        <LandingPage />
      </React.Suspense>
    );
  }

  if (role === 'BIDDER') {
    return <Navigate to="/bidder" replace />;
  }

  if (role === 'OFFICER') {
    return <Navigate to="/officer" replace />;
  }

  // Authenticated without canonical role -> route to settings/role notice
  return <Navigate to="/settings" replace />;
}

/**
 * SecondLook Frontend Application Entry Route Tree — Milestone 05
 * Role-aware routing for canonical BIDDER and OFFICER roles.
 * ProtectedRoute enforces client-side role guards; backend RBAC remains authoritative.
 */
export default function App() {
  return (
    <MainLayout>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<RootRoute />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* BIDDER Protected Workspace & Namespaced Routes */}
        <Route element={<ProtectedRoute allowedRoles={['BIDDER']} />}>
          <Route path="/bidder" element={<BidderWorkspacePage />} />
          <Route path="/bidder/tenders" element={<BidderTendersPage />} />
          <Route path="/bidder/bids" element={<BidderPlaceholderPage type="bids" />} />
          <Route path="/bidder/compliance" element={<BidderPlaceholderPage type="compliance" />} />
          <Route path="/bidder/documents" element={<BidderPlaceholderPage type="documents" />} />
          <Route path="/bidder/profile" element={<BidderProfilePage />} />
        </Route>

        {/* OFFICER Protected Workspace & Namespaced Routes */}
        <Route element={<ProtectedRoute allowedRoles={['OFFICER']} />}>
          <Route path="/officer" element={<DashboardPage />} />
          <Route path="/officer/dashboard" element={<DashboardPage />} />
          <Route path="/officer/tenders" element={<TendersPage />} />
          <Route path="/officer/tenders/:id" element={<TenderDetailPage />} />
          <Route path="/officer/tenders/:id/dashboard" element={<TenderWorkflowPage />} />
          <Route path="/officer/tenders/:id/workflow" element={<TenderWorkflowPage />} />
          <Route path="/officer/bidders" element={<BiddersPage />} />
          <Route path="/officer/bidders/:id" element={<BidderDetailPage />} />
          <Route path="/officer/evaluations" element={<VerificationPage />} />
          <Route path="/officer/reviews" element={<TenderWorkflowPage />} />
          <Route path="/officer/audit" element={<AuditPage />} />
          <Route path="/officer/documents" element={<DocumentsPage />} />

          {/* Preserved existing domain routes wrapped under Officer role guard */}
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/tenders" element={<TendersPage />} />
          <Route path="/tenders/:id" element={<TenderDetailPage />} />
          <Route path="/tenders/:id/dashboard" element={<TenderWorkflowPage />} />
          <Route path="/tenders/:id/workflow" element={<TenderWorkflowPage />} />
          <Route path="/bidders" element={<BiddersPage />} />
          <Route path="/bidders/:id" element={<BidderDetailPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/verification" element={<VerificationPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Route>

        {/* Shared Authenticated Routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/settings" element={<SettingsPage />} />
        </Route>

        {/* Catch-all fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </MainLayout>
  );
}
