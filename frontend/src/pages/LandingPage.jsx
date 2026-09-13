import React, { Suspense } from 'react';
import { Link } from 'react-router-dom';
import PublicNavbar from '../components/landing/PublicNavbar.jsx';

const Hero3D = React.lazy(() => import('../components/landing/Hero3D.jsx'));

/**
 * LandingPage — Milestone 06
 * Public product experience for SecondLook.
 * 
 * Narrative Structure:
 * 1. Public Navbar with tricolor accent & theme toggle
 * 2. Hero Section + 3D Evidence Constellation + Role CTAs
 * 3. 5-Step Deterministic Workflow ("How It Works")
 * 4. Evidence & Explainability Architecture ("Evidence Chain")
 * 5. AI + Human Control Principle ("AI suggests. Rules evaluate. Evidence explains. Officers decide.")
 * 6. For Bidders Workspace Overview
 * 7. For Officers Workspace Overview
 * 8. Core Product Principles
 * 9. Dual-Card Role CTA ("Choose Your Workspace")
 * 10. Public Footer with GeM compliance context
 */
export default function LandingPage() {
  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg-page)',
        color: 'var(--color-text-primary)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* 1. Public Navigation */}
      <PublicNavbar />

      <main style={{ flex: 1 }}>
        {/* 2. Hero Section */}
        <section
          style={{
            position: 'relative',
            overflow: 'hidden',
            borderBottom: '1px solid var(--color-border)',
            background: 'linear-gradient(180deg, var(--color-bg-card) 0%, var(--color-bg-page) 100%)',
            padding: 'var(--space-8) var(--space-4) var(--space-10) var(--space-4)',
          }}
        >
          <div
            style={{
              maxWidth: 'var(--max-content-width)',
              margin: '0 auto',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: 'var(--space-8)',
              alignItems: 'center',
            }}
          >
            {/* Hero Text & CTAs */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {/* Category chip */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    padding: 'var(--space-1) var(--space-3)',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: 'var(--color-primary-subtle)',
                    color: 'var(--color-primary)',
                    fontSize: 'var(--font-size-xs)',
                    fontWeight: 'var(--font-weight-semibold)',
                    letterSpacing: '0.05em',
                    textTransform: 'uppercase',
                    border: '1px solid var(--color-border)',
                  }}
                >
                  <span style={{ color: 'var(--gov-saffron-bright)' }}>●</span>
                  AI-Powered Public Procurement Compliance
                </span>
              </div>

              <h1
                style={{
                  fontSize: 'clamp(2rem, 4vw, 3rem)',
                  fontWeight: '800',
                  lineHeight: 1.15,
                  letterSpacing: '-0.03em',
                  color: 'var(--color-text-primary)',
                  margin: 0,
                }}
              >
                AI-Powered Tender Compliance and Verification Platform
              </h1>

              <p
                style={{
                  fontSize: 'var(--font-size-lg)',
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.6,
                  margin: 0,
                  maxWidth: '560px',
                }}
              >
                <strong>Upload. Verify. Understand.</strong> SecondLook helps procurement teams evaluate tender requirements, evidence, verification results and compliance in one transparent, human-controlled workflow.
              </p>

              {/* Primary Role CTAs */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 'var(--space-3)',
                  marginTop: 'var(--space-2)',
                }}
              >
                <Link
                  to="/signup?role=bidder"
                  style={{
                    padding: 'var(--space-3) var(--space-5)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 'var(--font-size-base)',
                    fontWeight: 'var(--font-weight-semibold)',
                    color: '#FFFFFF',
                    backgroundColor: 'var(--color-success)',
                    border: 'none',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    boxShadow: 'var(--shadow-sm)',
                    transition: 'transform var(--transition-fast)',
                  }}
                >
                  <span>🏢</span> Sign Up as Bidder
                </Link>

                <Link
                  to="/signup?role=officer"
                  style={{
                    padding: 'var(--space-3) var(--space-5)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 'var(--font-size-base)',
                    fontWeight: 'var(--font-weight-semibold)',
                    color: '#FFFFFF',
                    backgroundColor: 'var(--color-primary)',
                    border: 'none',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    boxShadow: 'var(--shadow-sm)',
                    transition: 'transform var(--transition-fast)',
                  }}
                >
                  <span>⚖️</span> Sign Up as Officer
                </Link>
              </div>

              {/* Trust Indicators */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 'var(--space-4)',
                  paddingTop: 'var(--space-4)',
                  borderTop: '1px solid var(--color-border)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-text-muted)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                  <span>✓</span> Deterministic Rules
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                  <span>✓</span> Evidence Traceability
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                  <span>✓</span> Officer Authority
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                  <span>✓</span> Immutable Audit
                </div>
              </div>
            </div>

            {/* Hero 3D Canvas */}
            <div
              style={{
                position: 'relative',
                height: '460px',
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Suspense
                fallback={
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 'var(--space-2)',
                      height: '100%',
                      color: 'var(--color-text-muted)',
                      fontSize: 'var(--font-size-xs)',
                    }}
                  >
                    <span>Loading 3D visualization...</span>
                  </div>
                }
              >
                <Hero3D />
              </Suspense>
            </div>
          </div>
        </section>

        {/* 3. How SecondLook Works (5-Step Deterministic Workflow) */}
        <section
          id="how-it-works"
          style={{
            padding: 'var(--space-10) var(--space-4)',
            maxWidth: 'var(--max-content-width)',
            margin: '0 auto',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                fontWeight: 'var(--font-weight-bold)',
                color: 'var(--color-primary)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              The SecondLook Process
            </span>
            <h2
              style={{
                fontSize: 'var(--font-size-2xl)',
                fontWeight: '700',
                margin: 'var(--space-2) 0 var(--space-3) 0',
              }}
            >
              How SecondLook Works
            </h2>
            <p
              style={{
                maxWidth: '680px',
                margin: '0 auto',
                fontSize: 'var(--font-size-base)',
                color: 'var(--color-text-secondary)',
                lineHeight: 1.6,
              }}
            >
              A transparent, deterministic 5-step procurement evaluation pipeline built around statutory verification and human review.
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--space-4)',
            }}
          >
            {[
              {
                step: '01',
                title: 'Upload',
                icon: '📁',
                desc: 'Tender and bidder documents securely enter the workflow in native PDF/scanned formats.',
              },
              {
                step: '02',
                title: 'Extract',
                icon: '🔍',
                desc: 'OCR and intelligent extraction structure relevant requirements, financial numbers, and company metadata.',
              },
              {
                step: '03',
                title: 'Verify',
                icon: '🛡️',
                desc: 'Extracted attributes are cross-referenced with statutory sources including GSTIN, PAN, and registry records.',
              },
              {
                step: '04',
                title: 'Evaluate',
                icon: '⚖️',
                desc: 'Deterministic rules evaluate requirements against collected evidence, recording compliant, non-compliant, or flagged statuses.',
              },
              {
                step: '05',
                title: 'Review',
                icon: '👤',
                desc: 'Procurement officers inspect side-by-side evidence excerpts and record final explicit decisions.',
              },
            ].map((card) => (
              <div
                key={card.step}
                style={{
                  padding: 'var(--space-5)',
                  backgroundColor: 'var(--color-bg-card)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border)',
                  boxShadow: 'var(--shadow-xs)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-2)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '24px' }}>{card.icon}</span>
                  <span
                    style={{
                      fontSize: 'var(--font-size-xs)',
                      fontWeight: 'var(--font-weight-bold)',
                      color: 'var(--color-primary)',
                      backgroundColor: 'var(--color-primary-subtle)',
                      padding: 'var(--space-1) var(--space-2)',
                      borderRadius: 'var(--radius-xs)',
                    }}
                  >
                    STEP {card.step}
                  </span>
                </div>
                <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: '600', margin: 'var(--space-1) 0 0 0' }}>
                  {card.title}
                </h3>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: 0 }}>
                  {card.desc}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* 4. Evidence + Explainability Section */}
        <section
          id="evidence"
          style={{
            backgroundColor: 'var(--color-bg-subtle)',
            borderTop: '1px solid var(--color-border)',
            borderBottom: '1px solid var(--color-border)',
            padding: 'var(--space-10) var(--space-4)',
          }}
        >
          <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>
              <span
                style={{
                  fontSize: 'var(--font-size-xs)',
                  fontWeight: 'var(--font-weight-bold)',
                  color: 'var(--color-primary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                }}
              >
                Explainable Architecture
              </span>
              <h2
                style={{
                  fontSize: 'var(--font-size-2xl)',
                  fontWeight: '700',
                  margin: 'var(--space-2) 0 var(--space-3) 0',
                }}
              >
                The Traceable Evidence Chain
              </h2>
              <p
                style={{
                  maxWidth: '720px',
                  margin: '0 auto',
                  fontSize: 'var(--font-size-base)',
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.6,
                }}
              >
                Every compliance evaluation is grounded in an immutable, auditable evidence chain. No black-box scores, no unexplained disqualifications.
              </p>
            </div>

            {/* Visual Evidence Chain Schematic */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: 'var(--space-2)',
                alignItems: 'center',
                backgroundColor: 'var(--color-bg-card)',
                padding: 'var(--space-6)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              {[
                { step: 'Requirement', desc: 'Mandated tender criterion', badge: 'Rule' },
                { step: 'Evaluation', desc: 'Deterministic condition logic', badge: 'Engine' },
                { step: 'Evidence', desc: 'Extracted fact & confidence', badge: 'Proof' },
                { step: 'Source', desc: 'Official registry verification', badge: 'Authority' },
                { step: 'Document', desc: 'Original submitted page & text', badge: 'Origin' },
                { step: 'Audit', desc: 'Immutable action timestamp', badge: 'Ledger' },
              ].map((item, idx, arr) => (
                <div key={item.step} style={{ textAlign: 'center', position: 'relative' }}>
                  <div
                    style={{
                      padding: 'var(--space-3)',
                      backgroundColor: 'var(--color-bg-page)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--color-border)',
                      marginBottom: 'var(--space-2)',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: '700',
                        color: 'var(--color-primary)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                      }}
                    >
                      {item.badge}
                    </span>
                    <div style={{ fontWeight: '600', fontSize: 'var(--font-size-sm)', marginTop: '2px' }}>
                      {item.step}
                    </div>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>{item.desc}</div>
                </div>
              ))}
            </div>

            {/* Illustrative Callout Card */}
            <div
              style={{
                marginTop: 'var(--space-6)',
                padding: 'var(--space-4) var(--space-5)',
                backgroundColor: 'var(--color-bg-card)',
                borderRadius: 'var(--radius-md)',
                borderLeft: '4px solid var(--gov-green)',
                borderTop: '1px solid var(--color-border)',
                borderRight: '1px solid var(--color-border)',
                borderBottom: '1px solid var(--color-border)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-1)' }}>
                <span style={{ color: 'var(--gov-green)', fontWeight: 'bold' }}>✓</span>
                <strong style={{ fontSize: 'var(--font-size-sm)' }}>Illustrative Example: Statutory GSTIN Verification</strong>
              </div>
              <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                When a bidder submits Form GSTR-3B, SecondLook verifies the GSTIN structure, cross-references active registration with statutory verification services, locates the precise document excerpt, and presents the officer with both the original scan and verification evidence before any requirement is marked compliant.
              </p>
            </div>
          </div>
        </section>

        {/* 5. AI + Human Control Section */}
        <section
          id="human-control"
          style={{
            padding: 'var(--space-10) var(--space-4)',
            maxWidth: 'var(--max-content-width)',
            margin: '0 auto',
          }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: 'var(--space-8)',
              alignItems: 'center',
            }}
          >
            <div>
              <span
                style={{
                  fontSize: 'var(--font-size-xs)',
                  fontWeight: 'var(--font-weight-bold)',
                  color: 'var(--color-primary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                }}
              >
                Core Governing Principle
              </span>
              <h2
                style={{
                  fontSize: 'var(--font-size-2xl)',
                  fontWeight: '700',
                  margin: 'var(--space-2) 0 var(--space-4) 0',
                }}
              >
                AI Assisting Human Authority
              </h2>

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-3)',
                  marginBottom: 'var(--space-6)',
                }}
              >
                {[
                  { title: 'AI Suggests', desc: 'Identifies potential requirement matches, extracts numeric parameters, and pinpoints document sections.' },
                  { title: 'Rules Evaluate', desc: 'Deterministic compliance engines check boolean and threshold rules without hallucination.' },
                  { title: 'Evidence Explains', desc: 'Clear evidence traces link every status to specific pages, timestamps, and registry checks.' },
                  { title: 'Officers Decide', desc: 'Human procurement officers retain absolute authority to approve, reject, or request clarification.' },
                ].map((item, index) => (
                  <div key={item.title} style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start' }}>
                    <div
                      style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: 'var(--radius-full)',
                        backgroundColor: 'var(--color-primary-subtle)',
                        color: 'var(--color-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 'var(--font-size-xs)',
                        fontWeight: 'bold',
                        flexShrink: 0,
                        marginTop: '2px',
                      }}
                    >
                      {index + 1}
                    </div>
                    <div>
                      <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                        {item.title}:
                      </strong>{' '}
                      <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                        {item.desc}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div
                style={{
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-bg-subtle)',
                  border: '1px solid var(--color-border)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-text-muted)',
                }}
              >
                SecondLook strictly prevents autonomous tender disqualification or tender awarding. All procurement decisions remain legally accountable to the designated procurement officer.
              </div>
            </div>

            {/* Side Card: The Mantra */}
            <div
              style={{
                backgroundColor: 'var(--color-bg-card)',
                padding: 'var(--space-8)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-md)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-4)',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '40px' }}>⚖️</div>
              <div
                style={{
                  fontSize: 'var(--font-size-xl)',
                  fontWeight: '700',
                  color: 'var(--color-primary)',
                  lineHeight: 1.4,
                  letterSpacing: '-0.02em',
                }}
              >
                &ldquo;AI suggests.<br />
                Rules evaluate.<br />
                Evidence explains.<br />
                Officers decide.&rdquo;
              </div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                SecondLook Evidence-Driven Architecture Standard
              </div>
            </div>
          </div>
        </section>

        {/* 6. For Bidders Section */}
        <section
          id="for-bidders"
          style={{
            backgroundColor: 'var(--color-bg-subtle)',
            borderTop: '1px solid var(--color-border)',
            borderBottom: '1px solid var(--color-border)',
            padding: 'var(--space-10) var(--space-4)',
          }}
        >
          <div
            style={{
              maxWidth: 'var(--max-content-width)',
              margin: '0 auto',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: 'var(--space-8)',
              alignItems: 'center',
            }}
          >
            <div>
              <span
                style={{
                  fontSize: 'var(--font-size-xs)',
                  fontWeight: 'var(--font-weight-bold)',
                  color: 'var(--color-success)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                }}
              >
                For Bidders &amp; Suppliers
              </span>
              <h2
                style={{
                  fontSize: 'var(--font-size-2xl)',
                  fontWeight: '700',
                  margin: 'var(--space-2) 0 var(--space-3) 0',
                }}
              >
                Understand What Your Submission Needs
              </h2>
              <p
                style={{
                  fontSize: 'var(--font-size-base)',
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.6,
                  marginBottom: 'var(--space-4)',
                }}
              >
                With the upcoming SecondLook bidder workspace, suppliers will be able to verify their submission readiness against mandated requirements before evaluation deadlines:
              </p>

              <ul
                style={{
                  listStyle: 'none',
                  padding: 0,
                  margin: '0 0 var(--space-6) 0',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-2)',
                }}
              >
                {[
                  'Review structured tender requirements and required document formats',
                  'Upload company verification and technical bid documents',
                  'Track document processing and statutory verification status',
                  'Inspect compliance results with transparent, evidence-based explanations',
                  'Identify missing or non-compliant statutory documentation in advance',
                ].map((item) => (
                  <li key={item} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-size-sm)' }}>
                    <span style={{ color: 'var(--color-success)', fontWeight: 'bold' }}>✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>

              <Link
                to="/signup?role=bidder"
                style={{
                  padding: 'var(--space-3) var(--space-5)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: 'var(--font-weight-semibold)',
                  color: '#FFFFFF',
                  backgroundColor: 'var(--color-success)',
                  border: 'none',
                  textDecoration: 'none',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                }}
              >
                <span>🏢</span> Register as Bidder
              </Link>
            </div>

            <div
              style={{
                backgroundColor: 'var(--color-bg-card)',
                padding: 'var(--space-6)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div
                style={{
                  fontSize: 'var(--font-size-xs)',
                  fontWeight: 'bold',
                  textTransform: 'uppercase',
                  color: 'var(--color-text-muted)',
                  marginBottom: 'var(--space-3)',
                }}
              >
                Upcoming Bidder Workspace (Illustrative Preview)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: '600', fontSize: 'var(--font-size-sm)' }}>GSTIN Registration</span>
                    <span style={{ fontSize: '11px', color: 'var(--color-success)', fontWeight: 'bold' }}>VERIFIED</span>
                  </div>
                  <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    Matched with Ministry of Corporate Affairs Registry
                  </p>
                </div>

                <div style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: '600', fontSize: 'var(--font-size-sm)' }}>Annual Turnover Threshold</span>
                    <span style={{ fontSize: '11px', color: 'var(--color-success)', fontWeight: 'bold' }}>COMPLIANT</span>
                  </div>
                  <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    ₹42.50 Cr validated via Audited P&amp;L Excerpts
                  </p>
                </div>

                <div style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: '600', fontSize: 'var(--font-size-sm)' }}>Experience Certificate</span>
                    <span style={{ fontSize: '11px', color: 'var(--color-warning)', fontWeight: 'bold' }}>PENDING REVIEW</span>
                  </div>
                  <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    Completion certificate awaiting procurement officer sign-off
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 7. For Officers Section */}
        <section
          id="for-officers"
          style={{
            padding: 'var(--space-10) var(--space-4)',
            maxWidth: 'var(--max-content-width)',
            margin: '0 auto',
          }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: 'var(--space-8)',
              alignItems: 'center',
            }}
          >
            <div
              style={{
                backgroundColor: 'var(--color-bg-card)',
                padding: 'var(--space-6)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div
                style={{
                  fontSize: 'var(--font-size-xs)',
                  fontWeight: 'bold',
                  textTransform: 'uppercase',
                  color: 'var(--color-text-muted)',
                  marginBottom: 'var(--space-3)',
                }}
              >
                Officer Evaluation Dashboard (Illustrative Preview)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border)' }}>
                  <div>
                    <div style={{ fontWeight: '600', fontSize: 'var(--font-size-sm)' }}>Tender #GEM/2026/B/8912 (Sample)</div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>3 Bidders Evaluated • 12 Requirements</div>
                  </div>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', backgroundColor: 'var(--color-primary-subtle)', color: 'var(--color-primary)' }}>
                    SAMPLE REVIEW
                  </span>
                </div>

                <div style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border)' }}>
                  <div style={{ fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Side-by-Side Document Inspection</div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                    Inspect original scanned bid excerpts next to automated OCR extractions, statutory registry payloads, and compliance scores.
                  </div>
                </div>

                <div style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border)' }}>
                  <div style={{ fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Immutable Decision Signing</div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                    Approve or reject requirements with an explicit audit trail recorded under your verified officer identity.
                  </div>
                </div>
              </div>
            </div>

            <div>
              <span
                style={{
                  fontSize: 'var(--font-size-xs)',
                  fontWeight: 'var(--font-weight-bold)',
                  color: 'var(--color-primary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                }}
              >
                For Procurement Officers
              </span>
              <h2
                style={{
                  fontSize: 'var(--font-size-2xl)',
                  fontWeight: '700',
                  margin: 'var(--space-2) 0 var(--space-3) 0',
                }}
              >
                Evidence-Driven Review Workspace
              </h2>
              <p
                style={{
                  fontSize: 'var(--font-size-base)',
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.6,
                  marginBottom: 'var(--space-4)',
                }}
              >
                Accelerate technical evaluations from weeks to hours without compromising compliance or legal accountability.
              </p>

              <ul
                style={{
                  listStyle: 'none',
                  padding: 0,
                  margin: '0 0 var(--space-6) 0',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-2)',
                }}
              >
                {[
                  'Define and manage structured tender requirement criteria',
                  'Inspect automated AI extractions with confidence ratings',
                  'Cross-reference evidence against statutory registries',
                  'Conduct side-by-side document and evidence reviews',
                  'Record explicit decisions with timestamped audit logs',
                  'Prevent single-point corruption with traceable review chains',
                ].map((item) => (
                  <li key={item} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-size-sm)' }}>
                    <span style={{ color: 'var(--color-primary)', fontWeight: 'bold' }}>✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>

              <Link
                to="/signup?role=officer"
                style={{
                  padding: 'var(--space-3) var(--space-5)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: 'var(--font-weight-semibold)',
                  color: '#FFFFFF',
                  backgroundColor: 'var(--color-primary)',
                  border: 'none',
                  textDecoration: 'none',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                }}
              >
                <span>⚖️</span> Access Officer Portal
              </Link>
            </div>
          </div>
        </section>

        {/* 8. Product Principles Section */}
        <section
          id="principles"
          style={{
            backgroundColor: 'var(--color-bg-subtle)',
            borderTop: '1px solid var(--color-border)',
            borderBottom: '1px solid var(--color-border)',
            padding: 'var(--space-10) var(--space-4)',
          }}
        >
          <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', textAlign: 'center' }}>
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                fontWeight: 'var(--font-weight-bold)',
                color: 'var(--color-primary)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              Architectural Standard
            </span>
            <h2
              style={{
                fontSize: 'var(--font-size-2xl)',
                fontWeight: '700',
                margin: 'var(--space-2) 0 var(--space-8) 0',
              }}
            >
              Our Core Principles
            </h2>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: 'var(--space-4)',
              }}
            >
              {[
                { title: 'Evidence First', desc: 'No compliance claim is valid without verified, documented evidence.' },
                { title: 'Explainable', desc: 'Every evaluation produces an explicit human-readable justification.' },
                { title: 'Human Controlled', desc: 'Officers retain full decision authority; AI never acts autonomously.' },
                { title: 'Multi-Source', desc: 'Evidence verified against official registries (MCA, GSTN, PAN).' },
                { title: 'Auditable', desc: 'Every change, upload, review, and decision is written to an immutable audit trail.' },
              ].map((prin) => (
                <div
                  key={prin.title}
                  style={{
                    backgroundColor: 'var(--color-bg-card)',
                    padding: 'var(--space-5)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--color-border)',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ fontWeight: '600', fontSize: 'var(--font-size-base)', marginBottom: 'var(--space-1)', color: 'var(--color-primary)' }}>
                    {prin.title}
                  </div>
                  <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                    {prin.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 9. Final Role Selection Dual-Card CTA */}
        <section
          style={{
            padding: 'var(--space-10) var(--space-4)',
            maxWidth: 'var(--max-content-width)',
            margin: '0 auto',
            textAlign: 'center',
          }}
        >
          <h2
            style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: '700',
              marginBottom: 'var(--space-2)',
            }}
          >
            Ready to Take a Second Look?
          </h2>
          <p
            style={{
              fontSize: 'var(--font-size-base)',
              color: 'var(--color-text-secondary)',
              maxWidth: '560px',
              margin: '0 auto var(--space-8) auto',
            }}
          >
            Choose your workspace to begin evaluating tender requirements and compliance.
          </p>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: 'var(--space-6)',
              maxWidth: '800px',
              margin: '0 auto',
            }}
          >
            {/* Bidder Card */}
            <div
              style={{
                backgroundColor: 'var(--color-bg-card)',
                padding: 'var(--space-6)',
                borderRadius: 'var(--radius-lg)',
                border: '2px solid var(--color-success)',
                boxShadow: 'var(--shadow-sm)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                textAlign: 'left',
              }}
            >
              <div>
                <div style={{ fontSize: '32px', marginBottom: 'var(--space-2)' }}>🏢</div>
                <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: '700', margin: '0 0 var(--space-2) 0' }}>
                  I'm a Bidder
                </h3>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: '0 0 var(--space-6) 0' }}>
                  Submit and monitor your tender bids with automated document validation and pre-evaluation compliance guidance.
                </p>
              </div>
              <Link
                to="/signup?role=bidder"
                style={{
                  padding: 'var(--space-3)',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--color-success)',
                  color: '#FFFFFF',
                  textAlign: 'center',
                  fontWeight: 'var(--font-weight-semibold)',
                  fontSize: 'var(--font-size-sm)',
                  textDecoration: 'none',
                }}
              >
                Sign Up as Bidder
              </Link>
            </div>

            {/* Officer Card */}
            <div
              style={{
                backgroundColor: 'var(--color-bg-card)',
                padding: 'var(--space-6)',
                borderRadius: 'var(--radius-lg)',
                border: '2px solid var(--color-primary)',
                boxShadow: 'var(--shadow-sm)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                textAlign: 'left',
              }}
            >
              <div>
                <div style={{ fontSize: '32px', marginBottom: 'var(--space-2)' }}>⚖️</div>
                <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: '700', margin: '0 0 var(--space-2) 0' }}>
                  I'm a Procurement Officer
                </h3>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: '0 0 var(--space-6) 0' }}>
                  Evaluate tenders, verify compliance evidence, and record explicit review decisions with an immutable audit trail.
                </p>
              </div>
              <Link
                to="/signup?role=officer"
                style={{
                  padding: 'var(--space-3)',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--color-primary)',
                  color: '#FFFFFF',
                  textAlign: 'center',
                  fontWeight: 'var(--font-weight-semibold)',
                  fontSize: 'var(--font-size-sm)',
                  textDecoration: 'none',
                }}
              >
                Sign Up as Officer
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* 10. Public Footer */}
      <footer
        style={{
          backgroundColor: 'var(--color-bg-header)',
          borderTop: '1px solid var(--color-border)',
          padding: 'var(--space-8) var(--space-4)',
        }}
      >
        <div
          style={{
            maxWidth: 'var(--max-content-width)',
            margin: '0 auto',
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 'var(--space-4)',
          }}
        >
          <div>
            <div style={{ fontWeight: '700', fontSize: 'var(--font-size-base)', color: 'var(--color-primary)' }}>
              SecondLook
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
              AI-Powered Tender &amp; Bidder Compliance Engine
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-4)', fontSize: 'var(--font-size-xs)' }}>
            <Link to="/login" style={{ color: 'var(--color-text-secondary)', textDecoration: 'none' }}>
              Sign In
            </Link>
            <Link to="/signup?role=bidder" style={{ color: 'var(--color-text-secondary)', textDecoration: 'none' }}>
              Bidder Portal
            </Link>
            <Link to="/signup?role=officer" style={{ color: 'var(--color-text-secondary)', textDecoration: 'none' }}>
              Officer Portal
            </Link>
          </div>
        </div>

        <div
          style={{
            maxWidth: 'var(--max-content-width)',
            margin: 'var(--space-4) auto 0 auto',
            paddingTop: 'var(--space-4)',
            borderTop: '1px solid var(--color-border)',
            fontSize: '11px',
            color: 'var(--color-text-muted)',
            textAlign: 'center',
          }}
        >
          Designed for transparent, evidence-backed public procurement. All procurement decisions remain under human officer authority.
        </div>
      </footer>
    </div>
  );
}
