<script>
  import { onMount } from 'svelte';

  // API base URL - adjust this to match your backend
  const API_BASE = 'http://localhost:8000';

  // State variables
  let files = [];
  let documents = [];
  let uploading = false;
  let loading = false;
  let message = '';
  let messageType = '';

  // Chat state
  let chatMessages = [];
  let currentQuestion = '';
  let isQuerying = false;
  let availableModels = [];
  let selectedModel = 'qwen3:0.6b';

  // File input reference
  let fileInput;
  let chatContainer;

  // Load documents and models on component mount
  onMount(() => {
    loadDocuments();
    loadAvailableModels();
  });

  // Handle file selection
  function handleFileSelect(event) {
    files = Array.from(event.target.files).filter(file => 
      file.type === 'application/pdf'
    );
    
    if (files.length === 0) {
      showMessage('Please select at least one PDF file', 'error');
    }
  }

  // Upload single PDF
  async function uploadSinglePDF(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload-pdf/`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return await response.json();
  }

  // Upload multiple PDFs
  async function uploadMultiplePDFs() {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await fetch(`${API_BASE}/upload-multiple-pdfs/`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return await response.json();
  }

  // Handle upload
  async function handleUpload() {
    if (files.length === 0) {
      showMessage('Please select files to upload', 'error');
      return;
    }

    uploading = true;
    message = '';

    try {
      let result;
      
      if (files.length === 1) {
        result = await uploadSinglePDF(files[0]);
        showMessage(`PDF processed successfully! ${result.chunks_processed} chunks created.`, 'success');
      } else {
        result = await uploadMultiplePDFs();
        const successCount = result.results.filter(r => r.status === 'success').length;
        const errorCount = result.results.filter(r => r.status === 'error').length;
        
        if (errorCount === 0) {
          showMessage(`All ${successCount} PDFs processed successfully!`, 'success');
        } else {
          showMessage(`${successCount} PDFs processed, ${errorCount} failed.`, 'warning');
        }
      }

      // Clear files and reload documents
      files = [];
      fileInput.value = '';
      await loadDocuments();

    } catch (error) {
      showMessage(`Upload failed: ${error.message}`, 'error');
    } finally {
      uploading = false;
    }
  }

  // Load documents list
  async function loadDocuments() {
    loading = true;
    try {
      const response = await fetch(`${API_BASE}/documents/`);
      if (!response.ok) {
        throw new Error('Failed to load documents');
      }
      const data = await response.json();
      documents = data.documents;
    } catch (error) {
      showMessage(`Failed to load documents: ${error.message}`, 'error');
    } finally {
      loading = false;
    }
  }

  // Load available models
  async function loadAvailableModels() {
    try {
      const response = await fetch(`${API_BASE}/ollama/models`);
      if (response.ok) {
        const data = await response.json();
        availableModels = data.models;
      }
    } catch (error) {
      console.log('Could not load available models:', error);
    }
  }

  // Delete document
  async function deleteDocument(documentId) {
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/documents/${documentId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete document');
      }

      showMessage('Document deleted successfully', 'success');
      await loadDocuments();
    } catch (error) {
      showMessage(`Failed to delete document: ${error.message}`, 'error');
    }
  }

  // Handle chat submission
  async function handleChatSubmit() {
    if (!currentQuestion.trim() || isQuerying) return;
    
    if (documents.length === 0) {
      showMessage('Please upload documents first before asking questions', 'error');
      return;
    }

    const question = currentQuestion.trim();
    currentQuestion = '';
    
    // Add user message
    chatMessages = [...chatMessages, {
      type: 'user',
      content: question,
      timestamp: new Date()
    }];

    // Add loading message
    const loadingMessageId = Date.now();
    chatMessages = [...chatMessages, {
      id: loadingMessageId,
      type: 'assistant',
      content: '',
      loading: true,
      timestamp: new Date()
    }];

    isQuerying = true;
    scrollToBottom();

    try {
      const response = await fetch(`${API_BASE}/query/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: question,
          top_k: 5,
          model: selectedModel
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Query failed');
      }

      const data = await response.json();

      // Remove loading message and add actual response
      chatMessages = chatMessages.filter(msg => msg.id !== loadingMessageId);
      chatMessages = [...chatMessages, {
        type: 'assistant',
        content: data.answer,
        sources: data.sources,
        model: data.model_used,
        timestamp: new Date()
      }];

    } catch (error) {
      // Remove loading message and add error
      chatMessages = chatMessages.filter(msg => msg.id !== loadingMessageId);
      chatMessages = [...chatMessages, {
        type: 'assistant',
        content: `Error: ${error.message}`,
        error: true,
        timestamp: new Date()
      }];
    } finally {
      isQuerying = false;
      scrollToBottom();
    }
  }

  // Clear chat
  function clearChat() {
    chatMessages = [];
  }

  // Scroll to bottom of chat
  function scrollToBottom() {
    setTimeout(() => {
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 100);
  }

  // Handle enter key in chat input
  function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleChatSubmit();
    }
  }

  // Show message helper
  function showMessage(text, type) {
    message = text;
    messageType = type;
    setTimeout(() => {
      message = '';
      messageType = '';
    }, 5000);
  }

  // Format file size
  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // Format date
  function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
  }

  // Format chat timestamp
  function formatChatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
