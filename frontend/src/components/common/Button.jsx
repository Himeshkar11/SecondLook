import React from 'react';

/**
 * Reusable Button component
 * Variants: primary, secondary, success, warning, danger, ghost
 */
export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  type = 'button',
  className = '',
  ...props
}) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: 'inherit',
    fontWeight: 'var(--font-weight-medium)',
    borderRadius: 'var(--radius-sm)',
    transition: 'background-color var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1,
    border: '1px solid transparent',
  };

  const sizes = {
    sm: {
      padding: 'var(--space-1) var(--space-2)',
      fontSize: 'var(--font-size-xs)',
      height: '28px',
    },
    md: {
      padding: 'var(--space-2) var(--space-4)',
      fontSize: 'var(--font-size-sm)',
      height: '36px',
    },
    lg: {
      padding: 'var(--space-3) var(--space-5)',
      fontSize: 'var(--font-size-base)',
      height: '42px',
    },
  };

  const variants = {
    primary: {
      backgroundColor: 'var(--color-primary)',
      color: 'var(--color-text-inverse)',
      borderColor: 'var(--color-primary)',
    },
    secondary: {
      backgroundColor: 'var(--color-bg-card)',
      color: 'var(--color-text-primary)',
      borderColor: 'var(--color-border)',
    },
    success: {
      backgroundColor: 'var(--color-success)',
      color: 'var(--color-text-inverse)',
      borderColor: 'var(--color-success)',
    },
    warning: {
      backgroundColor: 'var(--color-warning)',
      color: 'var(--color-text-inverse)',
      borderColor: 'var(--color-warning)',
    },
    danger: {
      backgroundColor: 'var(--color-danger)',
      color: 'var(--color-text-inverse)',
      borderColor: 'var(--color-danger)',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: 'var(--color-text-primary)',
      borderColor: 'transparent',
    },
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      style={{
        ...baseStyles,
        ...sizes[size],
        ...variants[variant],
      }}
      className={`sl-button ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
