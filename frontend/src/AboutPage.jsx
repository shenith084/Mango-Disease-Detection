import React from 'react';
import './AboutPage.css';

function AboutPage() {
  const teamMembers = [
    {
      name: "Dr. John Smith",
      role: "Agricultural Expert",
      image: "/api/placeholder/150/150",
      description: "Leading researcher in tropical fruit diseases with 15+ years experience"
    },
    {
      name: "Sarah Johnson",
      role: "AI Developer",
      image: "/api/placeholder/150/150",
      description: "Machine learning specialist focused on agricultural applications"
    },
    {
      name: "Mike Chen",
      role: "Full Stack Developer",
      image: "/api/placeholder/150/150",
      description: "Software engineer passionate about sustainable farming technology"
    },
    {
      name: "Dr. Priya Patel",
      role: "Plant Pathologist",
      image: "/api/placeholder/150/150",
      description: "Expert in mango disease identification and treatment strategies"
    }
  ];

  const features = [
    {
      icon: "fas fa-brain",
      title: "AI-Powered Detection",
      description: "Advanced machine learning algorithms trained on thousands of mango images for accurate disease identification"
    },
    {
      icon: "fas fa-mobile-alt",
      title: "Easy to Use",
      description: "Simple upload process - just take a photo and get instant results with treatment recommendations"
    },
    {
      icon: "fas fa-leaf",
      title: "Eco-Friendly",
      description: "Promotes sustainable farming practices and reduces unnecessary pesticide usage"
    },
    {
      icon: "fas fa-chart-line",
      title: "Track Progress",
      description: "Monitor your farm's health over time with detailed prediction history and analytics"
    },
    {
      icon: "fas fa-users",
      title: "Expert Support",
      description: "Access to agricultural experts and AI-powered chatbot for farming guidance"
    },
    {
      icon: "fas fa-globe",
      title: "Accessible",
      description: "Works on any device with internet connection, supporting farmers worldwide"
    }
  ];

  return (
    <div className="about-page">
      <div className="container">
        {/* Hero Section */}
        <div className="about-hero">
          <div className="row align-items-center">
            <div className="col-lg-6">
              <h1 className="about-title">About Manglo</h1>
              <p className="about-subtitle">
                Empowering farmers with AI-powered mango disease detection technology
              </p>
              <p className="about-description">
                Manglo is an innovative agricultural technology platform that combines artificial 
                intelligence with expert agricultural knowledge to help mango farmers protect their 
                crops and improve their harvest yields.
              </p>
            </div>
            <div className="col-lg-6">
              <div className="hero-image">
                <img
                  src="/api/placeholder/500/400"
                  alt="Mango farming"
                  className="img-fluid rounded"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Mission Section */}
        <div className="mission-section">
          <div className="row">
            <div className="col-12 text-center mb-5">
              <h2 className="section-title">Our Mission</h2>
            </div>
          </div>
          <div className="row">
            <div className="col-lg-4 mb-4">
              <div className="mission-card">
                <i className="fas fa-target mission-icon"></i>
                <h4>Early Detection</h4>
                <p>Enable farmers to detect mango diseases early, when treatment is most effective and cost-efficient</p>
              </div>
            </div>
            <div className="col-lg-4 mb-4">
              <div className="mission-card">
                <i className="fas fa-seedling mission-icon"></i>
                <h4>Sustainable Farming</h4>
                <p>Promote environmentally friendly farming practices that protect both crops and the ecosystem</p>
              </div>
            </div>
            <div className="col-lg-4 mb-4">
              <div className="mission-card">
                <i className="fas fa-handshake mission-icon"></i>
                <h4>Support Farmers</h4>
                <p>Provide accessible technology that empowers farmers with expert knowledge and actionable insights</p>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="features-section">
          <div className="row">
            <div className="col-12 text-center mb-5">
              <h2 className="section-title">Why Choose Manglo?</h2>
              <p className="section-subtitle">
                Discover the features that make Manglo the trusted choice for mango farmers
              </p>
            </div>
          </div>
          <div className="row">
            {features.map((feature, index) => (
              <div key={index} className="col-lg-4 col-md-6 mb-4">
                <div className="feature-card">
                  <i className={`${feature.icon} feature-icon`}></i>
                  <h5>{feature.title}</h5>
                  <p>{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Team Section */}
        <div className="team-section">
          <div className="row">
            <div className="col-12 text-center mb-5">
              <h2 className="section-title">Meet Our Team</h2>
              <p className="section-subtitle">
                Passionate experts dedicated to advancing agricultural technology
              </p>
            </div>
          </div>
          <div className="row">
            {teamMembers.map((member, index) => (
              <div key={index} className="col-lg-3 col-md-6 mb-4">
                <div className="team-card">
                  <div className="team-image">
                    <img
                      src={member.image}
                      alt={member.name}
                      className="img-fluid rounded-circle"
                    />
                  </div>
                  <h5 className="team-name">{member.name}</h5>
                  <p className="team-role">{member.role}</p>
                  <p className="team-description">{member.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Technology Section */}
        <div className="technology-section">
          <div className="row align-items-center">
            <div className="col-lg-6">
              <h2 className="section-title">Our Technology</h2>
              <p>
                Manglo uses state-of-the-art deep learning models trained on extensive datasets 
                of mango images. Our AI system can identify multiple disease types including:
              </p>
              <ul className="disease-list">
                <li><i className="fas fa-check text-success me-2"></i>Anthracnose</li>
                <li><i className="fas fa-check text-success me-2"></i>Bacterial Canker</li>
                <li><i className="fas fa-check text-success me-2"></i>Cutting Weevil</li>
                <li><i className="fas fa-check text-success me-2"></i>Die Back</li>
                <li><i className="fas fa-check text-success me-2"></i>Gall Midge</li>
                <li><i className="fas fa-check text-success me-2"></i>Powdery Mildew</li>
                <li><i className="fas fa-check text-success me-2"></i>Sooty Mould</li>
              </ul>
            </div>
            <div className="col-lg-6">
              <div className="tech-stats">
                <div className="stat-item">
                  <h3>95%</h3>
                  <p>Accuracy Rate</p>
                </div>
                <div className="stat-item">
                  <h3>10k+</h3>
                  <p>Images Trained</p>
                </div>
                <div className="stat-item">
                  <h3>8</h3>
                  <p>Disease Types</p>
                </div>
                <div className="stat-item">
                  <h3>24/7</h3>
                  <p>Availability</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Contact Section */}
        <div className="contact-section">
          <div className="row">
            <div className="col-12 text-center mb-5">
              <h2 className="section-title">Get in Touch</h2>
              <p className="section-subtitle">
                Have questions? We'd love to hear from you
              </p>
            </div>
          </div>
          <div className="row">
            <div className="col-md-4 mb-4">
              <div className="contact-info">
                <i className="fas fa-map-marker-alt contact-icon"></i>
                <h5>Address</h5>
                <p>Rajarata University of Sri Lanka, Mihintale</p>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="contact-info">
                <i className="fas fa-phone contact-icon"></i>
                <h5>Phone</h5>
                <p>041-0123456</p>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="contact-info">
                <i className="fas fa-envelope contact-icon"></i>
                <h5>Email</h5>
                <p>mangodisease@gmail.com</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AboutPage;