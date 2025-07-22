import React from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

function LandingPage() {
  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="navbar navbar-expand-lg navbar-dark">
        <div className="container">
          <Link className="navbar-brand d-flex align-items-center" to="/">
            <div className="logo-circle me-2">
              <span className="logo-text">M</span>
            </div>
            <span className="brand-text">MANGLO</span>
          </Link>
          
          <button 
            className="navbar-toggler" 
            type="button" 
            data-bs-toggle="collapse" 
            data-bs-target="#navbarNav"
          >
            <span className="navbar-toggler-icon"></span>
          </button>
          
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto">
              <li className="nav-item">
                <Link className="nav-link" to="/">Home</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/prediction">Prediction</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/chatbot">Chatbot</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/about">About Us</Link>
              </li>
            </ul>
            
            <div className="d-flex">
              <Link to="/login" className="btn btn-outline-light me-2">Log In</Link>
              <Link to="/register" className="btn btn-warning">Sign Up</Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="container">
          <div className="row align-items-center min-vh-100">
            <div className="col-lg-6">
              <h1 className="hero-title">
                Welcome to Manglo
              </h1>
              <h2 className="hero-subtitle">
                The Smart Way to Protect Your Mangoes.........
              </h2>
              
              <ul className="hero-features">
                <li>
                  <i className="fas fa-upload me-2"></i>
                  Upload fruit image
                </li>
                <li>
                  <i className="fas fa-brain me-2"></i>
                  Get instant AI-powered diagnosis
                </li>
                <li>
                  <i className="fas fa-lightbulb me-2"></i>
                  Receive expert tips for treatment
                </li>
                <li>
                  <i className="fas fa-shield-alt me-2"></i>
                  Save crops, reduce pesticide use, and boost yield
                </li>
              </ul>
              
              <p className="hero-tagline">
                <em>Protect your farm. Improve your harvest. Trust Manglo !</em>
              </p>
            </div>
            
            <div className="col-lg-6">
              <div className="hero-image">
                <div className="mango-display">
                  <img 
                    src="/api/placeholder/400/300" 
                    alt="Fresh mangoes" 
                    className="img-fluid rounded"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="contact-section py-5">
        <div className="container">
          <div className="row">
            <div className="col-12 text-center mb-5">
              <h2 className="section-title">Get In Touch</h2>
            </div>
          </div>
          
          <div className="row">
            <div className="col-md-4">
              <div className="contact-card">
                <div className="contact-icon">
                  <i className="fas fa-map-marker-alt"></i>
                </div>
                <h5>Address</h5>
                <p>Rajarata University of Sri Lanka, Mihintale</p>
              </div>
            </div>
            
            <div className="col-md-4">
              <div className="contact-card">
                <div className="contact-icon">
                  <i className="fas fa-phone"></i>
                </div>
                <h5>Phone Number</h5>
                <p>041-0123456</p>
              </div>
            </div>
            
            <div className="col-md-4">
              <div className="contact-card">
                <div className="contact-icon">
                  <i className="fas fa-envelope"></i>
                </div>
                <h5>E-mail</h5>
                <p>mangodisease@gmail.com</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <div className="row">
            <div className="col-md-6">
              <p className="mb-0">© 2025 Manglo. All right reserved.</p>
            </div>
            <div className="col-md-6 text-md-end">
              <Link to="/terms" className="footer-link me-3">Terms of use</Link>
              <Link to="/privacy" className="footer-link">Privacy Policy</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;