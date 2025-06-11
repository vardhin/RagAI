<script>
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import Navbar from '$lib/components/Navbar.svelte';

  let isAuthenticated = false;
  let heroSection;
  let featuresSection;
  let stepsSection;
  let ctaSection;

  onMount(() => {
    if (browser) {
      const token = localStorage.getItem('access_token');
      if (token) {
        isAuthenticated = true;
      }

      // Load GSAP
      loadGSAP().then(() => {
        initAnimations();
      });
    }
  });

  async function loadGSAP() {
    const gsap = await import('gsap');
    const ScrollTrigger = await import('gsap/ScrollTrigger');
    
    gsap.default.registerPlugin(ScrollTrigger.default);
    window.gsap = gsap.default;
    window.ScrollTrigger = ScrollTrigger.default;
  }

  function initAnimations() {
    // Hero section animations
    const tl = gsap.timeline();
    
    // Initial state - hide elements
    gsap.set(['.hero-text', '.hero-visual'], { opacity: 0, y: 50 });
    gsap.set('.demo-card', { scale: 0.8, rotation: 5 });
    gsap.set('.chat-bubble', { opacity: 0, x: -30 });
    gsap.set('.typing-indicator', { opacity: 0 });

    // Hero entrance animation
    tl.to('.hero-text', {
      duration: 1.2,
      opacity: 1,
      y: 0,
      ease: "power3.out"
    })
    .to('.hero-visual', {
      duration: 1,
      opacity: 1,
      y: 0,
      ease: "power3.out"
    }, "-=0.6")
    .to('.demo-card', {
      duration: 0.8,
      scale: 1,
      rotation: 0,
      ease: "back.out(1.7)"
    }, "-=0.4")
    .to('.chat-bubble.user', {
      duration: 0.6,
      opacity: 1,
      x: 0,
      ease: "power2.out"
    }, "-=0.2")
    .to('.chat-bubble.assistant', {
      duration: 0.6,
      opacity: 1,
      x: 0,
      ease: "power2.out"
    }, "+=0.5")
    .to('.typing-indicator', {
      duration: 0.4,
      opacity: 1,
      ease: "power2.out"
    }, "+=0.3");

    // Floating animation for demo card
    gsap.to('.demo-card', {
      duration: 3,
      y: -10,
      ease: "power1.inOut",
      repeat: -1,
      yoyo: true
    });

    // Features section animation
    gsap.set('.feature-card', { opacity: 0, y: 50, scale: 0.9 });
    
    ScrollTrigger.create({
      trigger: '.features',
      start: "top 80%",
      onEnter: () => {
        gsap.to('.feature-card', {
          duration: 0.8,
          opacity: 1,
          y: 0,
          scale: 1,
          stagger: 0.1,
          ease: "power3.out"
        });
      }
    });

    // Feature cards hover animations
    document.querySelectorAll('.feature-card').forEach(card => {
      card.addEventListener('mouseenter', () => {
        gsap.to(card, {
          duration: 0.3,
          y: -10,
          scale: 1.02,
          boxShadow: "0 20px 40px rgba(0,0,0,0.15)",
          ease: "power2.out"
        });
      });

      card.addEventListener('mouseleave', () => {
        gsap.to(card, {
          duration: 0.3,
          y: 0,
          scale: 1,
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
          ease: "power2.out"
        });
      });
    });

    // Steps section animation
    gsap.set('.step', { opacity: 0, y: 50 });
    gsap.set('.step-arrow', { opacity: 0, scale: 0 });
    
    ScrollTrigger.create({
      trigger: '.how-it-works',
      start: "top 70%",
      onEnter: () => {
        const stepTl = gsap.timeline();
        stepTl.to('.step', {
          duration: 0.8,
          opacity: 1,
          y: 0,
          stagger: 0.2,
          ease: "power3.out"
        })
        .to('.step-arrow', {
          duration: 0.5,
          opacity: 1,
          scale: 1,
          stagger: 0.1,
          ease: "back.out(1.7)"
        }, "-=0.4");
      }
    });

    // Step numbers pulsing animation
    gsap.to('.step-number', {
      duration: 2,
      scale: 1.1,
      ease: "power1.inOut",
      repeat: -1,
      yoyo: true,
      stagger: 0.3
    });

    // CTA section animation
    gsap.set('.cta-content > *', { opacity: 0, y: 30 });
    
    ScrollTrigger.create({
      trigger: '.cta-section',
      start: "top 80%",
      onEnter: () => {
        gsap.to('.cta-content > *', {
          duration: 0.8,
          opacity: 1,
          y: 0,
          stagger: 0.2,
          ease: "power3.out"
        });
      }
    });

    // Button animations
    document.querySelectorAll('.cta-button').forEach(button => {
      button.addEventListener('mouseenter', () => {
        gsap.to(button, {
          duration: 0.3,
          scale: 1.05,
          ease: "power2.out"
        });
      });

      button.addEventListener('mouseleave', () => {
        gsap.to(button, {
          duration: 0.3,
          scale: 1,
          ease: "power2.out"
        });
      });
    });

    // Parallax effect for hero background
    ScrollTrigger.create({
      trigger: '.hero',
      start: "top top",
      end: "bottom top",
      scrub: 1,
      onUpdate: (self) => {
        gsap.to('.hero', {
          duration: 0.3,
          backgroundPosition: `50% ${50 + self.progress * 20}%`,
          ease: "none"
        });
      }
    });

    // Footer animation
    gsap.set('.footer-section', { opacity: 0, y: 30 });
    
    ScrollTrigger.create({
      trigger: '.footer',
      start: "top 90%",
      onEnter: () => {
        gsap.to('.footer-section', {
          duration: 0.6,
          opacity: 1,
          y: 0,
          stagger: 0.1,
          ease: "power2.out"
        });
      }
    });
  }

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
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>
</svelte:head>

