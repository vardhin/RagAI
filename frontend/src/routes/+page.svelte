<script>
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import Navbar from '$lib/components/Navbar.svelte';

  let isAuthenticated = false;

  onMount(() => {
    if (browser) {
      const token = localStorage.getItem('access_token');
      if (token) {
        isAuthenticated = true;
      }
    }
  });

  function navigateToApp() {
    if (isAuthenticated) {
      goto('/app');
    } else {
      goto('/sign');
    }
  }

  function navigateToSignIn() {
    goto('/sign');
  }
</script>

<svelte:head>
  <title>RAG Pipeline - Intelligent Document Chat</title>
  <meta name="description" content="Upload your PDF documents and chat with them using AI. Get instant answers from your document collection with our RAG-powered system." />
</svelte:head>

<!-- Add Navbar -->
<Navbar />

<main class="landing">
  <!-- Hero Section -->
  <section class="hero">
    <div class="container">
      <div class="hero-content">
        <div class="hero-text">
          <h1>Chat with Your Documents</h1>
          <p class="hero-subtitle">
            Upload PDFs and get instant, intelligent answers from your document collection using our advanced RAG (Retrieval-Augmented Generation) system.
          </p>
          <div class="hero-buttons">
            <button on:click={navigateToApp} class="cta-button primary">
              {isAuthenticated ? 'Go to App' : 'Get Started'}
            </button>
            {#if !isAuthenticated}
              <button on:click={navigateToSignIn} class="cta-button secondary">
                Sign In
              </button>
            {/if}
          </div>
        </div>
        <div class="hero-visual">
          <div class="demo-card">
            <div class="demo-header">
              <div class="demo-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span class="demo-title">Document Chat</span>
            </div>
            <div class="demo-content">
              <div class="chat-bubble user">
                What are the key findings in the research paper?
              </div>
              <div class="chat-bubble assistant">
                Based on the uploaded research paper, the key findings include: improved accuracy by 23%, reduced processing time...
              </div>
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Features Section -->
  <section class="features">
    <div class="container">
      <h2>Why Choose Our RAG System?</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">📄</div>
          <h3>PDF Upload & Processing</h3>
          <p>Upload multiple PDF documents simultaneously. Our system automatically processes and chunks your documents for optimal retrieval.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🤖</div>
          <h3>AI-Powered Chat</h3>
          <p>Ask natural language questions about your documents. Get accurate, contextual answers powered by advanced language models.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🔍</div>
          <h3>Smart Document Search</h3>
          <p>Intelligent semantic search finds relevant information across all your documents, with source citations for verification.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">⚡</div>
          <h3>Multiple AI Models</h3>
          <p>Choose from various AI models including Qwen and others. Switch between models to find the best fit for your needs.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🔒</div>
          <h3>Secure & Private</h3>
          <p>Your documents are securely stored and processed. User authentication ensures your data remains private and protected.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📊</div>
          <h3>Document Management</h3>
          <p>Organize, view, and manage your document collection. Track processing status and delete documents as needed.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- How It Works Section -->
  <section class="how-it-works">
    <div class="container">
      <h2>How It Works</h2>
      <div class="steps">
        <div class="step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h3>Upload Documents</h3>
            <p>Upload your PDF files to our secure platform. Support for single or multiple file uploads.</p>
          </div>
        </div>
        <div class="step-arrow">→</div>
        <div class="step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h3>AI Processing</h3>
            <p>Our system automatically processes and chunks your documents for optimal retrieval and understanding.</p>
          </div>
        </div>
        <div class="step-arrow">→</div>
        <div class="step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h3>Ask Questions</h3>
            <p>Chat naturally with your documents. Get instant, accurate answers with source citations.</p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- CTA Section -->
  <section class="cta-section">
    <div class="container">
      <div class="cta-content">
        <h2>Ready to Transform Your Document Experience?</h2>
        <p>Join thousands of users who are already chatting with their documents using our RAG system.</p>
        <button on:click={navigateToApp} class="cta-button primary large">
          {isAuthenticated ? 'Go to Dashboard' : 'Start Free Trial'}
        </button>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="footer">
    <div class="container">
      <div class="footer-content">
        <div class="footer-section">
          <h4>RAG Pipeline</h4>
          <p>Intelligent document chat powered by AI</p>
        </div>
        <div class="footer-section">
          <h4>Features</h4>
          <ul>
            <li>PDF Upload</li>
            <li>AI Chat</li>
            <li>Document Management</li>
            <li>Multiple Models</li>
          </ul>
        </div>
        <div class="footer-section">
          <h4>Getting Started</h4>
          <ul>
            <li><button on:click={navigateToSignIn} class="footer-link">Sign Up</button></li>
            <li><button on:click={navigateToSignIn} class="footer-link">Sign In</button></li>
            <li><button on:click={navigateToApp} class="footer-link">Dashboard</button></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; 2025 RAG Pipeline. All rights reserved.</p>
      </div>
    </div>
  </footer>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    /* Enable scrolling for landing page */
    overflow-y: auto;
    overflow-x: hidden;
  }

  .landing {
    /* Account for navbar height */
    padding-top: 0;
    min-height: 100vh;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
  }

  /* Hero Section */
  .hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 4rem 0;
    min-height: calc(100vh - 64px); /* Subtract navbar height */
    display: flex;
    align-items: center;
  }

  .hero-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    align-items: center;
  }

  .hero-text h1 {
    font-size: 3.5rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    line-height: 1.2;
  }

  .hero-subtitle {
    font-size: 1.25rem;
    margin-bottom: 2rem;
    opacity: 0.9;
    line-height: 1.6;
  }

  .hero-buttons {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .cta-button {
    padding: 1rem 2rem;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    border: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .cta-button.primary {
    background: white;
    color: #667eea;
  }

  .cta-button.primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
  }

  .cta-button.secondary {
    background: transparent;
    color: white;
    border: 2px solid white;
  }

  .cta-button.secondary:hover {
    background: white;
    color: #667eea;
  }

  .cta-button.large {
    padding: 1.25rem 2.5rem;
    font-size: 1.2rem;
  }

  /* Demo Visual */
  .hero-visual {
    display: flex;
    justify-content: center;
  }

  .demo-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
    width: 400px;
    overflow: hidden;
  }

  .demo-header {
    background: #f8f9fa;
    padding: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    border-bottom: 1px solid #e9ecef;
  }

  .demo-dots {
    display: flex;
    gap: 0.5rem;
  }

  .demo-dots span {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #dee2e6;
  }

  .demo-title {
    color: #666;
    font-weight: 500;
  }

  .demo-content {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .chat-bubble {
    padding: 0.75rem 1rem;
    border-radius: 12px;
    max-width: 80%;
    font-size: 0.9rem;
  }

  .chat-bubble.user {
    background: #667eea;
    color: white;
    align-self: flex-end;
  }

  .chat-bubble.assistant {
    background: #f1f3f4;
    color: #333;
    align-self: flex-start;
  }

  .typing-indicator {
    display: flex;
    gap: 0.25rem;
    align-self: flex-start;
    padding: 0.75rem;
  }

  .typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #667eea;
    animation: typing 1.4s infinite ease-in-out;
  }

  .typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
  }

  .typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes typing {
    0%, 60%, 100% {
      transform: translateY(0);
      opacity: 0.5;
    }
    30% {
      transform: translateY(-10px);
      opacity: 1;
    }
  }

  /* Features Section */
  .features {
    padding: 5rem 0;
    background: #f8f9fa;
  }

  .features h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: #333;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
  }

  .feature-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    text-align: center;
    transition: transform 0.3s ease;
  }

  .feature-card:hover {
    transform: translateY(-5px);
  }

  .feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .feature-card h3 {
    color: #333;
    margin-bottom: 1rem;
    font-size: 1.3rem;
  }

  .feature-card p {
    color: #666;
    line-height: 1.6;
  }

  /* How It Works Section */
  .how-it-works {
    padding: 5rem 0;
    background: white;
  }

  .how-it-works h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: #333;
  }

  .steps {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
  }

  .step {
    text-align: center;
    max-width: 250px;
  }

  .step-number {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: bold;
    margin: 0 auto 1rem;
  }

  .step-content h3 {
    color: #333;
    margin-bottom: 0.5rem;
  }

  .step-content p {
    color: #666;
    font-size: 0.95rem;
  }

  .step-arrow {
    font-size: 2rem;
    color: #667eea;
    font-weight: bold;
  }

  /* CTA Section */
  .cta-section {
    padding: 5rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
  }

  .cta-content h2 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
  }

  .cta-content p {
    font-size: 1.2rem;
    margin-bottom: 2rem;
    opacity: 0.9;
  }

  /* Footer */
  .footer {
    background: #2c3e50;
    color: white;
    padding: 3rem 0 1rem;
  }

  .footer-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-bottom: 2rem;
  }

  .footer-section h4 {
    margin-bottom: 1rem;
    color: #ecf0f1;
  }

  .footer-section ul {
    list-style: none;
    padding: 0;
  }

  .footer-section li {
    margin-bottom: 0.5rem;
  }

  .footer-link {
    background: none;
    border: none;
    color: #bdc3c7;
    cursor: pointer;
    padding: 0;
    font-size: inherit;
    text-decoration: underline;
  }

  .footer-link:hover {
    color: white;
  }

  .footer-bottom {
    border-top: 1px solid #34495e;
    padding-top: 1rem;
    text-align: center;
    color: #bdc3c7;
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .container {
      padding: 0 1rem;
    }

    .hero {
      min-height: calc(100vh - 64px);
      padding: 2rem 0;
    }

    .hero-content {
      grid-template-columns: 1fr;
      text-align: center;
      gap: 2rem;
    }

    .hero-text h1 {
      font-size: 2.5rem;
    }

    .demo-card {
      width: 100%;
      max-width: 350px;
    }

    .steps {
      flex-direction: column;
    }

    .step-arrow {
      transform: rotate(90deg);
    }

    .hero-buttons {
      justify-content: center;
    }
  }

  @media (max-width: 480px) {
    .hero-text h1 {
      font-size: 2rem;
    }

    .hero-subtitle {
      font-size: 1.1rem;
    }

    .cta-button {
      padding: 0.75rem 1.5rem;
      font-size: 1rem;
    }

    .features h2,
    .how-it-works h2,
    .cta-content h2 {
      font-size: 2rem;
    }
  }
</style>