// App.js
import React, { useState } from 'react';
import Chatbot from './Chatbot';
import './App.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPalette, faUserNurse } from '@fortawesome/free-solid-svg-icons'; // Using faPalette for paintbrush, faUserNurse for logo

function App() {
  const [theme, setTheme] = useState('dark');

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <div className={`App ${theme}`}>
      <div className="top-bar">
        <div className="top-bar-logo">
          <FontAwesomeIcon icon={faUserNurse} className="chatbot-logo" />
          <h1>Me-Lo AI</h1>
        </div>
        <div className="top-bar-right theme-switcher">
          <button
            className={`icon-button theme-toggle-button`}
            onClick={toggleTheme}
            title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
            aria-label={theme === 'light' ? 'Dark Mode' : 'Light Mode'}
          >
            <FontAwesomeIcon icon={faPalette} className="theme-icon" /> {/* Paintbrush Icon */}
          </button>
        </div>
      </div>

      {/* Main Content Area (Chatbot - Always Visible) */}
      <div className="main-content">
        <p className="chatbot-description">
          Me-Lo AI: Your AI-powered medical assistant. Powered by Llama 3 model and a medical data.
        </p>
         <Chatbot />
      </div>

      {/* Add Copyright Footer */}
      <footer className="copyright-footer">
        © {new Date().getFullYear()} LongevAI
      </footer>
    </div>
  );
}

export default App;