<!-- Add Navbar -->
<Navbar />

<main class="landing">
  <!-- Hero Section -->
  <section class="hero" bind:this={heroSection}>
    <div class="hero-particles"></div>
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
  <section class="features" bind:this={featuresSection}>
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
  <section class="how-it-works" bind:this={stepsSection}>
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
  <section class="cta-section" bind:this={ctaSection}>
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
    overflow-y: auto;
    overflow-x: hidden;
  }

  .landing {
    padding-top: 0;
    min-height: 100vh;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
  }

  /* Hero Section with enhanced animations */
  .hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 4rem 0;
    min-height: calc(100vh - 64px);
    display: flex;
    align-items: center;
    position: relative;
    overflow: hidden;
  }

  .hero-particles {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at 20% 80%, rgba(255,255,255,0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255,255,255,0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(255,255,255,0.05) 0%, transparent 50%);
    pointer-events: none;
    animation: particleFloat 20s ease-in-out infinite;
  }

  @keyframes particleFloat {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    33% { transform: translateY(-20px) rotate(1deg); }
    66% { transform: translateY(10px) rotate(-1deg); }
  }

  .hero-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    align-items: center;
    position: relative;
    z-index: 1;
  }

  .hero-text h1 {
    font-size: 3.5rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    line-height: 1.2;
    background: linear-gradient(45deg, #ffffff, #e8f4fd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
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
    border-radius: 12px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    text-decoration: none;
    border: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
  }

  .cta-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
  }

  .cta-button:hover::before {
    left: 100%;
  }

  .cta-button.primary {
    background: linear-gradient(135deg, #ffffff, #f8f9fa);
    color: #667eea;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  }

  .cta-button.primary:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.2);
  }

  .cta-button.secondary {
    background: transparent;
    color: white;
    border: 2px solid rgba(255,255,255,0.8);
    backdrop-filter: blur(10px);
  }

  .cta-button.secondary:hover {
    background: rgba(255,255,255,0.1);
    border-color: white;
  }

  .cta-button.large {
    padding: 1.25rem 2.5rem;
    font-size: 1.2rem;
  }

  /* Enhanced Demo Visual */
  .hero-visual {
    display: flex;
    justify-content: center;
  }

  .demo-card {
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(20px);
    border-radius: 16px;
    box-shadow: 0 25px 80px rgba(0,0,0,0.3);
    width: 400px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.2);
  }

  .demo-header {
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    padding: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    border-bottom: 1px solid rgba(0,0,0,0.05);
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
    animation: dotPulse 2s ease-in-out infinite;
  }

  .demo-dots span:nth-child(2) { animation-delay: 0.2s; }
  .demo-dots span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes dotPulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
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
    border-radius: 16px;
    max-width: 80%;
    font-size: 0.9rem;
    position: relative;
  }

  .chat-bubble.user {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    align-self: flex-end;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }

  .chat-bubble.assistant {
    background: linear-gradient(135deg, #f1f3f4, #e8eaed);
    color: #333;
    align-self: flex-start;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
    background: linear-gradient(135deg, #667eea, #764ba2);
    animation: typing 1.4s infinite ease-in-out;
  }

  .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
  .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

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

  /* Enhanced Features Section */
  .features {
    padding: 5rem 0;
    background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
  }

  .features h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: #333;
    background: linear-gradient(135deg, #333, #667eea);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
  }

  .feature-card {
    background: white;
    padding: 2rem;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid rgba(0,0,0,0.05);
    position: relative;
    overflow: hidden;
  }

  .feature-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    transform: scaleX(0);
    transition: transform 0.3s ease;
  }

  .feature-card:hover::before {
    transform: scaleX(1);
  }

  .feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
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

  /* Enhanced How It Works Section */
  .how-it-works {
    padding: 5rem 0;
    background: white;
    position: relative;
  }

  .how-it-works::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: 
      radial-gradient(circle at 10% 20%, rgba(102, 126, 234, 0.05) 0%, transparent 50%),
      radial-gradient(circle at 90% 80%, rgba(118, 75, 162, 0.05) 0%, transparent 50%);
    pointer-events: none;
  }

  .how-it-works h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: #333;
    position: relative;
    z-index: 1;
  }

  .steps {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
    position: relative;
    z-index: 1;
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
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    position: relative;
  }

  .step-number::before {
    content: '';
    position: absolute;
    top: -5px;
    left: -5px;
    width: calc(100% + 10px);
    height: calc(100% + 10px);
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: -1;
  }

  .step:hover .step-number::before {
    opacity: 0.2;
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
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  /* Enhanced CTA Section */
  .cta-section {
    padding: 5rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
    position: relative;
    overflow: hidden;
  }

  .cta-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: 
      radial-gradient(circle at 20% 80%, rgba(255,255,255,0.1) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);
    pointer-events: none;
    animation: ctaFloat 15s ease-in-out infinite;
  }

  @keyframes ctaFloat {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-10px) scale(1.02); }
  }

  .cta-content {
    position: relative;
    z-index: 1;
  }

  .cta-content h2 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .cta-content p {
    font-size: 1.2rem;
    margin-bottom: 2rem;
    opacity: 0.9;
  }

  /* Enhanced Footer */
  .footer {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    color: white;
    padding: 3rem 0 1rem;
    position: relative;
  }

  .footer::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, #667eea, #764ba2);
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
    font-size: 1.1rem;
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
    text-decoration: none;
    transition: color 0.3s ease;
  }

  .footer-link:hover {
    color: #667eea;
  }

  .footer-bottom {
    border-top: 1px solid rgba(255,255,255,0.1);
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

  /* Smooth scrolling */
  :global(html) {
    scroll-behavior: smooth;
  }

  /* Custom scrollbar */
  :global(::-webkit-scrollbar) {
    width: 8px;
  }

  :global(::-webkit-scrollbar-track) {
    background: #f1f1f1;
  }

  :global(::-webkit-scrollbar-thumb) {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 4px;
  }

  :global(::-webkit-scrollbar-thumb:hover) {
    background: linear-gradient(135deg, #5a6fd8, #6a4c93);
  }
</style>