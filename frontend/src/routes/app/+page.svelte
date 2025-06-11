<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import Navbar from '$lib/components/Navbar.svelte';
  import { 
    Upload, 
    FileText, 
    Trash2, 
    RefreshCw, 
    Send, 
    Bot, 
    User, 
    Settings,
    MessageCircle,
    File,
    Clock,
    Loader2,
    Download,
    Eye,
    Search
  } from 'lucide-svelte';

  // API base URL - adjust this to match your backend
  const API_BASE = 'http://localhost:8000';

  // Authentication state
  let isAuthenticated = false;
  let user = null;

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
    checkAuthentication();
  });

  function checkAuthentication() {
    if (browser) {
      const token = localStorage.getItem('access_token');
      const userData = localStorage.getItem('user');

      if (token && userData) {
        try {
          user = JSON.parse(userData);
          isAuthenticated = true;
          loadDocuments();
          loadAvailableModels();
        } catch (error) {
          console.error('Error parsing user data:', error);
          // Clear corrupted data before redirecting
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          redirectToSignIn();
        }
      } else {
        redirectToSignIn();
      }
    }
  }

  function redirectToSignIn() {
    if (browser) {
      // Clear any existing auth data
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      isAuthenticated = false;
      user = null;
      // Use replace to prevent back button issues
      goto('/sign', { replaceState: true });
    }
  }

  // Handle file selection
  function handleFileSelect(event) {
    files = Array.from(event.target.files).filter((file) => {
      return file.type === 'application/pdf';
    });

    if (files.length === 0) {
      showMessage('Please select at least one PDF file', 'error');
    }
  }

  // Upload single PDF
  async function uploadSinglePDF(file) {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/upload-pdf/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      if (response.status === 401) {
        redirectToSignIn();
        return;
      }
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

    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/upload-multiple-pdfs/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      if (response.status === 401) {
        redirectToSignIn();
        return;
      }
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
      const token = localStorage.getItem('access_token');
      if (!token) {
        redirectToSignIn();
        return;
      }
      
      const response = await fetch(`${API_BASE}/documents/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          redirectToSignIn();
          return;
        }
        throw new Error('Failed to load documents');
      }
      
      const data = await response.json();
      documents = data.documents;
    } catch (error) {
      console.error('Error loading documents:', error);
      showMessage(`Failed to load documents: ${error.message}`, 'error');
    } finally {
      loading = false;
    }
  }

  // Load available models
  async function loadAvailableModels() {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/ollama/models`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        availableModels = data.models;
      }
    } catch (error) {
      console.error('Error loading models:', error);
      showMessage(`Failed to load models: ${error.message}`, 'error');
    }
  }

  // Delete document
  async function deleteDocument(documentId) {
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          redirectToSignIn();
          return;
        }
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
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/query/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          question: question,
          top_k: 5,
          model: selectedModel
        })
      });

      if (!response.ok) {
        if (response.status === 401) {
          redirectToSignIn();
          return;
        }
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
  <meta name="description" content="Upload and chat with your PDF documents using AI">
</svelte:head>

<!-- Add Navbar -->
<Navbar />

<!-- Show content only if authenticated -->
{#if isAuthenticated}
  <main class="app-container">
    <!-- Left Vertical Sidebar -->
    <aside class="sidebar">
      <!-- Sidebar Header -->
      <div class="sidebar-header">
        <div class="logo-section">
          <div class="logo-icon">
            <Bot size={20} color="white" />
          </div>
          <div class="logo-text">
            <h1>RAG AI</h1>
            <p>{documents.length} docs</p>
          </div>
        </div>
      </div>

      <!-- Upload Section -->
      <section class="sidebar-panel upload-section">
        <div class="section-header">
          <Upload size={16} />
          <h3>Upload</h3>
        </div>
        
        <div class="upload-area">
          <div class="upload-dropzone" class:uploading>
            <div class="upload-icon">
              <FileText size={24} />
            </div>
            <p class="upload-text">Drop PDFs here or click to browse</p>
            <input
              bind:this={fileInput}
              type="file"
              multiple
              accept=".pdf"
              on:change={handleFileSelect}
              disabled={uploading}
              class="file-input"
            />
          </div>
          
          {#if files.length > 0}
            <div class="selected-files">
              <p class="files-count">{files.length} file{files.length > 1 ? 's' : ''} selected</p>
              <div class="files-preview">
                {#each files.slice(0, 2) as file}
                  <div class="file-preview">
                    <File size={12} />
                    <span class="file-name">{file.name.length > 15 ? file.name.substring(0, 15) + '...' : file.name}</span>
                  </div>
                {/each}
                {#if files.length > 2}
                  <div class="file-preview">
                    <span class="more-files">+{files.length - 2} more</span>
                  </div>
                {/if}
              </div>
            </div>
          {/if}

          <button
            on:click={handleUpload}
            disabled={uploading || files.length === 0}
            class="upload-btn"
          >
            {#if uploading}
              <Loader2 size={14} class="spinner" />
            {:else}
              <Upload size={14} />
            {/if}
            {uploading ? 'Processing...' : 'Upload'}
          </button>
        </div>
      </section>

      <!-- Documents List -->
      <section class="sidebar-panel documents-section">
        <div class="section-header">
          <FileText size={16} />
          <h3>Documents</h3>
          <button on:click={loadDocuments} disabled={loading} class="refresh-btn">
            {#if loading}
              <Loader2 size={14} class="spinner" />
            {:else}
              <RefreshCw size={14} />
            {/if}
          </button>
        </div>

        <div class="documents-content">
          {#if loading}
            <div class="loading-state">
              <Loader2 size={20} class="spinner" />
              <p>Loading...</p>
            </div>
          {:else if documents.length === 0}
            <div class="empty-state">
              <FileText size={24} />
              <p>No documents</p>
              <span class="empty-hint">Upload your first PDF</span>
            </div>
          {:else}
            <div class="documents-list">
              {#each documents as doc}
                <div class="document-item">
                  <div class="document-icon">
                    <FileText size={16} />
                  </div>
                  <div class="document-info">
                    <h4 class="document-name">{doc.filename.length > 20 ? doc.filename.substring(0, 20) + '...' : doc.filename}</h4>
                    <p class="document-chunks">{doc.chunk_count} chunks</p>
                  </div>
                  <button
                    on:click={() => deleteDocument(doc.id)}
                    class="delete-btn"
                    title="Delete document"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </section>

      <!-- User Info -->
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">
            <User size={16} />
          </div>
          <div class="user-details">
            <p class="user-name">{user?.full_name ? (user.full_name.length > 15 ? user.full_name.substring(0, 15) + '...' : user.full_name) : 'User'}</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="main-content">
      <!-- Message Display -->
      {#if message}
        <div class="notification notification-{messageType}">
          <div class="notification-content">
            {message}
          </div>
        </div>
      {/if}

      <!-- Chat Section -->
      <section class="chat-section">
        <div class="chat-header">
          <div class="chat-title">
            <MessageCircle size={20} />
            <h2>Chat with Documents</h2>
          </div>
          <div class="chat-controls">
            {#if availableModels.length > 0}
              <div class="model-selector">
                <Settings size={14} />
                <select bind:value={selectedModel} class="model-select">
                  {#each availableModels as model}
                    <option value={model}>{model}</option>
                  {/each}
                </select>
              </div>
            {/if}
            <button 
              on:click={clearChat} 
              class="clear-btn" 
              disabled={chatMessages.length === 0}
              title="Clear chat history"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>

        <div class="chat-container" bind:this={chatContainer}>
          {#if chatMessages.length === 0}
            <div class="chat-empty">
              <Bot size={48} />
              <h3>Ready to help!</h3>
              <p>Ask questions about your uploaded documents.</p>
              {#if documents.length === 0}
                <p class="hint">Upload some documents first to get started.</p>
              {/if}
            </div>
          {:else}
            <div class="messages-list">
              {#each chatMessages as msg}
                <div class="message-wrapper message-{msg.type}">
                  <div class="message-avatar">
                    {#if msg.type === 'user'}
                      <User size={14} />
                    {:else}
                      <Bot size={14} />
                    {/if}
                  </div>
                  <div class="message-content">
                    {#if msg.loading}
                      <div class="typing-indicator">
                        <Loader2 size={14} class="spinner" />
                        <span>Thinking...</span>
                      </div>
                    {:else}
                      <div class="message-text" class:error={msg.error}>
                        {msg.content}
                      </div>
                      
                      {#if msg.sources && msg.sources.length > 0}
                        <div class="sources-section">
                          <h4 class="sources-title">
                            <Search size={12} />
                            Sources
                          </h4>
                          <div class="sources-list">
                            {#each msg.sources as source}
                              <div class="source-card">
                                <div class="source-header">
                                  <div class="source-name">
                                    <File size={12} />
                                    {source.filename}
                                  </div>
                                  <div class="source-similarity">
                                    {(source.similarity * 100).toFixed(1)}%
                                  </div>
                                </div>
                                <div class="source-preview">{source.preview}</div>
                              </div>
                            {/each}
                          </div>
                        </div>
                      {/if}
                      
                      {#if msg.model}
                        <div class="model-info">
                          <Settings size={10} />
                          {msg.model}
                        </div>
                      {/if}
                    {/if}
                    <div class="message-time">
                      <Clock size={10} />
                      {formatChatTime(msg.timestamp)}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <div class="chat-input-section">
          <div class="input-container">
            <textarea
              bind:value={currentQuestion}
              placeholder={documents.length > 0 ? "Ask a question about your documents..." : "Upload documents first to start chatting"}
              disabled={isQuerying || documents.length === 0}
              on:keypress={handleKeyPress}
              rows="1"
              class="chat-input"
            ></textarea>
            <button
              on:click={handleChatSubmit}
              disabled={!currentQuestion.trim() || isQuerying || documents.length === 0}
              class="send-btn"
              title="Send message"
            >
              {#if isQuerying}
                <Loader2 size={16} class="spinner" />
              {:else}
                <Send size={16} />
              {/if}
            </button>
          </div>
        </div>
      </section>
    </div>
  </main>
{:else}
  <!-- Loading state while checking authentication -->
  <div class="auth-loading">
    <Loader2 size={32} class="spinner" />
    <p>Checking authentication...</p>
  </div>
{/if}

<style>
  :root {
    --primary-600: #4f46e5;
    --primary-700: #4338ca;
    --primary-50: #eef2ff;
    --primary-100: #e0e7ff;
    --gray-50: #f9fafb;
    --gray-100: #f3f4f6;
    --gray-200: #e5e7eb;
    --gray-300: #d1d5db;
    --gray-400: #9ca3af;
    --gray-500: #6b7280;
    --gray-600: #4b5563;
    --gray-700: #374151;
    --gray-800: #1f2937;
    --gray-900: #111827;
    --red-500: #ef4444;
    --red-50: #fef2f2;
    --green-500: #10b981;
    --green-50: #ecfdf5;
    --yellow-500: #f59e0b;
    --yellow-50: #fffbeb;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    --border-radius: 6px;
    --border-radius-lg: 8px;
    --border-radius-xl: 12px;
    --sidebar-width: 320px;
    --navbar-height: 64px; /* Add navbar height variable */
  }

  :global(body) {
    margin: 0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--gray-50);
    color: var(--gray-900);
    line-height: 1.5;
    overflow: hidden;
  }

  .app-container {
    display: flex;
    height: calc(100vh - var(--navbar-height)); /* Subtract navbar height */
    overflow: hidden;
  }

  .auth-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: calc(60vh - var(--navbar-height)); /* Adjust for navbar */
    gap: 1rem;
    color: var(--gray-500);
  }

  /* Sidebar Styles */
  .sidebar {
    width: var(--sidebar-width);
    background: white;
    border-right: 1px solid var(--gray-200);
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex-shrink: 0;
    height: calc(100vh - var(--navbar-height)); /* Adjust for navbar */
  }

  .sidebar-header {
    padding: 1.5rem 1rem;
    border-bottom: 1px solid var(--gray-100);
    background: var(--gray-50);
  }

  .logo-section {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .logo-icon {
    background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
    width: 2rem;
    height: 2rem;
    border-radius: var(--border-radius);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-md);
    flex-shrink: 0;
  }

  .logo-text h1 {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: var(--gray-900);
    letter-spacing: -0.025em;
  }

  .logo-text p {
    margin: 0;
    color: var(--gray-500);
    font-size: 0.75rem;
  }

  .sidebar-panel {
    padding: 1rem;
    border-bottom: 1px solid var(--gray-100);
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    color: var(--gray-700);
  }

  .section-header h3 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--gray-900);
    flex: 1;
  }

  .refresh-btn {
    background: var(--gray-100);
    color: var(--gray-600);
    border: none;
    padding: 0.25rem;
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .refresh-btn:hover:not(:disabled) {
    background: var(--gray-200);
    color: var(--gray-700);
  }

  .refresh-btn:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  /* Upload Section */
  .upload-section {
    flex-shrink: 0;
  }

  .upload-area {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .upload-dropzone {
    border: 2px dashed var(--gray-300);
    border-radius: var(--border-radius-lg);
    padding: 1rem;
    text-align: center;
    transition: all 0.2s ease;
    position: relative;
    background: var(--gray-50);
  }

  .upload-dropzone:hover {
    border-color: var(--primary-400);
    background: var(--primary-50);
  }

  .upload-dropzone.uploading {
    border-color: var(--primary-500);
    background: var(--primary-50);
  }

  .upload-icon {
    color: var(--gray-400);
    margin-bottom: 0.5rem;
  }

  .upload-text {
    font-size: 0.75rem;
    color: var(--gray-500);
    margin: 0;
    font-weight: 500;
  }

  .file-input {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
  }

  .file-input:disabled {
    cursor: not-allowed;
  }

  .selected-files {
    background: var(--gray-50);
    border-radius: var(--border-radius);
    padding: 0.75rem;
  }

  .files-count {
    margin: 0 0 0.5rem 0;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--gray-700);
  }

  .files-preview {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .file-preview {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.6875rem;
    color: var(--gray-600);
  }

  .file-name {
    flex: 1;
    min-width: 0;
  }

  .more-files {
    color: var(--gray-500);
    font-style: italic;
  }

  .upload-btn {
    width: 100%;
    background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
    color: white;
    border: none;
    padding: 0.75rem;
    border-radius: var(--border-radius);
    font-size: 0.8125rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .upload-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: var(--shadow-lg);
  }

  .upload-btn:disabled {
    background: var(--gray-400);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  /* Documents Section */
  .documents-section {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden; /* Add this to contain the scrollable area */
  }

  .documents-content {
    flex: 1;
    overflow-y: auto;
    min-height: 0;
    /* Add scrollbar styling for better UX */
    scrollbar-width: thin;
    scrollbar-color: var(--gray-300) transparent;
  }

  /* Add webkit scrollbar styling */
  .documents-content::-webkit-scrollbar {
    width: 4px;
  }

  .documents-content::-webkit-scrollbar-track {
    background: transparent;
  }

  .documents-content::-webkit-scrollbar-thumb {
    background: var(--gray-300);
    border-radius: 2px;
  }

  .documents-content::-webkit-scrollbar-thumb:hover {
    background: var(--gray-400);
  }

  .loading-state, .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem 1rem;
    text-align: center;
    color: var(--gray-500);
    gap: 0.5rem;
  }

  .empty-state p {
    margin: 0;
    font-weight: 600;
    color: var(--gray-700);
    font-size: 0.875rem;
  }

  .empty-hint {
    font-size: 0.75rem;
    color: var(--gray-400);
  }

  .documents-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .document-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: var(--gray-50);
    border: 1px solid var(--gray-200);
    border-radius: var(--border-radius);
    transition: all 0.2s ease;
  }

  .document-item:hover {
    background: white;
    box-shadow: var(--shadow-sm);
  }

  .document-icon {
    color: var(--primary-600);
    flex-shrink: 0;
  }

  .document-info {
    flex: 1;
    min-width: 0;
  }

  .document-name {
    margin: 0 0 0.125rem 0;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--gray-900);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .document-chunks {
    margin: 0;
    font-size: 0.6875rem;
    color: var(--gray-500);
  }

  .delete-btn {
    background: var(--red-50);
    color: var(--red-500);
    border: none;
    padding: 0.375rem;
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .delete-btn:hover {
    background: var(--red-500);
    color: white;
  }

  /* Sidebar Footer */
  .sidebar-footer {
    padding: 1rem;
    border-top: 1px solid var(--gray-100);
    background: var(--gray-50);
    margin-top: auto;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .user-avatar {
    background: var(--gray-200);
    color: var(--gray-600);
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .user-details {
    flex: 1;
    min-width: 0;
  }

  .user-name {
    margin: 0;
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--gray-900);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* Main Content Area */
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow: hidden;
  }

  .notification {
    margin: 1rem;
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow);
    overflow: hidden;
  }

  .notification-content {
    padding: 0.875rem 1rem;
    font-weight: 500;
    font-size: 0.875rem;
  }

  .notification-success {
    background: var(--green-50);
    color: var(--green-500);
    border-left: 4px solid var(--green-500);
  }

  .notification-error {
    background: var(--red-50);
    color: var(--red-500);
    border-left: 4px solid var(--red-500);
  }

  .notification-warning {
    background: var(--yellow-50);
    color: var(--yellow-500);
    border-left: 4px solid var(--yellow-500);
  }

  /* Chat Section */
  .chat-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: white;
    margin: 1rem;
    border-radius: var(--border-radius-xl);
    border: 1px solid var(--gray-200);
    box-shadow: var(--shadow);
    overflow: hidden;
    min-height: 0;
  }

  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--gray-100);
    background: var(--gray-50);
  }

  .chat-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: var(--gray-700);
  }

  .chat-title h2 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--gray-900);
  }

  .chat-controls {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .model-selector {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem 0.75rem;
    background: var(--gray-100);
    border-radius: var(--border-radius);
    color: var(--gray-600);
  }

  .model-select {
    background: none;
    border: none;
    font-size: 0.75rem;
    color: var(--gray-700);
    font-weight: 500;
    cursor: pointer;
  }

  .clear-btn {
    background: var(--gray-100);
    color: var(--gray-600);
    border: none;
    padding: 0.375rem;
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .clear-btn:hover:not(:disabled) {
    background: var(--red-50);
    color: var(--red-500);
  }

  .clear-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .chat-container {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    min-height: 0;
  }

  .chat-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    color: var(--gray-500);
    gap: 1rem;
  }

  .chat-empty h3 {
    margin: 0;
    color: var(--gray-700);
    font-weight: 600;
  }

  .chat-empty p {
    margin: 0;
    font-size: 0.875rem;
  }

  .hint {
    font-size: 0.8125rem !important;
    color: var(--gray-400) !important;
  }

  .messages-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    max-width: 100%;
  }

  .message-wrapper {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    max-width: 100%;
  }

  .message-user {
    flex-direction: row-reverse;
    justify-content: flex-start;
  }

  .message-assistant {
    justify-content: flex-start;
  }

  .message-avatar {
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-weight: 600;
    font-size: 0.75rem;
    margin-top: 0.125rem; /* Align with first line of text */
  }

  .message-user .message-avatar {
    background: var(--primary-600);
    color: white;
  }

  .message-assistant .message-avatar {
    background: var(--gray-200);
    color: var(--gray-600);
  }

  .message-content {
    max-width: min(70%, 600px); /* Limit width to 70% or 600px max */
    min-width: 0;
  }

  .message-user .message-content {
    align-self: flex-end;
  }

  .message-assistant .message-content {
    align-self: flex-start;
  }

  .message-text {
    background: var(--gray-100);
    padding: 0.875rem 1rem;
    border-radius: 1rem; /* More rounded for modern look */
    font-size: 0.875rem;
    line-height: 1.5;
    color: var(--gray-900);
    word-wrap: break-word;
    hyphens: auto;
    box-shadow: var(--shadow-sm);
    position: relative;
  }

  .message-user .message-text {
    background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
    color: white;
    border-bottom-right-radius: 0.375rem; /* Smaller radius on sender side */
  }

  .message-assistant .message-text {
    border-bottom-left-radius: 0.375rem; /* Smaller radius on receiver side */
  }

  .message-text.error {
    background: var(--red-50);
    color: var(--red-600);
    border-left: 3px solid var(--red-500);
  }

  .typing-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.875rem 1rem;
    background: var(--gray-100);
    border-radius: 1rem;
    border-bottom-left-radius: 0.375rem;
    color: var(--gray-600);
    font-style: italic;
    font-size: 0.875rem;
    box-shadow: var(--shadow-sm);
    max-width: fit-content;
  }

  .sources-section {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--gray-200);
  }

  .sources-title {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    margin: 0 0 0.75rem 0;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--gray-600);
  }

  .message-user .sources-title {
    color: rgba(255, 255, 255, 0.8);
  }

  .sources-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .source-card {
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: var(--border-radius);
    padding: 0.75rem;
    font-size: 0.75rem;
  }

  .message-user .source-card {
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.3);
  }

  .source-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .source-name {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-weight: 500;
    color: var(--primary-600);
  }

  .source-similarity {
    font-size: 0.6875rem;
    color: var(--gray-500);
    background: var(--gray-100);
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
  }

  .source-preview {
    color: var(--gray-600);
    line-height: 1.4;
  }

  .model-info {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin-top: 0.75rem;
    font-size: 0.6875rem;
    color: var(--gray-500);
  }

  .message-user .model-info {
    color: rgba(255, 255, 255, 0.7);
    justify-content: flex-end;
  }

  .message-time {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin-top: 0.5rem;
    font-size: 0.6875rem;
    color: var(--gray-400);
  }

  .message-user .message-time {
    color: rgba(255, 255, 255, 0.7);
    justify-content: flex-end;
  }

  /* Chat Input Section - ADD THIS MISSING SECTION */
  .chat-input-section {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--gray-100);
    background: var(--gray-50);
  }

  .input-container {
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
  }

  .chat-input {
    flex: 1;
    min-height: 2.5rem;
    max-height: 6rem;
    padding: 0.75rem 1rem;
    border: 1px solid var(--gray-300);
    border-radius: var(--border-radius-lg);
    font-size: 0.875rem;
    line-height: 1.5;
    color: var(--gray-900);
    background: white;
    resize: none;
    font-family: inherit;
    transition: all 0.2s ease;
    box-shadow: var(--shadow-sm);
  }

  .chat-input:focus {
    outline: none;
    border-color: var(--primary-600);
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
  }

  .chat-input:disabled {
    background: var(--gray-100);
    color: var(--gray-500);
    cursor: not-allowed;
  }

  .chat-input::placeholder {
    color: var(--gray-400);
  }

  .send-btn {
    background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
    color: white;
    border: none;
    padding: 0.75rem;
    border-radius: var(--border-radius-lg);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 2.5rem;
    height: 2.5rem;
    box-shadow: var(--shadow-sm);
  }

  .send-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: var(--shadow-lg);
  }

  .send-btn:disabled {
    background: var(--gray-400);
    cursor: not-allowed;
    transform: none;
    box-shadow: var(--shadow-sm);
  }

  /* Auto-resize textarea */
  .chat-input {
    field-sizing: content;
    overflow-y: auto;
  }

  /* Spinner animation for loading states */
  :global(.spinner) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  /* Mobile responsiveness for chat bubbles */
  @media (max-width: 768px) {
    .message-content {
      max-width: min(85%, 400px); /* Slightly wider on mobile but still constrained */
    }

    .message-text {
      padding: 0.75rem 0.875rem;
      font-size: 0.8125rem;
    }

    .documents-section {
      max-height: 150px; /* Reduce slightly to fit better */
    }

    .main-content {
      flex: 1;
      min-height: 0;
    }

    .chat-section {
      margin: 0.5rem; /* Reduce margin on mobile */
      flex: 1;
      min-height: 0;
    }
  }

  @media (max-width: 480px) {
    .message-content {
      max-width: 90%; /* Even wider on very small screens */
    }

    .message-wrapper {
      gap: 0.5rem;
    }

    .message-avatar {
      width: 1.5rem;
      height: 1.5rem;
    }

    .chat-header {
      padding: 0.75rem 1rem;
    }

    .chat-container {
      padding: 1rem;
    }

    .chat-input-section {
      padding: 0.75rem 1rem;
    }

    .input-container {
      flex-direction: column;
      gap: 0.5rem;
    }

    .send-btn {
      align-self: flex-end;
      min-width: auto;
      padding: 0.75rem 1.5rem;
    }
  }

  /* Accessibility improvements */
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }

    :global(.spinner) {
      animation: none;
    }
  }

  @media (prefers-contrast: high) {
    .sidebar, .chat-section {
      border-width: 2px;
    }

    .chat-input:focus {
      border-width: 3px;
    }
  }

  /* Focus visible for better keyboard navigation */
  .upload-btn:focus-visible,
  .refresh-btn:focus-visible,
  .delete-btn:focus-visible,
  .clear-btn:focus-visible,
  .send-btn:focus-visible,
  .chat-input:focus-visible,
  .model-select:focus-visible {
    outline: 2px solid var(--primary-600);
    outline-offset: 2px;
  }
</style>