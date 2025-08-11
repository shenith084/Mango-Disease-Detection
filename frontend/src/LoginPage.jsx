import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './LoginPage.css';

function LoginPage({ onLogin }) {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        onLogin(data.user);
        navigate('/home');
      } else {
        setError(data.error || 'Login failed');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    console.log('Google login clicked');
    // Implement Google OAuth logic here
  };

  const handleFacebookLogin = () => {
    console.log('Facebook login clicked');
    // Implement Facebook OAuth logic here
  };

  return (
    <div className="manglo-login-page">
      {/* Left Section - Login Form */}
      <div className="manglo-login-section">
        <div className="manglo-login-container">
          <div className="manglo-form-wrapper">
            
            {/* Brand Header */}
            <div className="manglo-brand-section">
              <Link to="/" className="manglo-brand-link">
                <div className="manglo-logo-circle">
                  <span className="manglo-logo-text">M</span>
                </div>
                <span className="manglo-brand-text">MANGLO</span>
              </Link>
            </div>

            {/* Form Content */}
            <div className="manglo-form-content">
              <h1 className="manglo-form-title">Log in to your account</h1>
              <p className="manglo-form-subtitle">Welcome back! Please enter your details</p>

              {error && (
                <div className="manglo-error-alert">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="manglo-login-form">
                <div className="manglo-input-group">
                  <label htmlFor="email">E-mail</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    placeholder="Enter your email"
                    value={formData.email}
                    onChange={handleChange}
                    className="manglo-input-field"
                    required
                  />
                </div>

                <div className="manglo-input-group">
                  <label htmlFor="password">Password</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleChange}
                    className="manglo-input-field"
                    required
                  />
                </div>

                <div className="manglo-forgot-section">
                  <Link to="/forgot-password" className="manglo-forgot-link">
                    Forget Password?
                  </Link>
                </div>

                <button
                  type="submit"
                  className="manglo-login-btn"
                  disabled={loading}
                >
                  {loading && <span className="manglo-spinner"></span>}
                  Login
                </button>
              </form>

              <div className="manglo-divider">
                <span>Or Continue with</span>
              </div>

              <div className="manglo-social-buttons">
                <button
                  type="button"
                  className="manglo-social-btn manglo-google-btn"
                  onClick={handleGoogleLogin}
                >
                  <span className="manglo-social-icon">G</span>
                  Google
                </button>

                <button
                  type="button"
                  className="manglo-social-btn manglo-facebook-btn"
                  onClick={handleFacebookLogin}
                >
                  <span className="manglo-social-icon">f</span>
                  Facebook
                </button>
              </div>

              <div className="manglo-signup-section">
                <span>Don't have an account? </span>
                <Link to="/register" className="manglo-signup-link">Create account</Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Section - Background Image */}
      <div className="manglo-image-section">
        {/* Background image is handled by CSS */}
      </div>
    </div>
  );
}

export default LoginPage;