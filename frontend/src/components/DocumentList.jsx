import React from 'react';

function DocumentList({ documents, onDelete, onRefresh }) {
  
  const getIconDetails = (docName) => {
    const ext = docName.split('.').pop().toLowerCase();
    if (ext === 'pdf') return { icon: 'fa-file-pdf', color: 'pdf-icon' };
    if (ext === 'docx') return { icon: 'fa-file-word', color: 'word-icon' };
    return { icon: 'fa-file-lines', color: 'txt-icon' };
  };

  return (
    <div className="inventory-section">
      <div className="inventory-header">
        <h3>Indexed Corpus (<span id="document-count">{documents.length}</span>)</h3>
        <button className="icon-btn" onClick={onRefresh} title="Refresh Document List">
          <i className="fa-solid fa-arrows-rotate"></i>
        </button>
      </div>

      <div className="document-list-scroll">
        <ul className="document-list">
          {documents.length === 0 ? (
            <li className="empty-list-state">
              <i className="fa-solid fa-folder-open empty-icon"></i>
              <p>No documents indexed yet.</p>
            </li>
          ) : (
            documents.map((doc, idx) => {
              const { icon, color } = getIconDetails(doc.name);
              const sizeKB = (doc.file_size / 1024).toFixed(1);
              return (
                <li key={idx} className="document-item">
                  <div className="doc-info">
                    <i className={`fa-solid ${icon} doc-type-icon ${color}`}></i>
                    <div className="doc-details">
                      <span className="doc-name" title={doc.name}>{doc.name}</span>
                      <span className="doc-meta">{sizeKB} KB | Pages: {doc.page_count}</span>
                    </div>
                  </div>
                  <button className="delete-doc-btn" onClick={() => onDelete(doc.name)} title="Delete Document Index">
                    <i className="fa-regular fa-trash-can"></i>
                  </button>
                </li>
              );
            })
          )}
        </ul>
      </div>
    </div>
  );
}

export default DocumentList;
