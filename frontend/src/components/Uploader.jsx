import React, { useState, useRef } from 'react';

function Uploader({ API_BASE_URL, onUploadSuccess, addToast }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadPercent, setUploadPercent] = useState("0%");
  const [filename, setFilename] = useState("");
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      uploadFiles(files);
    }
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      uploadFiles(files);
    }
  };

  const uploadFiles = async (files) => {
    setIsUploading(true);
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      setFilename(file.name);
      setUploadPercent("0%");
      
      const formData = new FormData();
      formData.append("file", file);
      
      try {
        // Fast progress visualizer
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.random() * 15;
          if (progress > 85) {
            clearInterval(interval);
            setUploadPercent("Processing index...");
          } else {
            setUploadPercent(`${Math.round(progress)}%`);
          }
        }, 100);

        const response = await fetch(`${API_BASE_URL}/upload`, {
          method: "POST",
          body: formData
        });

        clearInterval(interval);
        
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || "Upload failed");
        }
        
        const data = await response.json();
        setUploadPercent("100%");
        addToast(`Indexed: ${file.name} (${data.chunks_count} chunks)`, "success");
        onUploadSuccess();
      } catch (err) {
        addToast(`Ingestion Error for ${file.name}: ${err.message}`, "error");
      }
    }
    
    setTimeout(() => {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }, 1500);
  };

  return (
    <div>
      <div 
        className={`upload-dropzone ${isDragOver ? 'dragover' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: "none" }} 
          multiple 
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFileChange}
        />
        <div className="dropzone-content">
          <i className="fa-solid fa-file-pdf pdf-icon"></i>
          <i className="fa-solid fa-file-word word-icon"></i>
          <i className="fa-solid fa-file-lines txt-icon"></i>
          <div className="dropzone-text">
            <p className="main-text">
              Drag & drop files here, or <span className="highlight-link">browse</span>
            </p>
            <p className="sub-text">Supports PDF, DOCX, TXT, MD (Max 20MB)</p>
          </div>
        </div>
      </div>

      {isUploading && (
        <div className="progress-container">
          <div className="progress-header">
            <span id="progress-filename">{filename}</span>
            <span id="progress-percent">{uploadPercent}</span>
          </div>
          <div className="progress-bar-bg">
            <div 
              className="progress-bar-fill" 
              style={{ width: uploadPercent.includes('%') ? uploadPercent : '90%' }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Uploader;
