import React, { useState } from 'react';
import Header from './Header.jsx';
import Sidebar from './Sidebar.jsx';

/**
 * Main application layout wrapper
 * Desktop: persistent sidebar + top header
 * Mobile/tablet: collapsible sidebar drawer
 */
export default function MainLayout({ children }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)} />
      <div style={{ display: 'flex', flex: 1, position: 'relative' }}>
        <Sidebar
          isOpen={isSidebarOpen}
          onCloseMobile={() => setIsSidebarOpen(false)}
        />
        {/* Mobile backdrop */}
        {isSidebarOpen && (
          <div
            onClick={() => setIsSidebarOpen(false)}
            style={{
              position: 'fixed',
              top: 'var(--header-height)',
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(15, 23, 42, 0.4)',
              zIndex: 40,
            }}
            className="sl-sidebar-backdrop"
          />
        )}
        <main
          style={{
            flex: 1,
            backgroundColor: 'var(--color-bg-page)',
            minWidth: 0,
            overflowY: 'auto',
          }}
        >
          {children}
        </main>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .sl-sidebar {
            position: fixed !important;
            top: var(--header-height) !important;
            left: -100%;
            height: calc(100vh - var(--header-height)) !important;
            transition: left 200ms ease-in-out;
            box-shadow: var(--shadow-md);
          }
          .sl-sidebar.sl-sidebar-open {
            left: 0 !important;
          }
          .sl-page-container {
            padding: var(--space-4) !important;
          }
        }
        @media (min-width: 769px) {
          .sl-header-sub {
            display: inline !important;
          }
          .sl-sidebar-backdrop {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
