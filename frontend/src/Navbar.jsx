// frontend/src/Navbar.jsx
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';


function Navbar({ user, onLogout }) {
  const location = useLocation();
  const [imgError, setImgError] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const isActive = (path) => location.pathname === path ? 'active' : '';
  
  const toggleNavbar = () => setIsOpen(!isOpen);
  
  const closeNavbar = () => setIsOpen(false);

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container">
        <Link className="navbar-brand d-flex align-items-center" to="/home">
          {/* Display logo image or fallback emoji logo */}
          {!imgError ? (
            <img 
              src="/assets/logo.png"  // Assumes logo is in public/assets/
              alt="Manglo Logo"
              className="logo-image me-2"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="logo-circle me-2">
              <span className="logo-text">🥭</span>
            </div>
          )}

          <span className="brand-text">MANGLO</span>
        </Link>

        <button
          className="navbar-toggler"
          type="button"
          onClick={toggleNavbar}
          aria-expanded={isOpen}
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className={`collapse navbar-collapse ${isOpen ? 'show' : ''}`} id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/home')}`} to="/home" onClick={closeNavbar}>Home</Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/prediction')}`} to="/prediction" onClick={closeNavbar}>Prediction</Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/chatbot')}`} to="/chatbot" onClick={closeNavbar}>Chatbot</Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/about')}`} to="/about" onClick={closeNavbar}>About Us</Link>
            </li>
          </ul>

          <div className="d-flex align-items-center">
            <span className="navbar-text me-3">
              Welcome, {user?.email}
            </span>
            <button className="btn btn-outline-warning" onClick={() => {
              closeNavbar();
              onLogout();
            }}>
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;