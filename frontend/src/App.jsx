import React, { useState, useEffect, useRef } from 'react';
import Uploader from './components/Uploader';
import DocumentList from './components/DocumentList';
import ChatConsole from './components/ChatConsole';

const API_BASE_URL = "http://localhost:8080/api";

function App() {
  const [backendStatus, setBackendStatus] = useState("Connecting to API...");
  const [isOnline, setIsOnline] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [perfStats, setPerfStats] = useState(null);
  
  // RAG config states
  const [topK, setTopK] = useState(5);
  const [minSimilarity, setMinSimilarity] = useState(0.0);
  
  // Toast notifications state
  const [toasts, setToasts] = useState([]);

  // Check API health status
  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      const data = await response.json();
      if (data.status === "healthy") {
        setBackendStatus(`API Connected: ${data.llm_model}`);
        setIsOnline(true);
      } else {
        setBackendStatus("API Degradation Detected");
        setIsOnline(false);
      }
    } catch (err) {
      setBackendStatus("Offline - Cannot connect to backend");
      setIsOnline(false);
    }
  };

  // Fetch document inventory list
  const loadDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/documents`);
      if (!response.ok) throw new Error("Could not retrieve documents inventory");
      const data = await response.json();
      setDocuments(data);
    } catch (err) {
      addToast(err.message, "error");
    }
  };

  useEffect(() => {
    checkHealth();
    loadDocuments();
    
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Add toast helper
  const addToast = (message, type = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type, isFading: false }]);
    
    // Trigger fade-out 300ms before deletion (matching index.css fade-out duration)
    setTimeout(() => {
      setToasts(prev =>
        prev.map(t => t.id === id ? { ...t, isFading: true } : t)
      );
    }, 3700);

    // Remove toast completely
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  // Delete document
  const handleDeleteDocument = async (filename) => {
    if (!confirm(`Are you sure you want to delete '${filename}'? This deletes all associated vector indexes.`)) return;
    try {
      const response = await fetch(`${API_BASE_URL}/documents/${filename}`, {
        method: "DELETE"
      });
      if (!response.ok) throw new Error("Failed to delete document.");
      addToast(`Deleted document index: ${filename}`, "success");
      loadDocuments();
    } catch (err) {
      addToast(err.message, "error");
    }
  };

  // Submit search query
  const handleQuerySubmit = async (queryText) => {
    if (!queryText.trim()) return;

    // 1. Add user query message
    setChatMessages(prev => [...prev, { role: "user", text: queryText }]);
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: queryText,
          top_k: topK,
          min_similarity: minSimilarity
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Query execution failed.");
      }

      const data = await response.json();
      
      // 2. Add assistant message with full context matching data
      setChatMessages(prev => [...prev, {
        role: "assistant",
        text: data.answer,
        chunks: data.retrieved_chunks
      }]);
      
      // Set performance
      setPerfStats(data.performance);
    } catch (err) {
      setChatMessages(prev => [...prev, {
        role: "assistant",
        text: `System Error: ${err.message}`,
        isError: true
      }]);
      addToast(err.message, "error");
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="app-container">
      {/* Ambient background blur circles */}
      <div className="glow-sphere glow-purple"></div>
      <div className="glow-sphere glow-cyan"></div>

      {/* Header */}
      <header className="app-header">
        <div className="header-logo">
          <i className="fa-solid fa-circle-nodes logo-icon"></i>
          <div className="logo-text">
            <h1>Veri<span className="accent-text">Cite</span></h1>
            <span className="logo-sub">Fact-Checking & Attributed RAG</span>
          </div>
        </div>
        <div className="system-status">
          <span className={`status-indicator ${isOnline ? 'online' : 'offline'}`}></span>
          <span>{backendStatus}</span>
        </div>
      </header>

      {/* Grid Layout */}
      <main className="workspace-grid">
        {/* Left column: document manager */}
        <section className="workspace-panel ingestion-panel">
          <div className="panel-header">
            <h2><i className="fa-solid fa-cloud-arrow-up"></i> Document Ingestion</h2>
            <p className="panel-desc">Upload source documents to build your vector search index.</p>
          </div>

          <Uploader API_BASE_URL={API_BASE_URL} onUploadSuccess={loadDocuments} addToast={addToast} />

          <DocumentList 
            documents={documents} 
            onDelete={handleDeleteDocument} 
            onRefresh={loadDocuments} 
          />
        </section>

        {/* Right column: QA chat client */}
        <section className="workspace-panel qa-panel">
          <ChatConsole 
            messages={chatMessages}
            isTyping={isTyping}
            perfStats={perfStats}
            topK={topK}
            setTopK={setTopK}
            minSimilarity={minSimilarity}
            setMinSimilarity={setMinSimilarity}
            onSubmit={handleQuerySubmit}
            addToast={addToast}
          />
        </section>
      </main>

      {/* Toast Alert notifications */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type} ${toast.isFading ? 'fade-out' : ''}`}>
            <i className={`fa-solid ${
              toast.type === 'error' ? 'fa-triangle-exclamation' :
              toast.type === 'warning' ? 'fa-circle-exclamation' : 'fa-circle-check'
            }`}></i>
            <span>{toast.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
