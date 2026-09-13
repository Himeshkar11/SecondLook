import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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

export default function LoginPage() {
  const navigate = useNavigate();
  const { signIn, user, isLoading, isConfigured, configurationError, identityError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    if (!email.trim() || !password) {
      setError('Email and password are required.');
      return;
    }

    setIsSubmitting(true);
    try {
      await signIn(email.trim(), password);
      navigate('/dashboard');
    } catch (signInError) {
      setError(signInError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageContainer
      title="Portal Access"
      subtitle="Sign in with your SecondLook account"
      maxWidth="720px"
    >
      <section
        style={{
          maxWidth: '440px',
          margin: '0 auto',
          padding: 'var(--space-6)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--color-bg-card)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        {user ? (
          <div role="status" style={{ display: 'grid', gap: 'var(--space-3)' }}>
            <strong>Already signed in</strong>
            <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
              {user.email}
            </p>
            {identityError && (
              <p role="alert" style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)' }}>
                {identityError}
              </p>
            )}
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              style={{
                padding: 'var(--space-3)',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--color-primary)',
                color: '#fff',
                fontWeight: 'var(--font-weight-semibold)',
              }}
            >
              Continue to portal
            </button>
          </div>
        ) : (
          <form onSubmit={submit} noValidate style={{ display: 'grid', gap: 'var(--space-4)' }}>
            <label style={{ display: 'grid', gap: 'var(--space-1)', fontSize: 'var(--font-size-sm)' }}>
              Email
              <input
                type="email"
                name="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                style={fieldStyle}
                required
              />
            </label>
            <label style={{ display: 'grid', gap: 'var(--space-1)', fontSize: 'var(--font-size-sm)' }}>
              Password
              <input
                type="password"
                name="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                style={fieldStyle}
                required
              />
            </label>

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

            <button
              type="submit"
              disabled={isLoading || isSubmitting || !isConfigured}
              style={{
                padding: 'var(--space-3)',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--color-primary)',
                color: '#fff',
                fontWeight: 'var(--font-weight-semibold)',
                opacity: isLoading || isSubmitting || !isConfigured ? 0.6 : 1,
              }}
            >
              {isSubmitting ? 'Signing in...' : 'Sign in'}
            </button>
            <p style={{ textAlign: 'center', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
              Need an account? <Link to="/signup">Create one</Link>
            </p>
          </form>
        )}
      </section>
    </PageContainer>
  );
}