</script>

<svelte:head>
  <title>RAG Pipeline - Document Manager & Chat</title>
</svelte:head>

<main class="container">
  <header>
    <h1>RAG Pipeline Document Manager</h1>
    <p>Upload and manage PDF documents, then chat with your documents</p>
  </header>

  <!-- Message Display -->
  {#if message}
    <div class="message {messageType}">
      {message}
    </div>
  {/if}

  <div class="main-content">
    <!-- Left Column: Upload & Documents -->
    <div class="left-column">
      <!-- Upload Section -->
      <section class="upload-section">
        <h2>Upload Documents</h2>
        
        <div class="upload-area">
          <input
            bind:this={fileInput}
            type="file"
            multiple
            accept=".pdf"
            on:change={handleFileSelect}
            disabled={uploading}
          />
          
          {#if files.length > 0}
            <div class="selected-files">
              <h3>Selected Files ({files.length}):</h3>
              <ul>
                {#each files as file}
                  <li>
                    <span class="filename">{file.name}</span>
                    <span class="filesize">({formatFileSize(file.size)})</span>
                  </li>
                {/each}
              </ul>
            </div>
          {/if}

          <button
            on:click={handleUpload}
            disabled={uploading || files.length === 0}
            class="upload-btn"
          >
            {#if uploading}
              <span class="spinner"></span>
              Processing...
            {:else}
              Upload {files.length > 1 ? `${files.length} PDFs` : 'PDF'}
            {/if}
          </button>
        </div>
      </section>

      <!-- Documents List -->
      <section class="documents-section">
        <div class="section-header">
          <h2>Documents ({documents.length})</h2>
          <button on:click={loadDocuments} disabled={loading} class="refresh-btn">
            {#if loading}
              <span class="spinner"></span>
            {:else}
              Refresh
            {/if}
          </button>
        </div>

        {#if loading}
          <div class="loading">Loading documents...</div>
        {:else if documents.length === 0}
          <div class="empty-state">
            <p>No documents uploaded yet. Upload your first PDF to get started!</p>
          </div>
        {:else}
          <div class="documents-list">
            {#each documents as doc}
              <div class="document-item">
                <div class="document-info">
                  <h4>{doc.filename}</h4>
                  <p>{doc.chunk_count} chunks</p>
                </div>
                <button
                  on:click={() => deleteDocument(doc.id)}
                  class="delete-btn"
                  title="Delete document"
                >
                  ×
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </section>
    </div>

    <!-- Right Column: Chat -->
    <div class="right-column">
      <section class="chat-section">
        <div class="chat-header">
          <h2>Chat with Documents</h2>
          <div class="chat-controls">
            {#if availableModels.length > 0}
              <select bind:value={selectedModel} class="model-select">
                {#each availableModels as model}
                  <option value={model}>{model}</option>
                {/each}
              </select>
            {/if}
            <button on:click={clearChat} class="clear-btn" disabled={chatMessages.length === 0}>
              Clear Chat
            </button>
          </div>
        </div>

        <div class="chat-container" bind:this={chatContainer}>
          {#if chatMessages.length === 0}
            <div class="chat-empty">
              <p>Ask questions about your uploaded documents!</p>
              {#if documents.length === 0}
                <p class="hint">Upload some documents first to get started.</p>
              {/if}
            </div>
          {:else}
            {#each chatMessages as msg}
              <div class="message-wrapper {msg.type}">
                <div class="message-content">
                  {#if msg.loading}
                    <div class="typing-indicator">
                      <span class="spinner"></span>
                      Thinking...
                    </div>
                  {:else}
                    <div class="message-text" class:error={msg.error}>
                      {msg.content}
                    </div>
                    
                    {#if msg.sources && msg.sources.length > 0}
                      <div class="sources">
                        <h4>Sources:</h4>
                        {#each msg.sources as source}
                          <div class="source-item">
                            <div class="source-header">
                              <span class="source-filename">{source.filename}</span>
                              <span class="source-similarity">({(source.similarity * 100).toFixed(1)}% match)</span>
                            </div>
                            <div class="source-preview">{source.preview}</div>
                          </div>
                        {/each}
                      </div>
                    {/if}
                    
                    {#if msg.model}
                      <div class="model-info">Model: {msg.model}</div>
                    {/if}
                  {/if}
                </div>
                <div class="message-time">{formatChatTime(msg.timestamp)}</div>
              </div>
            {/each}
          {/if}
        </div>

        <div class="chat-input-area">
          <div class="input-wrapper">
            <textarea
              bind:value={currentQuestion}
              placeholder={documents.length > 0 ? "Ask a question about your documents..." : "Upload documents first to start chatting"}
              disabled={isQuerying || documents.length === 0}
              on:keypress={handleKeyPress}
              rows="2"
            ></textarea>
            <button
              on:click={handleChatSubmit}
              disabled={!currentQuestion.trim() || isQuerying || documents.length === 0}
              class="send-btn"
            >
              {#if isQuerying}
                <span class="spinner"></span>
              {:else}
                Send
              {/if}
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #f5f5f5;
  }

  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }

  header {
    text-align: center;
    margin-bottom: 2rem;
  }

  header h1 {
    color: #333;
    margin-bottom: 0.5rem;
  }

  header p {
    color: #666;
    font-size: 1.1rem;
  }

  .message {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    font-weight: 500;
  }

  .message.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
  }

  .message.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
  }

  .message.warning {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
  }

  .main-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    align-items: start;
  }

  .left-column, .right-column {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .upload-section, .documents-section, .chat-section {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }

  .upload-area {
    border: 2px dashed #ddd;
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    transition: border-color 0.3s;
  }

  .upload-area:hover {
    border-color: #007bff;
  }

  input[type="file"] {
    margin-bottom: 1rem;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    width: 100%;
    max-width: 300px;
  }

  .selected-files {
    margin: 1rem 0;
    text-align: left;
    max-width: 300px;
    margin-left: auto;
    margin-right: auto;
  }

  .selected-files ul {
    list-style: none;
    padding: 0;
  }

  .selected-files li {
    padding: 0.5rem;
    background: #f8f9fa;
    margin: 0.25rem 0;
    border-radius: 4px;
    display: flex;
    justify-content: space-between;
  }

  .filename {
    font-weight: 500;
  }

  .filesize {
    color: #666;
    font-size: 0.9rem;
  }

  .upload-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0 auto;
    transition: background-color 0.3s;
  }

  .upload-btn:hover:not(:disabled) {
    background: #0056b3;
  }

  .upload-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .refresh-btn {
    background: #28a745;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .refresh-btn:hover:not(:disabled) {
    background: #218838;
  }

  .loading, .empty-state {
    text-align: center;
    padding: 1.5rem;
    color: #666;
  }

  .documents-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .document-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: #f8f9fa;
    border-radius: 6px;
    border: 1px solid #e9ecef;
  }

  .document-info h4 {
    margin: 0 0 0.25rem 0;
    font-size: 0.9rem;
    color: #333;
  }

  .document-info p {
    margin: 0;
    font-size: 0.8rem;
    color: #666;
  }

  .delete-btn {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
  }

  .delete-btn:hover {
    background: #c82333;
  }

  /* Chat Styles */
  .chat-section {
    height: 600px;
    display: flex;
    flex-direction: column;
  }

  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #eee;
  }

  .chat-controls {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .model-select {
    padding: 0.25rem 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .clear-btn {
    background: #6c757d;
    color: white;
    border: none;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
  }

  .clear-btn:hover:not(:disabled) {
    background: #5a6268;
  }

  .clear-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .chat-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .chat-empty {
    text-align: center;
    color: #666;
    padding: 2rem;
  }

  .chat-empty .hint {
    font-size: 0.9rem;
    color: #999;
    margin-top: 0.5rem;
  }

  .message-wrapper {
    display: flex;
    flex-direction: column;
    max-width: 85%;
  }

  .message-wrapper.user {
    align-self: flex-end;
  }

  .message-wrapper.assistant {
    align-self: flex-start;
  }

  .message-content {
    padding: 0.75rem 1rem;
    border-radius: 12px;
    position: relative;
  }

  .message-wrapper.user .message-content {
    background: #007bff;
    color: white;
  }

  .message-wrapper.assistant .message-content {
    background: #f1f3f4;
    color: #333;
  }

  .message-text.error {
    color: #dc3545;
  }

  .message-time {
    font-size: 0.7rem;
    color: #999;
    margin-top: 0.25rem;
    padding: 0 0.5rem;
  }

  .message-wrapper.user .message-time {
    text-align: right;
  }

  .typing-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #666;
  }

  .sources {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #ddd;
  }

  .sources h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.8rem;
    color: #666;
  }

  .source-item {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .source-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.25rem;
  }

  .source-filename {
    font-weight: 500;
    font-size: 0.8rem;
    color: #007bff;
  }

  .source-similarity {
    font-size: 0.7rem;
    color: #666;
  }

  .source-preview {
    font-size: 0.75rem;
    color: #555;
    line-height: 1.3;
  }

  .model-info {
    font-size: 0.7rem;
    color: #999;
    margin-top: 0.5rem;
    text-align: right;
  }

  .chat-input-area {
    padding-top: 1rem;
    border-top: 1px solid #eee;
  }

  .input-wrapper {
    display: flex;
    gap: 0.5rem;
    align-items: flex-end;
  }

  .input-wrapper textarea {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    resize: none;
    font-family: inherit;
    font-size: 0.9rem;
  }

  .input-wrapper textarea:focus {
    outline: none;
    border-color: #007bff;
  }

  .send-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }

  .send-btn:hover:not(:disabled) {
    background: #0056b3;
  }

  .send-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @media (max-width: 1024px) {
    .main-content {
      grid-template-columns: 1fr;
    }
    
    .chat-section {
      height: 500px;
    }
  }

  @media (max-width: 768px) {
    .container {
      padding: 1rem;
    }

    .chat-header {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }

    .chat-controls {
      justify-content: space-between;
    }
  }
</style>