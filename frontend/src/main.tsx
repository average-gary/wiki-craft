import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Set initial theme - dark by default, respect system preference
const getInitialTheme = () => {
  const stored = localStorage.getItem('theme');
  if (stored === 'light' || stored === 'dark') {
    return stored;
  }
  // Default to dark unless system prefers light
  if (window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light';
  }
  return 'dark';
};

// Apply theme immediately to prevent flash
const theme = getInitialTheme();
if (theme === 'dark') {
  document.documentElement.classList.add('dark');
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
