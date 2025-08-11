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
  const [imageError, setImageError] = useState(false);
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
    // Implement Google OAuth signup
    console.log('Google signup clicked');
    // You can implement this later
  };

  const handleFacebookSignup = () => {
    // Implement Facebook OAuth signup
    console.log('Facebook signup clicked');
    // You can implement this later
  };

  const handleImageError = () => {
    setImageError(true);
  };

  return (
    <div className="register-page">
      <div className="container-fluid">
        <div className="row min-vh-100">
          {/* Left side - Form */}
          <div className="col-lg-6 d-flex align-items-center">
            <div className="register-form-container">
              <div className="brand-header mb-4">
                <Link to="/" className="brand-link">
                  <div className="logo-circle me-2">
                    <span className="logo-text">M</span>
                  </div>
                  <span className="brand-text">MANGLO</span>
                </Link>
              </div>

              <div className="register-form">
                <h2 className="form-title">Create your account</h2>
                <p className="form-subtitle">Join Manglo to protect your mango crops</p>

                {error && (
                  <div className="alert alert-danger" role="alert">
                    <i className="fas fa-exclamation-triangle me-2"></i>
                    {error}
                  </div>
                )}

                {success && (
                  <div className="alert alert-success" role="alert">
                    <i className="fas fa-check-circle me-2"></i>
                    {success}
                  </div>
                )}

                <form onSubmit={handleSubmit}>
                  <div className="mb-3">
                    <input
                      type="email"
                      className="form-control"
                      name="email"
                      placeholder="E-mail"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      disabled={success}
                    />
                  </div>

                  <div className="mb-3">
                    <input
                      type="password"
                      className="form-control"
                      name="password"
                      placeholder="Password (min 6 characters)"
                      value={formData.password}
                      onChange={handleChange}
                      required
                      minLength="6"
                      disabled={success}
                    />
                  </div>

                  <div className="mb-3">
                    <input
                      type="password"
                      className="form-control"
                      name="confirmPassword"
                      placeholder="Confirm Password"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      required
                      minLength="6"
                      disabled={success}
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn btn-primary w-100 mb-3"
                    disabled={loading || success}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Creating Account...
                      </>
                    ) : success ? (
                      <>
                        <i className="fas fa-check me-2"></i>
                        Account Created!
                      </>
                    ) : (
                      'Create Account'
                    )}
                  </button>
                </form>

                {/* Only show social login if not successful */}
                {!success && (
                  <>
                    <div className="divider">
                      <span>or Continue with</span>
                    </div>

                    <div className="social-login">
                      <button
                        type="button"
                        className="btn btn-outline-secondary me-2"
                        onClick={handleGoogleSignup}
                        disabled={loading}
                      >
                        <i className="fab fa-google me-2"></i>
                        Google
                      </button>

                      <button
                        type="button"
                        className="btn btn-outline-secondary"
                        onClick={handleFacebookSignup}
                        disabled={loading}
                      >
                        <i className="fab fa-facebook-f me-2"></i>
                        Facebook
                      </button>
                    </div>
                  </>
                )}

                <div className="login-link">
                  <span>Already have an account? </span>
                  <Link to="/login">Sign in</Link>
                </div>

                {/* Show redirect message when successful */}
                {success && (
                  <div className="text-center mt-3">
                    <small className="text-muted">
                      <i className="fas fa-clock me-1"></i>
                      Redirecting to login page in 2 seconds...
                    </small>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right side - Image */}
          <div className="col-lg-6 d-none d-lg-block">
            <div className="register-image">
              <div className="image-overlay"></div>
              {imageError ? (
                // Fallback content when image fails
                <div className="placeholder-content d-flex align-items-center justify-content-center h-100">
                  <div className="text-center text-white">
                    <i className="fas fa-seedling fa-5x mb-3 opacity-50"></i>
                    <h3>Growing Success</h3>
                    <p>Protect your mango crops with AI-powered disease detection</p>
                  </div>
                </div>
              ) : (
                <img
                  src=""
                  alt="Fresh mango in hands"
                  className="img-fluid h-100 w-100 object-cover"
                  onError={handleImageError}
                  onLoad={() => console.log('Image loaded successfully')}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;