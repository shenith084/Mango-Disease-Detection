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
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Improved scroll to bottom function
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end',
        inline: 'nearest'
      });
    }
  };

  // Auto-scroll when messages change
  useEffect(() => {
    const timer = setTimeout(() => {
      scrollToBottom();
    }, 100); // Small delay to ensure DOM is updated

    return () => clearTimeout(timer);
  }, [messages]);

  // Force scroll when loading changes
  useEffect(() => {
    if (loading) {
      const timer = setTimeout(() => {
        scrollToBottom();
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [loading]);

  useEffect(() => {
    // Check authentication status
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/check-auth', {
        method: 'GET',
        credentials: 'include',
      });
      const data = await response.json();
      setIsAuthenticated(data.authenticated);
    } catch (error) {
      console.error('Auth check error:', error);
      setIsAuthenticated(false);
    }
  };

  // Enhanced format bot response function
  const formatBotResponse = (text) => {
    if (!text) return '';

    // Clean up common markdown artifacts and unwanted characters
    let cleanedText = text
      // Remove excessive asterisks and markdown symbols
      .replace(/\*{3,}/g, '') // Remove 3+ asterisks
      .replace(/#{1,}\s*/g, '') // Remove hash symbols
      .replace(/\|/g, '') // Remove pipe symbols
      .replace(/\-{3,}/g, '') // Remove long dashes
      .replace(/_{3,}/g, '') // Remove long underscores
      // Clean up excessive whitespace
      .replace(/\s{3,}/g, ' ') // Replace 3+ spaces with single space
      .replace(/\n{3,}/g, '\n\n') // Replace 3+ newlines with double newline
      .trim();

    // Split by double newlines for paragraphs
    const paragraphs = cleanedText.split('\n\n').filter(p => p.trim());
    
    return paragraphs.map((paragraph, index) => {
      // Check if it's a header (starts with ** and ends with **)
      const headerMatch = paragraph.match(/^\*\*(.*?)\*\*/);
      if (headerMatch) {
        const headerText = headerMatch[1].trim();
        const remainingText = paragraph.replace(/^\*\*(.*?)\*\*/, '').trim();
        return (
          <div key={index} className="response-section">
            <h6 className="response-header">{headerText}</h6>
            {remainingText && <div className="response-content">{formatTextContent(remainingText)}</div>}
          </div>
        );
      }
      
      // Regular paragraph
      return (
        <div key={index} className="response-paragraph">
          {formatTextContent(paragraph)}
        </div>
      );
    });
  };

  // Enhanced format text content function
  const formatTextContent = (text) => {
    const lines = text.split('\n').filter(line => line.trim());
    
    return lines.map((line, index) => {
      // Remove leading/trailing whitespace and clean up the line
      let cleanLine = line.trim()
        .replace(/^\|+|\|+$/g, '') // Remove leading/trailing pipes
        .replace(/\s+\|/g, '') // Remove spaces before pipes
        .replace(/\|\s+/g, '') // Remove pipes followed by spaces
        .trim();

      // Skip empty lines after cleaning
      if (!cleanLine) return null;

      // Check for bullet points (• or -)
      if (cleanLine.startsWith('•') || cleanLine.startsWith('-')) {
        const bulletText = cleanLine.replace(/^[•-]\s*/, '').trim();
        if (!bulletText) return null;
        
        return (
          <div key={index} className="response-bullet">
            <span className="bullet-point">•</span>
            <span className="bullet-text">{bulletText}</span>
          </div>
        );
      }
      
      // Check for numbered lists
      const numberedMatch = cleanLine.match(/^(\d+)\.\s*(.+)/);
      if (numberedMatch) {
        const [, number, content] = numberedMatch;
        return (
          <div key={index} className="response-numbered">
            <span className="number-point">{number}.</span>
            <span className="numbered-text">{content.trim()}</span>
          </div>
        );
      }

      // Check for comparison or structured data (contains multiple sections separated by |)
      if (cleanLine.includes('|') && cleanLine.split('|').length > 2) {
        const parts = cleanLine.split('|').map(part => part.trim()).filter(part => part);
        if (parts.length > 1) {
          return (
            <div key={index} className="response-comparison">
              {parts.map((part, partIndex) => (
                <div key={partIndex} className="comparison-item">
                  {part}
                </div>
              ))}
            </div>
          );
        }
      }
      
      // Regular line - clean up any remaining markdown
      cleanLine = cleanLine
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold text
        .replace(/\*(.*?)\*/g, '<em>$1</em>'); // Italic text
      
      return (
        <div key={index} className="response-line" dangerouslySetInnerHTML={{ __html: cleanLine }} />
      );
    }).filter(item => item !== null); // Remove null items
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    if (!isAuthenticated) {
      const errorMessage = {
        type: 'bot',
        text: 'Please log in to use the chatbot feature.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      return;
    }

    // Add user message
    const userMessage = {
      type: 'user',
      text: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentMessage = inputMessage;
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ message: currentMessage })
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
        let errorText = 'Sorry, I encountered an error. Please try again.';
        
        if (response.status === 401) {
          errorText = 'Please log in to continue chatting.';
          setIsAuthenticated(false);
        } else if (data.error) {
          errorText = data.error;
        }
        
        const errorMessage = {
          type: 'bot',
          text: errorText,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        type: 'bot',
        text: 'Sorry, I\'m having trouble connecting. Please check your internet connection and try again.',
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
    "Organic treatment options?",
    "How to prevent black mould rot?",
    "What causes alternaria in mangoes?",
    "When to apply fungicides?"
  ];

  const handleQuickQuestion = (question) => {
    if (!loading && isAuthenticated) {
      setInputMessage(question);
      // Auto-focus input after setting question
      setTimeout(() => {
        const input = document.querySelector('.chat-input');
        if (input) input.focus();
      }, 100);
    }
  };

  const clearChat = async () => {
    try {
      // Call API to clear chat history
      await fetch('http://localhost:5000/api/chat/clear', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Error clearing chat history:', error);
    }

    // Clear local messages
    setMessages([
      {
        type: 'bot',
        text: 'Hello! I\'m your mango disease assistant. I can help you with questions about mango diseases, treatments, and farming practices. How can I help you today?',
        timestamp: new Date()
      }
    ]);
  };

  return (
    <div className="chatbot-page">
      <div className="container-fluid h-100">
        <div className="row h-100">
          {/* Chat Area */}
          <div className="col-lg-8">
            <div className="chat-container">
              <div className="chat-header">
                <div className="header-content">
                  <h3 className="chat-title">
                    <i className="fas fa-robot me-2"></i>
                    Mango Disease Assistant
                  </h3>
                  <p className="chat-subtitle">
                    Ask me anything about mango diseases and treatments
                    {!isAuthenticated && (
                      <span className="text-warning ms-2">
                        <i className="fas fa-exclamation-triangle"></i> Please log in to chat
                      </span>
                    )}
                  </p>
                </div>
                <button 
                  className="btn btn-sm btn-light clear-chat-btn"
                  onClick={clearChat}
                  title="Clear chat"
                >
                  <i className="fas fa-trash"></i>
                </button>
              </div>
              
              <div className="chat-messages" ref={messagesContainerRef}>
                <div className="messages-wrapper">
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
                          {message.type === 'bot' ? (
                            <div className="formatted-response">
                              {formatBotResponse(message.text)}
                            </div>
                          ) : (
                            message.text
                          )}
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
                        <div className="message-text">
                          <div className="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div ref={messagesEndRef} className="messages-end-marker" />
              </div>

              <form className="chat-input-form" onSubmit={handleSendMessage}>
                <div className="input-group">
                  <input
                    type="text"
                    className="form-control chat-input"
                    placeholder={isAuthenticated ? "Type your message here..." : "Please log in to chat..."}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    disabled={loading || !isAuthenticated}
                    autoComplete="off"
                  />
                  <button
                    type="submit"
                    className="btn btn-warning send-button"
                    disabled={loading || !inputMessage.trim() || !isAuthenticated}
                  >
                    {loading ? (
                      <i className="fas fa-spinner fa-spin"></i>
                    ) : (
                      <i className="fas fa-paper-plane"></i>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Sidebar */}
          <div className="col-lg-4">
            <div className="chat-sidebar">
              <div className="quick-questions">
                <h5 className="sidebar-title">
                  <i className="fas fa-bolt me-2"></i>
                  Quick Questions
                </h5>
                <div className="quick-questions-grid">
                  {quickQuestions.map((question, index) => (
                    <button
                      key={index}
                      className="btn btn-outline-warning quick-question-btn"
                      onClick={() => handleQuickQuestion(question)}
                      disabled={loading || !isAuthenticated}
                    >
                      <i className="fas fa-arrow-right me-2"></i>
                      {question}
                    </button>
                  ))}
                </div>
              </div>

              <div className="chat-info">
                <h5 className="sidebar-title">
                  <i className="fas fa-info-circle me-2"></i>
                  About Assistant
                </h5>
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
                <div className="info-card">
                  <i className="fas fa-database info-icon"></i>
                  <div>
                    <h6>Disease Database</h6>
                    <p>Covers Alternaria, Anthracnose, Black Mould Rot, and more</p>
                  </div>
                </div>
              </div>

              {!isAuthenticated && (
                <div className="auth-notice">
                  <div className="alert alert-warning">
                    <i className="fas fa-info-circle"></i>
                    <strong>Login Required</strong><br/>
                    Please log in to your account to use the chatbot feature.
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

export default ChatbotPage;