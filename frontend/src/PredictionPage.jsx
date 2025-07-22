import React, { useState, useRef } from 'react';
import './PredictionPage.css';

function PredictionPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError('');
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setError('');
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select an image file');
      return;
    }

    setLoading(true);
    setError('');
    setPrediction(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);

      const response = await fetch('http://localhost:5000/api/predict', {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setPrediction(data);
      } else {
        setError(data.error || 'Prediction failed');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setPreview(null);
    setPrediction(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="prediction-page">
      <div className="container-fluid">
        <div className="row">
          {/* Left side - Upload */}
          <div className="col-lg-6 upload-section">
            <div className="upload-container">
              <h3 className="upload-title">
                Upload an image of a mango fruit to check for diseases.
              </h3>
              <p className="upload-subtitle">
                Drag and drop your image in here or click to select a file
              </p>

              <div 
                className="upload-area"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                {preview ? (
                  <div className="image-preview">
                    <img src={preview} alt="Preview" className="preview-image" />
                    <button 
                      className="btn btn-sm btn-danger remove-image"
                      onClick={(e) => {
                        e.stopPropagation();
                        resetForm();
                      }}
                    >
                      <i className="fas fa-times"></i>
                    </button>
                  </div>
                ) : (
                  <div className="upload-placeholder">
                    <i className="fas fa-cloud-upload-alt upload-icon"></i>
                    <p>Drag and drop your image here</p>
                  </div>
                )}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="d-none"
              />

              <button 
                className="btn btn-warning upload-btn"
                onClick={handleUpload}
                disabled={loading || !selectedFile}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" />
                    Analyzing...
                  </>
                ) : (
                  'Upload Images'
                )}
              </button>

              {error && (
                <div className="alert alert-danger mt-3" role="alert">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Right side - Results */}
          <div className="col-lg-6 results-section">
            <div className="results-container">
              <h3 className="results-title">Prediction Results</h3>
              
              {!prediction && !loading && (
                <div className="results-placeholder">
                  <p>Once an image is uploaded the prediction result will be displayed here, including the detected disease.</p>
                </div>
              )}

              {loading && (
                <div className="text-center py-4">
                  <div className="spinner-border text-warning" role="status">
                    <span className="visually-hidden">Analyzing...</span>
                  </div>
                  <p className="mt-2">Analyzing your image...</p>
                </div>
              )}

              {prediction && (
                <div className="prediction-results">
                  <div className="disease-detection">
                    <h5>Disease Detected</h5>
                    <div className={`disease-result ${prediction.disease === 'Healthy' ? 'healthy' : 'diseased'}`}>
                      {prediction.disease}
                    </div>
                    <div className="confidence-score">
                      Confidence: {Math.round(prediction.confidence * 100)}%
                    </div>
                  </div>

                  <div className="recommendations">
                    <h5>Recommendations</h5>
                    <div className="recommendation-text">
                      {prediction.recommendations || 'Based on the prediction, treatment will be provided here'}
                    </div>
                  </div>

                  <div className="action-buttons">
                    <button 
                      className="btn btn-outline-warning me-2"
                      onClick={resetForm}
                    >
                      Upload Another Image
                    </button>
                    <button 
                      className="btn btn-warning"
                      onClick={() => window.print()}
                    >
                      Save Results
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PredictionPage;