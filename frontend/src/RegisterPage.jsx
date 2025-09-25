import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './RegisterPage.css';

function RegisterPage({ onLogin, onRegistrationSuccess }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Reset messages
    setError('');
    setSuccess('');
    
    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    // Validate password length
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });

      const data = await response.json();
      console.log('Registration response:', data);

      if (response.ok) {
        // Registration successful
        setSuccess('Registration successful! Redirecting to login...');
        
        // Call the success callback if provided
        if (onRegistrationSuccess) {
          onRegistrationSuccess();
        }
        
        // Clear the form
        setFormData({
          email: '',
          password: '',
          confirmPassword: ''
        });
        
        // Redirect to login page after 2 seconds
        setTimeout(() => {
          navigate('/login');
        }, 2000);
        
      } else {
        // Registration failed
        setError(data.error || 'Registration failed. Please try again.');
      }
      
    } catch (error) {
      console.error('Registration error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = () => {
    console.log('Google signup clicked');
    // Implement Google OAuth signup
  };

  const handleFacebookSignup = () => {
    console.log('Facebook signup clicked');
    // Implement Facebook OAuth signup
  };

  return (
    <div className="manglo-register-page">
      {/* Left Section - Registration Form */}
      <div className="manglo-register-section">
        <div className="manglo-register-container">
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
              <h1 className="manglo-form-title">Create your account</h1>
              <p className="manglo-form-subtitle">Join Manglo to protect your mango crops with AI-powered disease detection</p>

              {error && (
                <div className="manglo-error-alert">
                  {error}
                </div>
              )}

              {success && (
                <div className="manglo-success-alert">
                  {success}
                </div>
              )}

              <form onSubmit={handleSubmit} className="manglo-register-form">
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
                    disabled={success}
                  />
                </div>

                <div className="manglo-input-group">
                  <label htmlFor="password">Password</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    placeholder="Create a password (min 6 characters)"
                    value={formData.password}
                    onChange={handleChange}
                    className="manglo-input-field"
                    required
                    minLength="6"
                    disabled={success}
                  />
                </div>

                <div className="manglo-input-group">
                  <label htmlFor="confirmPassword">Confirm Password</label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className="manglo-input-field"
                    required
                    minLength="6"
                    disabled={success}
                  />
                </div>

                <button
                  type="submit"
                  className="manglo-register-btn"
                  disabled={loading || success}
                >
                  {loading && <span className="manglo-spinner"></span>}
                  {success ? 'Account Created!' : loading ? 'Creating Account...' : 'Create Account'}
                </button>
              </form>

              {/* Only show social login if not successful */}
              {!success && (
                <>
                  <div className="manglo-divider">
                    <span>Or Continue with</span>
                  </div>

                  <div className="manglo-social-buttons">
                    <button
                      type="button"
                      className="manglo-social-btn manglo-google-btn"
                      onClick={handleGoogleSignup}
                      disabled={loading}
                    >
                      <span className="manglo-social-icon">G</span>
                      Google
                    </button>

                    <button
                      type="button"
                      className="manglo-social-btn manglo-facebook-btn"
                      onClick={handleFacebookSignup}
                      disabled={loading}
                    >
                      <span className="manglo-social-icon">f</span>
                      Facebook
                    </button>
                  </div>
                </>
              )}

              <div className="manglo-signin-section">
                <span>Already have an account? </span>
                <Link to="/login" className="manglo-signin-link">Sign in</Link>
              </div>

              {/* Show redirect message when successful */}
              {success && (
                <div className="manglo-redirect-info">
                  <span>Redirecting to login page in 2 seconds...</span>
                </div>
              )}
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

export default RegisterPage;