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
    // Implement Google OAuth login
    console.log('Google login clicked');
  };

  const handleFacebookLogin = () => {
    // Implement Facebook OAuth login
    console.log('Facebook login clicked');
  };

  return (
    <div className="login-page">
      <div className="container-fluid">
        <div className="row min-vh-100">
          {/* Left side - Form */}
          <div className="col-lg-6 d-flex align-items-center">
            <div className="login-form-container">
              <div className="brand-header mb-4">
                <Link to="/" className="brand-link">
                  <div className="logo-circle me-2">
                    <span className="logo-text">M</span>
                  </div>
                  <span className="brand-text">MANGLO</span>
                </Link>
              </div>

              <div className="login-form">
                <h2 className="form-title">Log in to your account</h2>
                <p className="form-subtitle">Welcome back! Please enter your details</p>

                {error && (
                  <div className="alert alert-danger" role="alert">
                    {error}
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
                    />
                  </div>

                  <div className="mb-3">
                    <input
                      type="password"
                      className="form-control"
                      name="password"
                      placeholder="Password"
                      value={formData.password}
                      onChange={handleChange}
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <Link to="/forgot-password" className="forgot-password-link">
                      Forget Password?
                    </Link>
                  </div>

                  <button
                    type="submit"
                    className="btn btn-primary w-100 mb-3"
                    disabled={loading}
                  >
                    {loading ? (
                      <span className="spinner-border spinner-border-sm me-2" />
                    ) : null}
                    Login
                  </button>
                </form>

                <div className="divider">
                  <span>or Continue with</span>
                </div>

                <div className="social-login">
                  <button
                    type="button"
                    className="btn btn-outline-secondary me-2"
                    onClick={handleGoogleLogin}
                  >
                    <i className="fab fa-google me-2"></i>
                    Google
                  </button>

                  <button
                    type="button"
                    className="btn btn-outline-secondary"
                    onClick={handleFacebookLogin}
                  >
                    <i className="fab fa-facebook-f me-2"></i>
                    Facebook
                  </button>
                </div>

                <div className="signup-link">
                  <span>Don't have an account? </span>
                  <Link to="/register">Create account</Link>
                </div>
              </div>
            </div>
          </div>

          {/* Right side - Image */}
          <div className="col-lg-6 d-none d-lg-block">
            <div className="login-image">
              <div className="image-overlay"></div>
              <img
                src="/api/placeholder/600/800"
                alt="Fresh mango in hands"
                className="img-fluid h-100 w-100 object-cover"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;