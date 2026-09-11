import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout.jsx';
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

/**
 * SecondLook Frontend Application Entry Route Tree — M20
 * Full end-to-end demo portal: Dashboard → Tenders → Bidders → Documents → Verification → Results
 */
export default function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/tenders" element={<TendersPage />} />
        <Route path="/tenders/:id" element={<TenderDetailPage />} />
        <Route path="/bidders" element={<BiddersPage />} />
        <Route path="/bidders/:id" element={<BidderDetailPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/verification" element={<VerificationPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/login" element={<PlaceholderPage title="Portal Access" description="Authentication and role-based access management" />} />
      </Routes>
    </MainLayout>
  );
}

