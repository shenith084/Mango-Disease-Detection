import React, { useState, useRef, useEffect } from 'react';
import './ChatbotPage.css';

function ChatbotPage() {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: 'Hello! I\'m your mango disease assistant. I can help you with questions about mango diseases, treatments, and farming practices. How can I help you today?',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    // Add user message
    const userMessage = {
      type: 'user',
      text: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ message: inputMessage })
      });

      const data = await response.json();
      
      if (response.ok) {
        const botMessage = {
          type: 'bot',
          text: data.response,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, botMessage]);
      } else {
        const errorMessage = {
          type: 'bot',
          text: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        type: 'bot',
        text: 'Sorry, I\'m having trouble connecting. Please try again later.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const quickQuestions = [
    "What are common mango diseases?",
    "How to treat anthracnose?",
    "Signs of healthy mango trees?",
    "Best farming practices?",
    "Organic treatment options?"
  ];

  const handleQuickQuestion = (question) => {
    setInputMessage(question);
  };

  return (
    <div className="chatbot-page">
      <div className="container-fluid h-100">
        <div className="row h-100">
          {/* Chat Area */}
          <div className="col-lg-8">
            <div className="chat-container">
              <div className="chat-header">
                <h3 className="chat-title">
                  <i className="fas fa-robot me-2"></i>
                  Mango Disease Assistant
                </h3>
                <p className="chat-subtitle">Ask me anything about mango diseases and treatments</p>
              </div>
              
              <div className="chat-messages">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`message ${message.type === 'user' ? 'user-message' : 'bot-message'}`}
                  >
                    <div className="message-avatar">
                      {message.type === 'user' ? (
                        <i className="fas fa-user"></i>
                      ) : (
                        <i className="fas fa-robot"></i>
                      )}
                    </div>
                    <div className="message-content">
                      <div className="message-text">
                        {message.text}
                      </div>
                      <div className="message-time">
                        {message.timestamp.toLocaleTimeString([], { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </div>
                    </div>
                  </div>
                ))}
                
                {loading && (
                  <div className="message bot-message">
                    <div className="message-avatar">
                      <i className="fas fa-robot"></i>
                    </div>
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <form className="chat-input-form" onSubmit={handleSendMessage}>
                <div className="input-group">
                  <input
                    type="text"
                    className="form-control chat-input"
                    placeholder="Type your message here..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    disabled={loading}
                  />
                  <button
                    type="submit"
                    className="btn btn-warning send-button"
                    disabled={loading || !inputMessage.trim()}
                  >
                    <i className="fas fa-paper-plane"></i>
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Sidebar */}
          <div className="col-lg-4">
            <div className="chat-sidebar">
              <div className="quick-questions">
                <h5 className="sidebar-title">Quick Questions</h5>
                {quickQuestions.map((question, index) => (
                  <button
                    key={index}
                    className="btn btn-outline-warning quick-question-btn"
                    onClick={() => handleQuickQuestion(question)}
                  >
                    {question}
                  </button>
                ))}
              </div>

              <div className="chat-info">
                <h5 className="sidebar-title">About Assistant</h5>
                <div className="info-card">
                  <i className="fas fa-lightbulb info-icon"></i>
                  <div>
                    <h6>Expert Knowledge</h6>
                    <p>Get insights about mango diseases, treatments, and best practices</p>
                  </div>
                </div>
                <div className="info-card">
                  <i className="fas fa-clock info-icon"></i>
                  <div>
                    <h6>24/7 Available</h6>
                    <p>Ask questions anytime about your mango farming concerns</p>
                  </div>
                </div>
                <div className="info-card">
                  <i className="fas fa-leaf info-icon"></i>
                  <div>
                    <h6>Organic Solutions</h6>
                    <p>Learn about eco-friendly treatment options</p>
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

export default ChatbotPage;