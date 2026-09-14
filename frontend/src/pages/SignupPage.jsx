import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import { useAuth } from '../auth/AuthContext.jsx';

const fieldStyle = {
  width: '100%',
  padding: 'var(--space-3)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--color-bg-page)',
  color: 'var(--color-text-primary)',
  fontSize: 'var(--font-size-sm)',
};

const roleOptions = [
  {
    value: 'BIDDER',
    title: 'Bidder',
    description: 'Submit bids and track compliance',
  },
  {
    value: 'OFFICER',
    title: 'Officer',
    description: 'Manage tenders and review bidders',
  },
];

export default function SignupPage() {
  const navigate = useNavigate();
  const { signUp, isConfigured, configurationError } = useAuth();
  const [role, setRole] = useState('BIDDER');
  const [form, setForm] = useState({
    email: '',
    password: '',
    fullName: '',
    legalName: '',
    registrationNumber: '',
    gstNumber: '',
    panNumber: '',
  });
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateField = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  const selectRole = (nextRole) => {
    setRole(nextRole);
    setError('');
    if (nextRole === 'OFFICER') {
      setForm((current) => ({
        ...current,
        legalName: '',
        registrationNumber: '',
        gstNumber: '',
        panNumber: '',
      }));
    }
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');
    if (!role) {
      setError('Please select an account type.');
      return;
    }
    if (!form.email.trim() || !form.password || !form.fullName.trim()) {
      setError('Email, password, and full name are required.');
      return;
    }
    if (role === 'BIDDER' && !form.legalName.trim()) {
      setError('Company name is required for bidder accounts.');
      return;
    }

    setIsSubmitting(true);
    try {
      const signupResult = await signUp({
        email: form.email.trim(),
        password: form.password,
        role,
        fullName: form.fullName.trim(),
        legalName: role === 'BIDDER' ? form.legalName.trim() : null,
        registrationNumber: role === 'BIDDER' ? form.registrationNumber : null,
        gstNumber: role === 'BIDDER' ? form.gstNumber : null,
        panNumber: role === 'BIDDER' ? form.panNumber : null,
      });

      if (signupResult?.requiresEmailConfirmation) {
        setSuccessMessage('Account created. Check your email to confirm your address, then sign in to continue.');
        return;
      }

      navigate(role === 'BIDDER' ? '/bidder' : '/officer');
    } catch (signupError) {
      setError(signupError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageContainer
      title="Create your SecondLook account"
      subtitle="Choose an account type before entering your registration details"
      maxWidth="820px"
    >
      <section
        style={{
          maxWidth: '640px',
          margin: '0 auto',
          padding: 'var(--space-6)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--color-bg-card)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <fieldset style={{ border: 0, display: 'grid', gap: 'var(--space-3)' }}>
          <legend style={{ fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-1)' }}>
            I am signing up as:
          </legend>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 'var(--space-3)' }}>
            {roleOptions.map((option) => {
              const selected = role === option.value;
              return (
                <label
                  key={option.value}
                  style={{
                    display: 'grid',
                    gap: 'var(--space-1)',
                    padding: 'var(--space-4)',
                    border: `2px solid ${selected ? 'var(--color-primary)' : 'var(--color-border)'}`,
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: selected ? 'var(--color-primary-subtle)' : 'var(--color-bg-subtle)',
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="radio"
                    name="role"
                    value={option.value}
                    checked={selected}
                    onChange={() => selectRole(option.value)}
                    style={{ position: 'absolute', opacity: 0 }}
                  />
                  <strong>{option.title}</strong>
                  <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                    {option.description}
                  </span>
                </label>
              );
            })}
          </div>
        </fieldset>

        <form onSubmit={submit} noValidate style={{ display: 'grid', gap: 'var(--space-4)', marginTop: 'var(--space-6)' }}>
          <label style={{ display: 'grid', gap: 'var(--space-1)', fontSize: 'var(--font-size-sm)' }}>
            Full name
            <input type="text" value={form.fullName} onChange={updateField('fullName')} style={fieldStyle} required />
          </label>
          <label style={{ display: 'grid', gap: 'var(--space-1)', fontSize: 'var(--font-size-sm)' }}>
            Email
            <input type="email" autoComplete="email" value={form.email} onChange={updateField('email')} style={fieldStyle} required />
          </label>
          <label style={{ display: 'grid', gap: 'var(--space-1)', fontSize: 'var(--font-size-sm)' }}>
            Password
            <input type="password" autoComplete="new-password" value={form.password} onChange={updateField('password')} style={fieldStyle} required />
          </label>

          {role === 'BIDDER' && (
            <div style={{ display: 'grid', gap: 'var(--space-4)', borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-4)' }}>
              <label style={{ display: 'grid', gap: 'var(--space-1)', fontSize: 'var(--font-size-sm)' }}>
                Company name
                <input type="text" value={form.legalName} onChange={updateField('legalName')} style={fieldStyle} required />
              </label>
              <label style={{ display: 'grid', gap: 'var(--space-1)', fontSize: 'var(--font-size-sm)' }}>
                Registration number <span style={{ color: 'var(--color-text-muted)' }}>(optional)</span>
                <input type="text" value={form.registrationNumber} onChange={updateField('registrationNumber')} style={fieldStyle} />
              </label>
              <label style={{ display: 'grid', gap: 'var(--space-1)', fontSize: 'var(--font-size-sm)' }}>
                GST number <span style={{ color: 'var(--color-text-muted)' }}>(optional)</span>
                <input type="text" value={form.gstNumber} onChange={updateField('gstNumber')} style={fieldStyle} />
              </label>
              <label style={{ display: 'grid', gap: 'var(--space-1)', fontSize: 'var(--font-size-sm)' }}>
                PAN number <span style={{ color: 'var(--color-text-muted)' }}>(optional)</span>
                <input type="text" value={form.panNumber} onChange={updateField('panNumber')} style={fieldStyle} />
              </label>
            </div>
          )}

          {!isConfigured && (
            <p role="alert" style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)' }}>
              {configurationError}
            </p>
          )}
          {error && (
            <p role="alert" style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)' }}>
              {error}
            </p>
          )}
          {successMessage && (
            <p role="status" style={{ color: 'var(--color-success)', fontSize: 'var(--font-size-sm)' }}>
              {successMessage}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !isConfigured}
            style={{
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--color-primary)',
              color: '#fff',
              fontWeight: 'var(--font-weight-semibold)',
              opacity: isSubmitting || !isConfigured ? 0.6 : 1,
            }}
          >
            {isSubmitting ? 'Creating account...' : 'Create account'}
          </button>
        </form>
      </section>
    </PageContainer>
  );
}
