import { Routes, Route, Link } from 'react-router-dom';

function PlaceholderPage({ title }) {
  return (
    <div>
      <h1>SecondLook</h1>
      <nav>
        <Link to="/">Home</Link> | <Link to="/login">Login</Link> | <Link to="/dashboard">Dashboard</Link> | <Link to="/tenders">Tenders</Link> | <Link to="/bidders">Bidders</Link> | <Link to="/verification">Verification</Link> | <Link to="/documents">Documents</Link> | <Link to="/audit">Audit</Link> | <Link to="/settings">Settings</Link>
      </nav>
      <h2>{title}</h2>
    </div>
  );
}

function HomePage() {
  return <PlaceholderPage title="Frontend is running" />;
}

function LoginPage() {
  return <PlaceholderPage title="Login" />;
}

function DashboardPage() {
  return <PlaceholderPage title="Dashboard" />;
}

function TendersPage() {
  return <PlaceholderPage title="Tenders" />;
}

function BiddersPage() {
  return <PlaceholderPage title="Bidders" />;
}

function VerificationPage() {
  return <PlaceholderPage title="Verification" />;
}

function DocumentsPage() {
  return <PlaceholderPage title="Documents" />;
}

function AuditPage() {
  return <PlaceholderPage title="Audit" />;
}

function SettingsPage() {
  return <PlaceholderPage title="Settings" />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/tenders" element={<TendersPage />} />
      <Route path="/bidders" element={<BiddersPage />} />
      <Route path="/verification" element={<VerificationPage />} />
      <Route path="/documents" element={<DocumentsPage />} />
      <Route path="/audit" element={<AuditPage />} />
      <Route path="/settings" element={<SettingsPage />} />
    </Routes>
  );
}
