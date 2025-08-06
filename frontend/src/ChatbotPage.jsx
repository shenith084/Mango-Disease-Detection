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
  const [streamingResponse, setStreamingResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const abortControllerRef = useRef(null);

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

  // Auto-scroll when messages change or streaming updates
  useEffect(() => {
    const timer = setTimeout(() => {
      scrollToBottom();
    }, 100);
    return () => clearTimeout(timer);
  }, [messages, streamingResponse]);

  // Force scroll when loading/streaming changes
  useEffect(() => {
    if (loading || isStreaming) {
      const timer = setTimeout(() => {
        scrollToBottom();
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [loading, isStreaming]);

  useEffect(() => {
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
      .replace(/\*{3,}/g, '')
      .replace(/#{1,}\s*/g, '')
      .replace(/\|/g, '')
      .replace(/\-{3,}/g, '')
      .replace(/_{3,}/g, '')
      .replace(/\s{3,}/g, ' ')
      .replace(/\n{3,}/g, '\n\n')
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
      let cleanLine = line.trim()
        .replace(/^\|+|\|+$/g, '')
        .replace(/\s+\|/g, '')
        .replace(/\|\s+/g, '')
        .trim();

      if (!cleanLine) return null;

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
      
      cleanLine = cleanLine
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
      
      return (
        <div key={index} className="response-line" dangerouslySetInnerHTML={{ __html: cleanLine }} />
      );
    }).filter(item => item !== null);
  };

  // New streaming chat function
  const handleStreamingChat = async (userMessage) => {
    if (!isAuthenticated) {
      const errorMessage = {
        type: 'bot',
        text: 'Please log in to use the chatbot feature.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      return;
    }

    setIsStreaming(true);
    setStreamingResponse('');
    
    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      // Prepare messages for streaming
      const conversationHistory = messages.map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.text
      }));

      // Add current user message
      conversationHistory.push({
        role: 'user',
        content: userMessage
      });

      const response = await fetch('http://localhost:5000/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ messages: conversationHistory }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              // Streaming finished - add complete message to history
              if (fullResponse.trim()) {
                const botMessage = {
                  type: 'bot',
                  text: fullResponse,
                  timestamp: new Date()
                };
                setMessages(prev => [...prev, botMessage]);
              }
              setStreamingResponse('');
              setIsStreaming(false);
              return;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                fullResponse += parsed.content;
                setStreamingResponse(fullResponse);
              }
            } catch (e) {
              // Skip invalid JSON
              continue;
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Stream aborted');
        return;
      }

      console.error('Streaming error:', error);
      
      // Fallback to regular chat on error
      try {
        const response = await fetch('http://localhost:5000/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ message: userMessage })
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
          throw new Error(data.error || 'Chat failed');
        }
      } catch (fallbackError) {
        const errorMessage = {
          type: 'bot',
          text: 'Sorry, I\'m having trouble connecting. Please check your internet connection and try again.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsStreaming(false);
      setStreamingResponse('');
      setLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading || isStreaming) return;

    // Add user message immediately
    const userMessage = {
      type: 'user',
      text: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentMessage = inputMessage;
    setInputMessage('');
    setLoading(true);

    // Use streaming chat
    await handleStreamingChat(currentMessage);
  };

  // Stop streaming function
  const stopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsStreaming(false);
    setStreamingResponse('');
    setLoading(false);
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
    if (!loading && !isStreaming && isAuthenticated) {
      setInputMessage(question);
      setTimeout(() => {
        const input = document.querySelector('.chat-input');
        if (input) input.focus();
      }, 100);
    }
  };

  const clearChat = async () => {
    // Stop any ongoing streaming
    stopStreaming();

    try {
      await fetch('http://localhost:5000/api/chat/clear', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Error clearing chat history:', error);
    }

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
                    {isStreaming && (
                      <span className="text-info ms-2">
                        <i className="fas fa-circle-notch fa-spin"></i> Thinking...
                      </span>
                    )}
                  </p>
                </div>
                <div className="header-actions">
                  {isStreaming && (
                    <button 
                      className="btn btn-sm btn-danger me-2"
                      onClick={stopStreaming}
                      title="Stop response"
                    >
                      <i className="fas fa-stop"></i>
                    </button>
                  )}
                  <button 
                    className="btn btn-sm btn-light clear-chat-btn"
                    onClick={clearChat}
                    title="Clear chat"
                    disabled={isStreaming}
                  >
                    <i className="fas fa-trash"></i>
                  </button>
                </div>
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
                  
                  {/* Show streaming response */}
                  {isStreaming && streamingResponse && (
                    <div className="message bot-message streaming-message">
                      <div className="message-avatar">
                        <i className="fas fa-robot"></i>
                      </div>
                      <div className="message-content">
                        <div className="message-text">
                          <div className="formatted-response">
                            {formatBotResponse(streamingResponse)}
                            <span className="streaming-cursor">|</span>
                          </div>
                        </div>
                        <div className="message-time">
                          <i className="fas fa-circle-notch fa-spin me-1"></i>
                          Typing...
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Show loading indicator when starting */}
                  {(loading && !isStreaming) && (
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
                    disabled={loading || isStreaming || !isAuthenticated}
                    autoComplete="off"
                  />
                  <button
                    type="submit"
                    className="btn btn-warning send-button"
                    disabled={loading || isStreaming || !inputMessage.trim() || !isAuthenticated}
                  >
                    {loading || isStreaming ? (
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
                      disabled={loading || isStreaming || !isAuthenticated}
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
                    <h6>Real-time Responses</h6>
                    <p>See answers appear as they're generated, just like ChatGPT</p>
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