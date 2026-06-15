import React, { useState, useEffect, useRef } from 'react';

function ChatConsole({
  messages,
  isTyping,
  perfStats,
  topK,
  setTopK,
  minSimilarity,
  setMinSimilarity,
  onSubmit,
  addToast
}) {
  const [queryInput, setQueryInput] = useState("");
  const viewportRef = useRef(null);
  const [openDrawers, setOpenDrawers] = useState({});

  // Auto-scroll to bottom of chat when messages grow
  useEffect(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTo({
        top: viewportRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isTyping]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!queryInput.trim()) return;
    onSubmit(queryInput);
    setQueryInput("");
  };

  const handleExampleClick = (queryText) => {
    setQueryInput(queryText);
  };

  const toggleDrawer = (index) => {
    setOpenDrawers(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Glow source card fragments when its citations marker gets clicked
  const highlightChunk = (sourceName, pageNum) => {
    const cleanSource = sourceName.replace(/[^a-zA-Z0-9]/g, '');
    const matchedCard = document.querySelector(`[id^="chunk-${cleanSource}-${pageNum}-"]`);

    if (matchedCard) {
      // Find parent attribution title to click it open if it's closed
      const parentAttributionBox = matchedCard.closest('.attributions-box');
      if (parentAttributionBox) {
        const titleEl = parentAttributionBox.querySelector('.attributions-title');
        if (titleEl && !titleEl.classList.contains('open')) {
          titleEl.click();
        }
      }

      // Smooth scroll to chunk card
      setTimeout(() => {
        matchedCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        matchedCard.style.boxShadow = "0 0 20px #06b6d4";
        matchedCard.style.borderColor = "#06b6d4";

        setTimeout(() => {
          matchedCard.style.boxShadow = "";
          matchedCard.style.borderColor = "";
        }, 3000);

        addToast(`Scrolled to matched chunk in citations panel.`, "success");
      }, 100);
    } else {
      addToast(`Attributed chunk details for ${sourceName} p.${pageNum} not included in current top list.`, "warning");
    }
  };

  // Convert markdown to HTML tags supporting click citations
  const renderMarkdown = (text) => {
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Headings
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold, italic and code formatting
    html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');

    // Unordered lists
    html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');

    // Split paragraphs
    html = html.split('\n').map(line => {
      const trimmed = line.trim();
      if (!trimmed) return '';
      if (trimmed.startsWith('<h') || trimmed.startsWith('<li') || trimmed.startsWith('<ul')) return line;
      return `<p>${line}</p>`;
    }).join('\n');

    return { __html: html };
  };

  // Custom click handler interceptor for inline citations links inside generated HTML
  const handleChatClick = (e) => {
    const citationLink = e.target.closest('.citation-link');
    if (citationLink) {
      const source = citationLink.getAttribute('data-source');
      const page = parseInt(citationLink.getAttribute('data-page'));
      highlightChunk(source, page);
    }
  };

  // Replace standard bracket citation tags with clickable elements dynamically
  const parseResponseWithCitations = (answerText) => {
    const citationRegex = /\[Source:\s*([^,\]]+),\s*page\s*(\d+)\]/g;
    let text = answerText;
    
    // Parse markdown structures
    const htmlObj = renderMarkdown(text);
    
    // Replace markdown citation strings with clickable data elements
    const updatedHtml = htmlObj.__html.replace(citationRegex, (match, source, page) => {
      return `<span class="citation-link" data-source="${source}" data-page="${page}"><i class="fa-solid fa-feather-pointed"></i> ${source} p.${page}</span>`;
    });
    
    return { __html: updatedHtml };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', flex: 1 }}>
      {/* Messages viewport box */}
      <div className="chat-viewport" ref={viewportRef} onClick={handleChatClick}>
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <i className="fa-solid fa-quote-right quote-watermark"></i>
            <h3>Ask Your Corpus</h3>
            <p>Upload files on the left and ask questions here. VeriCite will locate relevant contexts, attribute sources, and synthesize an accurate answer.</p>
            <div className="example-queries">
              <span className="example-tag" onClick={() => handleExampleClick("What is the architecture of the VeriCite system?")}>Architecture</span>
              <span className="example-tag" onClick={() => handleExampleClick("What are the key technical specifications?")}>Key Specs</span>
              <span className="example-tag" onClick={() => handleExampleClick("Summary of historical background?")}>History</span>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message-row ${msg.role}`}>
              <div className={`chat-message ${msg.isError ? 'error-msg' : ''}`}>
                {msg.role === 'user' ? (
                  msg.text
                ) : (
                  <>
                    <div dangerouslySetInnerHTML={parseResponseWithCitations(msg.text)} />
                    
                    {msg.chunks && msg.chunks.length > 0 && (
                      <div className="attributions-box">
                        <div 
                          className={`attributions-title ${openDrawers[index] ? 'open' : ''}`}
                          onClick={() => toggleDrawer(index)}
                        >
                          <i className="fa-solid fa-chevron-right"></i> {openDrawers[index] ? 'Hide' : 'Show'} Attributed Document Fragments ({msg.chunks.length})
                        </div>
                        {openDrawers[index] && (
                          <div className="attributions-list">
                            {msg.chunks.map((chunk, cIdx) => {
                              const cleanSource = chunk.metadata.source.replace(/[^a-zA-Z0-9]/g, '');
                              const cardId = `chunk-${cleanSource}-${chunk.metadata.page}-${cIdx}`;
                              return (
                                <div key={cIdx} className="attribution-card" id={cardId}>
                                  <div className="attr-header">
                                    <span className="attr-source">
                                      <i className="fa-solid fa-file-invoice"></i> {chunk.metadata.source} (Page {chunk.metadata.page})
                                    </span>
                                    <span className="attr-score">Similarity: {chunk.score.toFixed(4)}</span>
                                  </div>
                                  <div className="attr-body">{chunk.content}</div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))
        )}

        {isTyping && (
          <div className="message-row assistant">
            <div className="chat-message">
              <div className="typing-bubble">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Latency timing indicators banner */}
      {perfStats && (
        <div className="retrieval-stats-bar" id="stats-bar">
          <span className="stat-badge"><i className="fa-regular fa-clock"></i> Retrieval: {perfStats.retrieval_time_sec.toFixed(3)}s</span>
          <span className="stat-badge"><i className="fa-solid fa-wand-magic-sparkles"></i> LLM: {perfStats.llm_time_sec.toFixed(3)}s</span>
          <span className="stat-badge"><i className="fa-solid fa-hourglass-half"></i> Total: {perfStats.total_time_sec.toFixed(3)}s</span>
        </div>
      )}

      {/* Input controls and sliders parameter panel */}
      <div className="query-area">
        <div className="query-params">
          <div className="param-group">
            <label htmlFor="top-k-slider">Top Chunks (k): <span id="top-k-val">{topK}</span></label>
            <input 
              type="range" 
              id="top-k-slider" 
              min="1" 
              max="10" 
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value))}
            />
          </div>
          <div className="param-group">
            <label htmlFor="threshold-slider">Min Score: <span id="threshold-val">{minSimilarity.toFixed(2)}</span></label>
            <input 
              type="range" 
              id="threshold-slider" 
              min="0" 
              max="1" 
              step="0.05" 
              value={minSimilarity}
              onChange={(e) => setMinSimilarity(parseFloat(e.target.value))}
            />
          </div>
        </div>

        <form className="query-input-wrapper" onSubmit={handleSubmit}>
          <input 
            type="text" 
            placeholder="Ask a question about your indexed documents..."
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            autoComplete="off"
            required
            disabled={isTyping}
          />
          <button type="submit" className="submit-btn" disabled={isTyping}>
            <span>Ask</span>
            <i className="fa-solid fa-paper-plane send-icon"></i>
            <div className="pulse-ring"></div>
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatConsole;
