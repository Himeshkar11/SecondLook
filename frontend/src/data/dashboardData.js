/**
 * Isolated demo data for SecondLook frontend dashboard
 * Keeps components free of hardcoded mock data for easy future API wiring.
 */

export const DASHBOARD_STATS = [
  {
    id: 'tenders',
    title: 'Active Tenders',
    value: '24',
    context: '+4 published this month',
    badgeText: 'Active',
    badgeVariant: 'info',
    icon: '📑',
  },
  {
    id: 'pending',
    title: 'Verification Pending',
    value: '08',
    context: 'Requires verification review',
    badgeText: 'Pending',
    badgeVariant: 'warning',
    icon: '⏳',
  },
  {
    id: 'compliant',
    title: 'Compliant Bidders',
    value: '71',
    context: '82% verified compliance rate',
    badgeText: 'Verified',
    badgeVariant: 'success',
    icon: '🏢',
  },
];

export const COMPLIANCE_DATA = {
  overallRate: 82,
  breakdown: [
    { label: 'GST Validations', rate: 92 },
    { label: 'PAN Registrations', rate: 96 },
    { label: 'MSME / Udyam', rate: 78 },
    { label: 'EPFO / ESIC', rate: 64 },
  ],
};

export const RISK_DATA = {
  riskLevel: 'LOW',
  score: 88,
  factors: [
    { name: 'Central Blacklist Registry', status: 'CLEAR', safe: true },
    { name: 'Debarment Index', status: 'CLEAR', safe: true },
    { name: 'Document Authenticity Check', status: 'CONFIRMED', safe: true },
    { name: 'Statutory GST Filing Status', status: 'ACTIVE', safe: true },
  ],
};

export const RECENT_TENDERS = [
  {
    id: 'GEM/2026/B/892104',
    title: 'Supply of Networking & IT Infrastructure Equipment',
    organization: 'CPCL / Ministry of Petroleum',
    bids: 12,
    status: 'ACTIVE',
    risk: 'LOW',
    closingDate: '24 Sep 2026',
  },
  {
    id: 'GEM/2026/B/891950',
    title: 'Turnkey Surveillance & Perimeter Security Systems',
    organization: 'BHEL Haridwar',
    bids: 8,
    status: 'REVIEW',
    risk: 'LOW',
    closingDate: '18 Sep 2026',
  },
  {
    id: 'GEM/2026/B/889412',
    title: 'Annual Maintenance Contract for Cloud Data Centers',
    organization: 'NIC / MeitY',
    bids: 15,
    status: 'ACTIVE',
    risk: 'MEDIUM',
    closingDate: '02 Oct 2026',
  },
  {
    id: 'GEM/2026/B/887201',
    title: 'Medical Grade Diagnostic Apparatus Procurement',
    organization: 'AIIMS New Delhi',
    bids: 5,
    status: 'PENDING',
    risk: 'LOW',
    closingDate: '28 Sep 2026',
  },
  {
    id: 'GEM/2026/B/885109',
    title: 'Diesel Generator Sets & Power Backup Infrastructure',
    organization: 'Northern Railway Zone',
    bids: 9,
    status: 'ACTIVE',
    risk: 'LOW',
    closingDate: '15 Oct 2026',
  },
];
