// frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

// Import components (adjusted paths — assuming they're all in src/)
import LandingPage from './LandingPage';
import LoginPage from './LoginPage';
import RegisterPage from './RegisterPage';
import HomePage from './HomePage';
import PredictionPage from './PredictionPage';
import ChatbotPage from './ChatbotPage';
import AboutPage from './AboutPage';
import Navbar from './Navbar';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/check-auth', {
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          setUser(data.user);
        }
      } catch (error) {
        console.error('Auth check error:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:5000/api/logout', {
        method: 'POST',
        credentials: 'include',
      });
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // Handle successful registration - redirect to login
  const handleRegistrationSuccess = () => {
    // You can add any success message or notification here
    console.log('Registration successful! Redirecting to login...');
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="spinner-border text-warning" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App" style={{ width: '100vw', height: '100vh', margin: 0, padding: 0 }}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/login"
            element={
              user ? <Navigate to="/home" /> : <LoginPage onLogin={handleLogin} />
            }
          />
          <Route
            path="/register"
            element={
              user ? (
                <Navigate to="/home" />
              ) : (
                <RegisterPage 
                  onLogin={handleLogin} 
                  onRegistrationSuccess={handleRegistrationSuccess}
                />
              )
            }
          />
          <Route
            path="/home"
            element={
              user ? (
                <>
                  <Navbar user={user} onLogout={handleLogout} />
                  <HomePage />
                </>
              ) : (
                <Navigate to="/login" />
              )
            }
          />
          <Route
            path="/prediction"
            element={
              user ? (
                <>
                  <Navbar user={user} onLogout={handleLogout} />
                  <PredictionPage />
                </>
              ) : (
                <Navigate to="/login" />
              )
            }
          />
          <Route
            path="/chatbot"
            element={
              user ? (
                <>
                  <Navbar user={user} onLogout={handleLogout} />
                  <ChatbotPage />
                </>
              ) : (
                <Navigate to="/login" />
              )
            }
          />
          <Route
            path="/about"
            element={
              user ? (
                <>
                  <Navbar user={user} onLogout={handleLogout} />
                  <AboutPage />
                </>
              ) : (
                <Navigate to="/login" />
              )
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;