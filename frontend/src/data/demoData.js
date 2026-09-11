/**
 * SecondLook Demo Data — M20
 *
 * Centralised deterministic demo dataset for the full end-to-end verification
 * flow: Dashboard → Tenders → Bidder → Documents → Verification → Results.
 *
 * This data is frontend-only and intentionally isolated from the backend so
 * the demo portal can function without a live database connection.
 * When real API endpoints become available, replace these imports with API calls.
 */

// ─────────────────────────────────────────────────────────────────────────────
// TENDERS
// ─────────────────────────────────────────────────────────────────────────────

export const DEMO_TENDERS = [
  {
    id: 'GEM/2026/B/892104',
    title: 'Supply of Networking & IT Infrastructure Equipment',
    organization: 'CPCL / Ministry of Petroleum',
    department: 'Information Technology Division',
    value: '₹ 4,20,00,000',
    bids: 12,
    status: 'ACTIVE',
    risk: 'LOW',
    closingDate: '24 Sep 2026',
    publishedDate: '01 Sep 2026',
    category: 'IT Equipment & Peripherals',
    description:
      'Procurement of enterprise-grade networking switches, routers, rack servers, UPS units, and structured cabling for the CPCL headquarters and four regional offices under the Digital India initiative.',
  },
  {
    id: 'GEM/2026/B/891950',
    title: 'Turnkey Surveillance & Perimeter Security Systems',
    organization: 'BHEL Haridwar',
    department: 'Security & Facilities',
    value: '₹ 2,85,00,000',
    bids: 8,
    status: 'REVIEW',
    risk: 'LOW',
    closingDate: '18 Sep 2026',
    publishedDate: '28 Aug 2026',
    category: 'Security Systems',
    description:
      'Design, supply, installation, commissioning, and AMC of a CCTV-based video surveillance system across the BHEL Haridwar manufacturing campus including control room integration.',
  },
  {
    id: 'GEM/2026/B/889412',
    title: 'Annual Maintenance Contract for Cloud Data Centers',
    organization: 'NIC / MeitY',
    department: 'Cloud & Data Infrastructure',
    value: '₹ 9,10,00,000',
    bids: 15,
    status: 'ACTIVE',
    risk: 'MEDIUM',
    closingDate: '02 Oct 2026',
    publishedDate: '20 Aug 2026',
    category: 'IT Services & AMC',
    description:
      'Comprehensive annual maintenance, monitoring, and SLA-backed operations for NIC National Data Centre facilities at Delhi, Pune, and Hyderabad.',
  },
  {
    id: 'GEM/2026/B/887201',
    title: 'Medical Grade Diagnostic Apparatus Procurement',
    organization: 'AIIMS New Delhi',
    department: 'Medical Equipment Procurement Cell',
    value: '₹ 6,50,00,000',
    bids: 5,
    status: 'PENDING',
    risk: 'LOW',
    closingDate: '28 Sep 2026',
    publishedDate: '25 Aug 2026',
    category: 'Medical Devices',
    description:
      'Procurement of high-resolution MRI scanners, CT systems, digital X-ray units, and associated PACS software for AIIMS New Delhi trauma and diagnostic centres.',
  },
  {
    id: 'GEM/2026/B/885109',
    title: 'Diesel Generator Sets & Power Backup Infrastructure',
    organization: 'Northern Railway Zone',
    department: 'Electrical Engineering Department',
    value: '₹ 1,75,00,000',
    bids: 9,
    status: 'ACTIVE',
    risk: 'LOW',
    closingDate: '15 Oct 2026',
    publishedDate: '02 Sep 2026',
    category: 'Electrical Equipment',
    description:
      'Supply and commissioning of 125 kVA and 250 kVA DG sets with synchronisation panels and AMF control systems at twelve Northern Railway divisional headquarters.',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// BIDDERS
// Maps bidder objects; each bidder references the tender ID they belong to.
// ─────────────────────────────────────────────────────────────────────────────

export const DEMO_BIDDERS = [
  {
    id: 'BID-001',
    tenderId: 'GEM/2026/B/892104',
    name: 'Infosys BPM Limited',
    pan: 'AAACI1681G',
    gstin: '29AAACI1681G1ZV',
    udyam: 'UDYAM-KA-01-0012345',
    cin: 'U72200KA1993PLC014137',
    registeredAddress: 'Electronics City, Phase 1, Bengaluru, Karnataka — 560100',
    contactPerson: 'Suresh Raghunath',
    email: 's.raghunath@infosys.com',
    phone: '+91-80-28520261',
    msmeCategory: 'NOT APPLICABLE',
    turnover: '₹ 420 Cr (FY 2025-26)',
    yearsInBusiness: 32,
    compliance: 94,
    risk: 'LOW',
    status: 'VERIFIED',
  },
  {
    id: 'BID-002',
    tenderId: 'GEM/2026/B/892104',
    name: 'Wipro Infrastructure Engineering',
    pan: 'AAACW2756G',
    gstin: '29AAACW2756G1ZN',
    udyam: 'UDYAM-KA-01-0034521',
    cin: 'U28920KA2000PLC027540',
    registeredAddress: 'Sarjapur Road, Outer Ring Road, Bengaluru, Karnataka — 560035',
    contactPerson: 'Priya Menon',
    email: 'p.menon@wipro.com',
    phone: '+91-80-28440011',
    msmeCategory: 'NOT APPLICABLE',
    turnover: '₹ 310 Cr (FY 2025-26)',
    yearsInBusiness: 25,
    compliance: 88,
    risk: 'LOW',
    status: 'VERIFIED',
  },
  {
    id: 'BID-003',
    tenderId: 'GEM/2026/B/892104',
    name: 'Centurion Electronics Pvt. Ltd.',
    pan: 'AABCC4512M',
    gstin: '07AABCC4512M1ZT',
    udyam: 'UDYAM-DL-07-0078234',
    cin: 'U31200DL2008PTC183412',
    registeredAddress: 'Plot 34, Okhla Industrial Area Phase-II, New Delhi — 110020',
    contactPerson: 'Ashok Verma',
    email: 'ashok.verma@centurionelec.in',
    phone: '+91-11-41234567',
    msmeCategory: 'SMALL',
    turnover: '₹ 42 Cr (FY 2025-26)',
    yearsInBusiness: 17,
    compliance: 76,
    risk: 'MEDIUM',
    status: 'PENDING',
  },
  {
    id: 'BID-004',
    tenderId: 'GEM/2026/B/891950',
    name: 'Godrej Security Solutions',
    pan: 'AAACG0286K',
    gstin: '27AAACG0286K1Z5',
    udyam: null,
    cin: 'U74999MH1897PLC000163',
    registeredAddress: 'Pirojshanagar, Eastern Express Highway, Vikhroli, Mumbai — 400079',
    contactPerson: 'Rajan Kapoor',
    email: 'rajan.kapoor@godrej.com',
    phone: '+91-22-67962000',
    msmeCategory: 'NOT APPLICABLE',
    turnover: '₹ 1,840 Cr (FY 2025-26)',
    yearsInBusiness: 127,
    compliance: 97,
    risk: 'LOW',
    status: 'VERIFIED',
  },
  {
    id: 'BID-005',
    tenderId: 'GEM/2026/B/889412',
    name: 'Tata Consultancy Services Ltd.',
    pan: 'AAACT2727Q',
    gstin: '27AAACT2727Q1ZZ',
    udyam: null,
    cin: 'L22210MH1995PLC084781',
    registeredAddress: 'TCS House, Raveline Street, Fort, Mumbai — 400001',
    contactPerson: 'Neha Joshi',
    email: 'neha.joshi@tcs.com',
    phone: '+91-22-67789999',
    msmeCategory: 'NOT APPLICABLE',
    turnover: '₹ 24,100 Cr (FY 2025-26)',
    yearsInBusiness: 56,
    compliance: 99,
    risk: 'LOW',
    status: 'VERIFIED',
  },
  {
    id: 'BID-006',
    tenderId: 'GEM/2026/B/889412',
    name: 'NxtGen Datacenter & Cloud Technologies',
    pan: 'AABCN7123P',
    gstin: '29AABCN7123P1ZX',
    udyam: 'UDYAM-KA-01-0091234',
    cin: 'U72900KA2012PTC065432',
    registeredAddress: 'Embassy Golf Links Business Park, Bengaluru — 560071',
    contactPerson: 'Sanjay Bhat',
    email: 's.bhat@nxtgen.com',
    phone: '+91-80-45234123',
    msmeCategory: 'MEDIUM',
    turnover: '₹ 187 Cr (FY 2025-26)',
    yearsInBusiness: 14,
    compliance: 42,
    risk: 'HIGH',
    status: 'FLAGGED',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// DOCUMENTS
// ─────────────────────────────────────────────────────────────────────────────

export const DEMO_DOCUMENTS = [
  // BID-001
  { id: 'DOC-101', bidderId: 'BID-001', type: 'PAN Certificate', status: 'VERIFIED', filename: 'PAN_Infosys_BPM.pdf', uploadedDate: '05 Sep 2026', size: '124 KB', verifiedBy: 'IT Dept' },
  { id: 'DOC-102', bidderId: 'BID-001', type: 'GST Registration Certificate', status: 'VERIFIED', filename: 'GST_Infosys_BPM.pdf', uploadedDate: '05 Sep 2026', size: '218 KB', verifiedBy: 'GST Portal' },
  { id: 'DOC-103', bidderId: 'BID-001', type: 'Udyam Registration', status: 'VERIFIED', filename: 'Udyam_Infosys_BPM.pdf', uploadedDate: '05 Sep 2026', size: '98 KB', verifiedBy: 'Udyam Portal' },
  { id: 'DOC-104', bidderId: 'BID-001', type: 'Company Incorporation Certificate', status: 'VERIFIED', filename: 'CIN_Infosys_BPM.pdf', uploadedDate: '06 Sep 2026', size: '342 KB', verifiedBy: 'MCA21' },
  { id: 'DOC-105', bidderId: 'BID-001', type: 'EPFO Registration', status: 'VERIFIED', filename: 'EPFO_Infosys_BPM.pdf', uploadedDate: '06 Sep 2026', size: '156 KB', verifiedBy: 'EPFO Portal' },

  // BID-002
  { id: 'DOC-201', bidderId: 'BID-002', type: 'PAN Certificate', status: 'VERIFIED', filename: 'PAN_Wipro.pdf', uploadedDate: '04 Sep 2026', size: '118 KB', verifiedBy: 'IT Dept' },
  { id: 'DOC-202', bidderId: 'BID-002', type: 'GST Registration Certificate', status: 'VERIFIED', filename: 'GST_Wipro.pdf', uploadedDate: '04 Sep 2026', size: '204 KB', verifiedBy: 'GST Portal' },
  { id: 'DOC-203', bidderId: 'BID-002', type: 'Udyam Registration', status: 'VERIFIED', filename: 'Udyam_Wipro.pdf', uploadedDate: '04 Sep 2026', size: '88 KB', verifiedBy: 'Udyam Portal' },
  { id: 'DOC-204', bidderId: 'BID-002', type: 'EPFO Registration', status: 'PENDING', filename: 'EPFO_Wipro.pdf', uploadedDate: '07 Sep 2026', size: '—', verifiedBy: '—' },

  // BID-003
  { id: 'DOC-301', bidderId: 'BID-003', type: 'PAN Certificate', status: 'VERIFIED', filename: 'PAN_Centurion.pdf', uploadedDate: '08 Sep 2026', size: '102 KB', verifiedBy: 'IT Dept' },
  { id: 'DOC-302', bidderId: 'BID-003', type: 'GST Registration Certificate', status: 'PENDING', filename: 'GST_Centurion.pdf', uploadedDate: '08 Sep 2026', size: '—', verifiedBy: '—' },
  { id: 'DOC-303', bidderId: 'BID-003', type: 'Udyam Registration', status: 'VERIFIED', filename: 'Udyam_Centurion.pdf', uploadedDate: '09 Sep 2026', size: '78 KB', verifiedBy: 'Udyam Portal' },
  { id: 'DOC-304', bidderId: 'BID-003', type: 'Company Incorporation Certificate', status: 'UPLOADED', filename: 'CIN_Centurion.pdf', uploadedDate: '09 Sep 2026', size: '234 KB', verifiedBy: '—' },

  // BID-004
  { id: 'DOC-401', bidderId: 'BID-004', type: 'PAN Certificate', status: 'VERIFIED', filename: 'PAN_Godrej.pdf', uploadedDate: '03 Sep 2026', size: '130 KB', verifiedBy: 'IT Dept' },
  { id: 'DOC-402', bidderId: 'BID-004', type: 'GST Registration Certificate', status: 'VERIFIED', filename: 'GST_Godrej.pdf', uploadedDate: '03 Sep 2026', size: '225 KB', verifiedBy: 'GST Portal' },
  { id: 'DOC-403', bidderId: 'BID-004', type: 'Company Incorporation Certificate', status: 'VERIFIED', filename: 'CIN_Godrej.pdf', uploadedDate: '03 Sep 2026', size: '410 KB', verifiedBy: 'MCA21' },
  { id: 'DOC-404', bidderId: 'BID-004', type: 'EPFO Registration', status: 'VERIFIED', filename: 'EPFO_Godrej.pdf', uploadedDate: '04 Sep 2026', size: '190 KB', verifiedBy: 'EPFO Portal' },

  // BID-005
  { id: 'DOC-501', bidderId: 'BID-005', type: 'PAN Certificate', status: 'VERIFIED', filename: 'PAN_TCS.pdf', uploadedDate: '02 Sep 2026', size: '115 KB', verifiedBy: 'IT Dept' },
  { id: 'DOC-502', bidderId: 'BID-005', type: 'GST Registration Certificate', status: 'VERIFIED', filename: 'GST_TCS.pdf', uploadedDate: '02 Sep 2026', size: '210 KB', verifiedBy: 'GST Portal' },
  { id: 'DOC-503', bidderId: 'BID-005', type: 'Company Incorporation Certificate', status: 'VERIFIED', filename: 'CIN_TCS.pdf', uploadedDate: '02 Sep 2026', size: '388 KB', verifiedBy: 'MCA21' },
  { id: 'DOC-504', bidderId: 'BID-005', type: 'EPFO Registration', status: 'VERIFIED', filename: 'EPFO_TCS.pdf', uploadedDate: '02 Sep 2026', size: '175 KB', verifiedBy: 'EPFO Portal' },

  // BID-006
  { id: 'DOC-601', bidderId: 'BID-006', type: 'PAN Certificate', status: 'VERIFIED', filename: 'PAN_NxtGen.pdf', uploadedDate: '10 Sep 2026', size: '108 KB', verifiedBy: 'IT Dept' },
  { id: 'DOC-602', bidderId: 'BID-006', type: 'GST Registration Certificate', status: 'REJECTED', filename: 'GST_NxtGen.pdf', uploadedDate: '10 Sep 2026', size: '198 KB', verifiedBy: 'GST Portal' },
  { id: 'DOC-603', bidderId: 'BID-006', type: 'Udyam Registration', status: 'PENDING', filename: 'Udyam_NxtGen.pdf', uploadedDate: '10 Sep 2026', size: '—', verifiedBy: '—' },
  { id: 'DOC-604', bidderId: 'BID-006', type: 'Company Incorporation Certificate', status: 'UPLOADED', filename: 'CIN_NxtGen.pdf', uploadedDate: '11 Sep 2026', size: '290 KB', verifiedBy: '—' },
];

// ─────────────────────────────────────────────────────────────────────────────
// VERIFICATION RESULTS (deterministic, per bidder)
// ─────────────────────────────────────────────────────────────────────────────

export const DEMO_VERIFICATION_RESULTS = {
  'BID-001': {
    bidderId: 'BID-001',
    bidderName: 'Infosys BPM Limited',
    score: 94,
    maxScore: 100,
    risk: 'LOW',
    verificationDate: '11 Sep 2026',
    provider: 'SecondLook Demo Pipeline v0.1',
    processingSteps: [
      'Initialising verification pipeline...',
      'Fetching PAN details from IT Department registry...',
      'Validating GST registration status via GSTN portal...',
      'Confirming Udyam MSME registration...',
      'Checking MCA21 company records...',
      'Running EPFO/ESIC compliance check...',
      'Querying Central Vendor Blacklist Registry...',
      'Performing OCR extraction on uploaded documents...',
      'Running AI-assisted document authenticity check...',
      'Computing composite compliance score...',
      'Verification complete.',
    ],
    findings: [
      { check: 'PAN Verification', status: 'PASS', detail: 'PAN AAACI1681G is active and linked to Infosys BPM Limited', source: 'Income Tax Department' },
      { check: 'GST Registration', status: 'PASS', detail: 'GSTIN 29AAACI1681G1ZV is active. All GST returns filed up to date.', source: 'GSTN Portal' },
      { check: 'Udyam / MSME', status: 'PASS', detail: 'Udyam registration UDYAM-KA-01-0012345 verified as active.', source: 'Udyam Portal' },
      { check: 'MCA21 Company Registry', status: 'PASS', detail: 'CIN U72200KA1993PLC014137 — Company status: Active. No strike-off proceedings.', source: 'MCA21' },
      { check: 'EPFO Compliance', status: 'PASS', detail: 'ECR filed for the last 12 consecutive months.', source: 'EPFO Portal' },
      { check: 'Central Blacklist Check', status: 'PASS', detail: 'Not found in any central debarment or blacklist registry.', source: 'CVC / DPIIT' },
      { check: 'Document Authenticity', status: 'PASS', detail: 'All submitted documents passed OCR and authenticity validation.', source: 'OCR Engine' },
    ],
    evidenceSources: [
      { source: 'Income Tax Department', status: 'VERIFIED', responseTime: '1.2s' },
      { source: 'GSTN Portal', status: 'VERIFIED', responseTime: '0.9s' },
      { source: 'Udyam Portal', status: 'VERIFIED', responseTime: '1.1s' },
      { source: 'MCA21', status: 'VERIFIED', responseTime: '1.4s' },
      { source: 'EPFO Portal', status: 'VERIFIED', responseTime: '0.8s' },
      { source: 'CVC Blacklist Registry', status: 'CLEAR', responseTime: '0.6s' },
    ],
  },

  'BID-002': {
    bidderId: 'BID-002',
    bidderName: 'Wipro Infrastructure Engineering',
    score: 88,
    maxScore: 100,
    risk: 'LOW',
    verificationDate: '11 Sep 2026',
    provider: 'SecondLook Demo Pipeline v0.1',
    processingSteps: [
      'Initialising verification pipeline...',
      'Fetching PAN details from IT Department registry...',
      'Validating GST registration status via GSTN portal...',
      'Confirming Udyam MSME registration...',
      'Checking MCA21 company records...',
      'Running EPFO/ESIC compliance check...',
      'Querying Central Vendor Blacklist Registry...',
      'Performing OCR extraction on uploaded documents...',
      'Running AI-assisted document authenticity check...',
      'Computing composite compliance score...',
      'Verification complete.',
    ],
    findings: [
      { check: 'PAN Verification', status: 'PASS', detail: 'PAN AAACW2756G is active and linked to Wipro Infrastructure Engineering.', source: 'Income Tax Department' },
      { check: 'GST Registration', status: 'PASS', detail: 'GSTIN 29AAACW2756G1ZN is active. Returns filed for last 11 months.', source: 'GSTN Portal' },
      { check: 'Udyam / MSME', status: 'PASS', detail: 'Udyam registration UDYAM-KA-01-0034521 is active.', source: 'Udyam Portal' },
      { check: 'MCA21 Company Registry', status: 'PASS', detail: 'Company status: Active. No pending disqualification.', source: 'MCA21' },
      { check: 'EPFO Compliance', status: 'WARN', detail: 'EPFO document upload pending. Physical ECR available but not yet digitally verified.', source: 'EPFO Portal' },
      { check: 'Central Blacklist Check', status: 'PASS', detail: 'Not found in any central debarment or blacklist registry.', source: 'CVC / DPIIT' },
      { check: 'Document Authenticity', status: 'PASS', detail: 'Documents PAN, GST, Udyam passed OCR authenticity check.', source: 'OCR Engine' },
    ],
    evidenceSources: [
      { source: 'Income Tax Department', status: 'VERIFIED', responseTime: '1.0s' },
      { source: 'GSTN Portal', status: 'VERIFIED', responseTime: '0.8s' },
      { source: 'Udyam Portal', status: 'VERIFIED', responseTime: '1.2s' },
      { source: 'MCA21', status: 'VERIFIED', responseTime: '1.5s' },
      { source: 'EPFO Portal', status: 'PENDING', responseTime: '—' },
      { source: 'CVC Blacklist Registry', status: 'CLEAR', responseTime: '0.6s' },
    ],
  },

  'BID-003': {
    bidderId: 'BID-003',
    bidderName: 'Centurion Electronics Pvt. Ltd.',
    score: 76,
    maxScore: 100,
    risk: 'MEDIUM',
    verificationDate: '11 Sep 2026',
    provider: 'SecondLook Demo Pipeline v0.1',
    processingSteps: [
      'Initialising verification pipeline...',
      'Fetching PAN details from IT Department registry...',
      'Validating GST registration status via GSTN portal...',
      'Confirming Udyam MSME registration...',
      'Checking MCA21 company records...',
      'Running EPFO/ESIC compliance check...',
      'Querying Central Vendor Blacklist Registry...',
      'Performing OCR extraction on uploaded documents...',
      'Running AI-assisted document authenticity check...',
      'Computing composite compliance score...',
      'Verification complete.',
    ],
    findings: [
      { check: 'PAN Verification', status: 'PASS', detail: 'PAN AABCC4512M is active and linked to Centurion Electronics Pvt. Ltd.', source: 'Income Tax Department' },
      { check: 'GST Registration', status: 'WARN', detail: 'GSTIN 07AABCC4512M1ZT found but 2 quarterly returns overdue.', source: 'GSTN Portal' },
      { check: 'Udyam / MSME', status: 'PASS', detail: 'Udyam UDYAM-DL-07-0078234 active for Small Enterprise category.', source: 'Udyam Portal' },
      { check: 'MCA21 Company Registry', status: 'PASS', detail: 'Company status: Active.', source: 'MCA21' },
      { check: 'EPFO Compliance', status: 'WARN', detail: 'EPFO not provided. Manual submission required.', source: 'EPFO Portal' },
      { check: 'Central Blacklist Check', status: 'PASS', detail: 'Not found in any central debarment or blacklist registry.', source: 'CVC / DPIIT' },
      { check: 'Document Authenticity', status: 'PASS', detail: 'PAN and Udyam documents passed. GST document pending review.', source: 'OCR Engine' },
    ],
    evidenceSources: [
      { source: 'Income Tax Department', status: 'VERIFIED', responseTime: '1.1s' },
      { source: 'GSTN Portal', status: 'WARNING', responseTime: '0.9s' },
      { source: 'Udyam Portal', status: 'VERIFIED', responseTime: '1.0s' },
      { source: 'MCA21', status: 'VERIFIED', responseTime: '1.6s' },
      { source: 'EPFO Portal', status: 'PENDING', responseTime: '—' },
      { source: 'CVC Blacklist Registry', status: 'CLEAR', responseTime: '0.5s' },
    ],
  },

  'BID-004': {
    bidderId: 'BID-004',
    bidderName: 'Godrej Security Solutions',
    score: 97,
    maxScore: 100,
    risk: 'LOW',
    verificationDate: '11 Sep 2026',
    provider: 'SecondLook Demo Pipeline v0.1',
    processingSteps: [
      'Initialising verification pipeline...',
      'Fetching PAN details from IT Department registry...',
      'Validating GST registration status via GSTN portal...',
      'Checking MCA21 company records...',
      'Running EPFO/ESIC compliance check...',
      'Querying Central Vendor Blacklist Registry...',
      'Performing OCR extraction on uploaded documents...',
      'Running AI-assisted document authenticity check...',
      'Computing composite compliance score...',
      'Verification complete.',
    ],
    findings: [
      { check: 'PAN Verification', status: 'PASS', detail: 'PAN AAACG0286K is active and linked to Godrej Security Solutions.', source: 'Income Tax Department' },
      { check: 'GST Registration', status: 'PASS', detail: 'GSTIN 27AAACG0286K1Z5 is active. All returns filed.', source: 'GSTN Portal' },
      { check: 'MCA21 Company Registry', status: 'PASS', detail: 'Company status: Active. 127-year operating history confirmed.', source: 'MCA21' },
      { check: 'EPFO Compliance', status: 'PASS', detail: 'EPFO returns filed for 24 consecutive months.', source: 'EPFO Portal' },
      { check: 'Central Blacklist Check', status: 'PASS', detail: 'Not found in any debarment registry.', source: 'CVC / DPIIT' },
      { check: 'Document Authenticity', status: 'PASS', detail: 'All documents passed OCR and authenticity validation.', source: 'OCR Engine' },
    ],
    evidenceSources: [
      { source: 'Income Tax Department', status: 'VERIFIED', responseTime: '1.1s' },
      { source: 'GSTN Portal', status: 'VERIFIED', responseTime: '0.8s' },
      { source: 'MCA21', status: 'VERIFIED', responseTime: '1.3s' },
      { source: 'EPFO Portal', status: 'VERIFIED', responseTime: '0.9s' },
      { source: 'CVC Blacklist Registry', status: 'CLEAR', responseTime: '0.5s' },
    ],
  },

  'BID-005': {
    bidderId: 'BID-005',
    bidderName: 'Tata Consultancy Services Ltd.',
    score: 99,
    maxScore: 100,
    risk: 'LOW',
    verificationDate: '11 Sep 2026',
    provider: 'SecondLook Demo Pipeline v0.1',
    processingSteps: [
      'Initialising verification pipeline...',
      'Fetching PAN details from IT Department registry...',
      'Validating GST registration status via GSTN portal...',
      'Checking MCA21 company records...',
      'Running EPFO/ESIC compliance check...',
      'Querying Central Vendor Blacklist Registry...',
      'Performing OCR extraction on uploaded documents...',
      'Running AI-assisted document authenticity check...',
      'Computing composite compliance score...',
      'Verification complete.',
    ],
    findings: [
      { check: 'PAN Verification', status: 'PASS', detail: 'PAN AAACT2727Q is active. Matches company name exactly.', source: 'Income Tax Department' },
      { check: 'GST Registration', status: 'PASS', detail: 'GSTIN 27AAACT2727Q1ZZ is active. All filings current.', source: 'GSTN Portal' },
      { check: 'MCA21 Company Registry', status: 'PASS', detail: 'Listed company. BSE/NSE listed entity. All filings current.', source: 'MCA21' },
      { check: 'EPFO Compliance', status: 'PASS', detail: 'EPFO and ESIC returns filed for 36 consecutive months.', source: 'EPFO Portal' },
      { check: 'Central Blacklist Check', status: 'PASS', detail: 'Not found in any debarment or blacklist registry.', source: 'CVC / DPIIT' },
      { check: 'Document Authenticity', status: 'PASS', detail: 'All documents passed OCR and AI authenticity validation.', source: 'OCR Engine' },
    ],
    evidenceSources: [
      { source: 'Income Tax Department', status: 'VERIFIED', responseTime: '1.0s' },
      { source: 'GSTN Portal', status: 'VERIFIED', responseTime: '0.7s' },
      { source: 'MCA21', status: 'VERIFIED', responseTime: '1.1s' },
      { source: 'EPFO Portal', status: 'VERIFIED', responseTime: '0.8s' },
      { source: 'CVC Blacklist Registry', status: 'CLEAR', responseTime: '0.4s' },
    ],
  },

  'BID-006': {
    bidderId: 'BID-006',
    bidderName: 'NxtGen Datacenter & Cloud Technologies',
    score: 42,
    maxScore: 100,
    risk: 'HIGH',
    verificationDate: '11 Sep 2026',
    provider: 'SecondLook Demo Pipeline v0.1',
    processingSteps: [
      'Initialising verification pipeline...',
      'Fetching PAN details from IT Department registry...',
      'Validating GST registration status via GSTN portal...',
      'Confirming Udyam MSME registration...',
      'Checking MCA21 company records...',
      'Running EPFO/ESIC compliance check...',
      'Querying Central Vendor Blacklist Registry...',
      'Performing OCR extraction on uploaded documents...',
      'Running AI-assisted document authenticity check...',
      'Computing composite compliance score...',
      'Verification complete. Issues found — manual review recommended.',
    ],
    findings: [
      { check: 'PAN Verification', status: 'PASS', detail: 'PAN AABCN7123P is active.', source: 'Income Tax Department' },
      { check: 'GST Registration', status: 'FAIL', detail: 'GSTIN 29AABCN7123P1ZX shows CANCELLED status as of July 2026. Refiling required.', source: 'GSTN Portal' },
      { check: 'Udyam / MSME', status: 'WARN', detail: 'Udyam UDYAM-KA-01-0091234 upload pending. Submitted document unreadable.', source: 'Udyam Portal' },
      { check: 'MCA21 Company Registry', status: 'PASS', detail: 'Company status: Active.', source: 'MCA21' },
      { check: 'EPFO Compliance', status: 'FAIL', detail: 'EPFO ECR not filed for 4 months. Non-compliance detected.', source: 'EPFO Portal' },
      { check: 'Central Blacklist Check', status: 'PASS', detail: 'Not found in central blacklist registry.', source: 'CVC / DPIIT' },
      { check: 'Document Authenticity', status: 'FAIL', detail: 'GST certificate OCR extraction failed — document may be altered.', source: 'OCR Engine' },
    ],
    evidenceSources: [
      { source: 'Income Tax Department', status: 'VERIFIED', responseTime: '1.2s' },
      { source: 'GSTN Portal', status: 'FAILED', responseTime: '0.9s' },
      { source: 'Udyam Portal', status: 'PENDING', responseTime: '—' },
      { source: 'MCA21', status: 'VERIFIED', responseTime: '1.7s' },
      { source: 'EPFO Portal', status: 'FAILED', responseTime: '1.0s' },
      { source: 'CVC Blacklist Registry', status: 'CLEAR', responseTime: '0.5s' },
    ],
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// AUDIT LOG ENTRIES
// ─────────────────────────────────────────────────────────────────────────────

export const DEMO_AUDIT_LOG = [
  { id: 'AUD-001', event: 'VERIFICATION_COMPLETED', entity: 'Infosys BPM Limited', entityId: 'BID-001', actor: 'SecondLook Pipeline', details: 'Score: 94/100 — LOW RISK', timestamp: '11 Sep 2026, 10:42 AM' },
  { id: 'AUD-002', event: 'DOCUMENT_UPLOADED', entity: 'Wipro Infrastructure Engineering', entityId: 'BID-002', actor: 'Bidder Portal', details: 'EPFO Registration uploaded', timestamp: '07 Sep 2026, 3:15 PM' },
  { id: 'AUD-003', event: 'TENDER_PUBLISHED', entity: 'GEM/2026/B/892104', entityId: 'GEM/2026/B/892104', actor: 'System', details: 'Tender published to GeM portal', timestamp: '01 Sep 2026, 9:00 AM' },
  { id: 'AUD-004', event: 'VERIFICATION_FLAGGED', entity: 'NxtGen Datacenter & Cloud Technologies', entityId: 'BID-006', actor: 'SecondLook Pipeline', details: 'Score: 42/100 — HIGH RISK — GST Cancelled', timestamp: '11 Sep 2026, 11:20 AM' },
  { id: 'AUD-005', event: 'OFFICER_DECISION', entity: 'Godrej Security Solutions', entityId: 'BID-004', actor: 'Auditor Officer', details: 'Approved — Score 97/100', timestamp: '11 Sep 2026, 2:05 PM' },
  { id: 'AUD-006', event: 'VERIFICATION_COMPLETED', entity: 'Tata Consultancy Services Ltd.', entityId: 'BID-005', actor: 'SecondLook Pipeline', details: 'Score: 99/100 — LOW RISK', timestamp: '11 Sep 2026, 10:55 AM' },
  { id: 'AUD-007', event: 'DOCUMENT_REJECTED', entity: 'NxtGen Datacenter & Cloud Technologies', entityId: 'BID-006', actor: 'SecondLook Pipeline', details: 'GST Certificate failed OCR authenticity check', timestamp: '11 Sep 2026, 11:18 AM' },
  { id: 'AUD-008', event: 'TENDER_PUBLISHED', entity: 'GEM/2026/B/889412', entityId: 'GEM/2026/B/889412', actor: 'System', details: 'Tender published to GeM portal', timestamp: '20 Aug 2026, 9:00 AM' },
];

// ─────────────────────────────────────────────────────────────────────────────
// HELPER UTILITIES
// ─────────────────────────────────────────────────────────────────────────────

/** Return bidders for a given tenderId */
export function getBiddersByTender(tenderId) {
  return DEMO_BIDDERS.filter((b) => b.tenderId === tenderId);
}

/** Return all bidders for all tenders */
export function getAllBidders() {
  return DEMO_BIDDERS;
}

/** Return a single bidder by ID */
export function getBidderById(bidderId) {
  return DEMO_BIDDERS.find((b) => b.id === bidderId) || null;
}

/** Return documents for a given bidderId */
export function getDocumentsByBidder(bidderId) {
  return DEMO_DOCUMENTS.filter((d) => d.bidderId === bidderId);
}

/** Return a single tender by ID */
export function getTenderById(tenderId) {
  return DEMO_TENDERS.find((t) => t.id === tenderId) || null;
}

/** Return verification result for a given bidderId */
export function getVerificationResult(bidderId) {
  return DEMO_VERIFICATION_RESULTS[bidderId] || null;
}
