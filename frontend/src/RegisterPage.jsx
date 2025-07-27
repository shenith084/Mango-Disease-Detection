import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './RegisterPage.css';

function RegisterPage({ onLogin }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
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
  e.preventDefault(); // 🔴 VERY IMPORTANT to prevent default form behavior

  try {
    const response = await fetch('http://localhost:5000/api/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json', // ✅ This tells Flask to expect JSON
      },
      credentials: 'include',
      body: JSON.stringify({
        email: formData.email,
        password: formData.password
      })
    });

    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error('Error:', error);
  }
};


  const handleGoogleSignup = () => {
    // Implement Google OAuth signup
    console.log('Google signup clicked');
  };

  const handleFacebookSignup = () => {
    // Implement Facebook OAuth signup
    console.log('Facebook signup clicked');
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
                      minLength="6"
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
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn btn-primary w-100 mb-3"
                    disabled={loading}
                  >
                    {loading ? (
                      <span className="spinner-border spinner-border-sm me-2" />
                    ) : null}
                    Create Account
                  </button>
                </form>

                <div className="divider">
                  <span>or Continue with</span>
                </div>

                <div className="social-login">
                  <button
                    type="button"
                    className="btn btn-outline-secondary me-2"
                    onClick={handleGoogleSignup}
                  >
                    <i className="fab fa-google me-2"></i>
                    Google
                  </button>

                  <button
                    type="button"
                    className="btn btn-outline-secondary"
                    onClick={handleFacebookSignup}
                  >
                    <i className="fab fa-facebook-f me-2"></i>
                    Facebook
                  </button>
                </div>

                <div className="login-link">
                  <span>Already have an account? </span>
                  <Link to="/login">Sign in</Link>
                </div>
              </div>
            </div>
          </div>

          {/* Right side - Image */}
          <div className="col-lg-6 d-none d-lg-block">
            <div className="register-image">
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

export default RegisterPage;