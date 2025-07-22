import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

function HomePage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/history', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setHistory(data.history);
      }
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <div className="container mt-4">
        {/* Welcome Section */}
        <div className="row mb-5">
          <div className="col-12">
            <div className="welcome-section">
              <h1 className="welcome-title">Welcome to Manglo Dashboard</h1>
              <p className="welcome-subtitle">
                Your smart companion for mango disease detection and management
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="row mb-5">
          <div className="col-md-4 mb-3">
            <div className="action-card">
              <div className="card-icon">
                <i className="fas fa-camera"></i>
              </div>
              <h5>Disease Detection</h5>
              <p>Upload mango images for instant AI-powered disease diagnosis</p>
              <Link to="/prediction" className="btn btn-warning">
                Start Prediction
              </Link>
            </div>
          </div>

          <div className="col-md-4 mb-3">
            <div className="action-card">
              <div className="card-icon">
                <i className="fas fa-comments"></i>
              </div>
              <h5>AI Assistant</h5>
              <p>Get expert advice and answers to your mango farming questions</p>
              <Link to="/chatbot" className="btn btn-warning">
                Chat Now
              </Link>
            </div>
          </div>

          <div className="col-md-4 mb-3">
            <div className="action-card">
              <div className="card-icon">
                <i className="fas fa-history"></i>
              </div>
              <h5>History</h5>
              <p>View your previous predictions and track your farm's health</p>
              <button 
                className="btn btn-warning"
                onClick={() => document.getElementById('history-section').scrollIntoView()}
              >
                View History
              </button>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="row mb-5">
          <div className="col-md-3 mb-3">
            <div className="stat-card">
              <div className="stat-number">{history.length}</div>
              <div className="stat-label">Total Predictions</div>
            </div>
          </div>
          <div className="col-md-3 mb-3">
            <div className="stat-card">
              <div className="stat-number">
                {history.filter(h => h.disease === 'Healthy').length}
              </div>
              <div className="stat-label">Healthy Crops</div>
            </div>
          </div>
          <div className="col-md-3 mb-3">
            <div className="stat-card">
              <div className="stat-number">
                {history.filter(h => h.disease !== 'Healthy').length}
              </div>
              <div className="stat-label">Diseases Detected</div>
            </div>
          </div>
          <div className="col-md-3 mb-3">
            <div className="stat-card">
              <div className="stat-number">
                {history.length > 0 ? 
                  Math.round(history.reduce((sum, h) => sum + h.confidence, 0) / history.length * 100) : 0}%
              </div>
              <div className="stat-label">Avg Confidence</div>
            </div>
          </div>
        </div>

        {/* Recent History */}
        <div className="row" id="history-section">
          <div className="col-12">
            <div className="history-section">
              <h3 className="section-title">Recent Predictions</h3>
              
              {loading ? (
                <div className="text-center py-4">
                  <div className="spinner-border text-warning" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                </div>
              ) : history.length === 0 ? (
                <div className="empty-history">
                  <i className="fas fa-leaf empty-icon"></i>
                  <h5>No predictions yet</h5>
                  <p>Start by uploading your first mango image for disease detection</p>
                  <Link to="/prediction" className="btn btn-warning">
                    Make First Prediction
                  </Link>
                </div>
              ) : (
                <div className="history-grid">
                  {history.slice(0, 6).map((item, index) => (
                    <div key={index} className="history-item">
                      <div className="history-header">
                        <span className={`disease-badge ${item.disease === 'Healthy' ? 'healthy' : 'diseased'}`}>
                          {item.disease}
                        </span>
                        <span className="prediction-date">
                          {new Date(item.date).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="confidence-bar">
                        <div 
                          className="confidence-fill"
                          style={{ width: `${item.confidence * 100}%` }}
                        ></div>
                      </div>
                      <div className="confidence-text">
                        Confidence: {Math.round(item.confidence * 100)}%
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tips Section */}
        <div className="row mt-5">
          <div className="col-12">
            <div className="tips-section">
              <h3 className="section-title">Quick Tips</h3>
              <div className="row">
                <div className="col-md-6">
                  <div className="tip-card">
                    <i className="fas fa-camera tip-icon"></i>
                    <h6>Best Photo Practices</h6>
                    <p>Take clear, well-lit photos of affected mango parts for accurate diagnosis</p>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="tip-card">
                    <i className="fas fa-clock tip-icon"></i>
                    <h6>Early Detection</h6>
                    <p>Regular monitoring helps catch diseases early when treatment is most effective</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


export default HomePage;