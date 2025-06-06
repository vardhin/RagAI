<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  // State management
  let isSignup = false;
  let isLoading = false;
  let showPassword = false;
  let showConfirmPassword = false;

  // Form data
  let formData = {
    email: '',
    password: '',
    confirmPassword: '',
    username: ''
  };

  // Validation states
  let errors = {};
  let touched = {};
  let isFormValid = false;

  // API base URL - adjust as needed
  const API_BASE_URL = 'http://localhost:8000';

  // Validation rules
  const validationRules = {
    email: {
      required: true,
      pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      message: 'Please enter a valid email address'
    },
    username: {
      required: true,
      minLength: 3,
      maxLength: 30,
      pattern: /^[a-zA-Z0-9_]+$/,
      message: 'Username must be 3-30 characters, alphanumeric and underscores only'
    },
    password: {
      required: true,
      minLength: 8,
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
      message: 'Password must be at least 8 characters with uppercase, lowercase, number, and special character'
    },
    confirmPassword: {
      required: true,
      match: 'password',
      message: 'Passwords do not match'
    }
  };

  // Validate individual field
  function validateField(field, value) {
    const rules = validationRules[field];
    if (!rules) return '';

    if (rules.required && !value.trim()) {
      return `${field.charAt(0).toUpperCase() + field.slice(1)} is required`;
    }

    if (value && rules.minLength && value.length < rules.minLength) {
      return `${field.charAt(0).toUpperCase() + field.slice(1)} must be at least ${rules.minLength} characters`;
    }

    if (value && rules.maxLength && value.length > rules.maxLength) {
      return `${field.charAt(0).toUpperCase() + field.slice(1)} must be no more than ${rules.maxLength} characters`;
    }

    if (value && rules.pattern && !rules.pattern.test(value)) {
      return rules.message;
    }

    if (rules.match && value !== formData[rules.match]) {
      return rules.message;
    }

    return '';
  }

  // Validate form
  function validateForm() {
    const newErrors = {};
    const fieldsToValidate = isSignup 
      ? ['email', 'username', 'password', 'confirmPassword']
      : ['email', 'password'];

    fieldsToValidate.forEach(field => {
      const error = validateField(field, formData[field]);
      if (error) newErrors[field] = error;
    });

    errors = newErrors;
    isFormValid = Object.keys(newErrors).length === 0;
    return isFormValid;
  }

  // Handle input changes
  function handleInput(field, value) {
    formData[field] = value;
    touched[field] = true;
    
    // Real-time validation
    if (touched[field]) {
      const error = validateField(field, value);
      if (error) {
        errors[field] = error;
      } else {
        delete errors[field];
      }
      errors = { ...errors };
    }
    
    validateForm();
  }

  // Handle form submission
  async function handleSubmit() {
    // Mark all fields as touched
    Object.keys(formData).forEach(field => {
      touched[field] = true;
    });

    if (!validateForm()) {
      return;
    }

    isLoading = true;
    
    try {
      const endpoint = isSignup ? '/auth/signup' : '/auth/signin';
      const payload = isSignup 
        ? {
            email: formData.email.trim(),
            password: formData.password,
            confirm_password: formData.confirmPassword, // Match backend field name
            full_name: formData.username.trim() // Match backend field name
          }
        : {
            email: formData.email.trim(),
            password: formData.password
          };

      console.log('Sending request to:', `${API_BASE_URL}${endpoint}`);
      console.log('Payload:', payload);

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        credentials: 'include'
      });

      console.log('Response status:', response.status);

      let data;
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        throw new Error(`Server returned non-JSON response: ${text}`);
      }

      console.log('Response data:', data);

      if (!response.ok) {
        // Handle different error response structures
        let errorMessage = 'Authentication failed';
        
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            // Handle validation errors from FastAPI
            errorMessage = data.detail.map(err => err.msg).join(', ');
          } else {
            errorMessage = JSON.stringify(data.detail);
          }
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.error) {
          errorMessage = data.error;
        }
        
        throw new Error(errorMessage);
      }

      // Store tokens securely
      if (browser) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        // Note: Backend doesn't return user object, so we'll create one
        const userInfo = {
          email: formData.email.trim(),
          full_name: isSignup ? formData.username.trim() : 'User'
        };
        localStorage.setItem('user', JSON.stringify(userInfo));
      }

      // Show success message
      showNotification(`${isSignup ? 'Account created' : 'Signed in'} successfully!`, 'success');
      
      // Redirect to dashboard or home page
      await goto('/');

    } catch (error) {
      console.error('Auth error:', error);
      
      // Handle specific error cases
      let errorMessage = error.message || 'Authentication failed';
      
      // Clear previous errors
      errors = {};
      
      if (errorMessage.toLowerCase().includes('already exists') || 
          errorMessage.toLowerCase().includes('already registered')) {
        errorMessage = 'An account with this email already exists';
        errors.email = errorMessage;
      } else if (errorMessage.toLowerCase().includes('invalid email') || 
                 errorMessage.toLowerCase().includes('incorrect')) {
        errorMessage = 'Invalid email or password';
        errors.email = errorMessage;
        errors.password = errorMessage;
      } else if (errorMessage.toLowerCase().includes('password') && 
                 errorMessage.toLowerCase().includes('match')) {
        errors.confirmPassword = 'Passwords do not match';
      } else if (errorMessage.toLowerCase().includes('network') || 
                 errorMessage.toLowerCase().includes('fetch')) {
        errorMessage = 'Network error. Please check your connection and try again.';
      } else if (errorMessage.includes('Server returned non-JSON')) {
        errorMessage = 'Server error. Please try again later.';
      }
      
      showNotification(errorMessage, 'error');
      errors = { ...errors };
    } finally {
      isLoading = false;
    }
  }

  // Toggle between signup and signin
  function toggleMode() {
    isSignup = !isSignup;
    // Reset form
    formData = {
      email: '',
      password: '',
      confirmPassword: '',
      username: ''
    };
    errors = {};
    touched = {};
    isFormValid = false;
  }

  // Show notification (you can replace this with your preferred notification system)
  function showNotification(message, type = 'info') {
    // Simple notification - replace with your toast/notification component
    if (browser) {
      const notification = document.createElement('div');
      notification.className = `notification notification-${type}`;
      notification.textContent = message;
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        max-width: 300px;
        background-color: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
      `;
      
      document.body.appendChild(notification);
      
      setTimeout(() => {
        notification.remove();
      }, 5000);
    }
  }

  // Check if user is already authenticated
  onMount(() => {
    if (browser) {
      const token = localStorage.getItem('access_token');
      if (token) {
        goto('/');
      }
    }
  });

  // Handle keyboard shortcuts
  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }
</script>

<svelte:head>
  <title>{isSignup ? 'Sign Up' : 'Sign In'} - RAG AI</title>
  <meta name="description" content={isSignup ? 'Create your account' : 'Sign in to your account'} />
</svelte:head>

<div class="auth-container" on:keydown={handleKeydown}>
  <div class="auth-card">
    <!-- Header -->
    <div class="header">
      <h1>{isSignup ? 'Create Account' : 'Welcome Back'}</h1>
      <p>{isSignup ? 'Sign up to get started with RAG AI' : 'Sign in to your account'}</p>
    </div>

    <!-- Form -->
    <form on:submit|preventDefault={handleSubmit} class="form">
      <!-- Email Field -->
      <div class="field">
        <label for="email" class="label">Email Address</label>
        <input
          id="email"
          type="email"
          bind:value={formData.email}
          on:input={(e) => handleInput('email', e.target.value)}
          on:blur={() => touched.email = true}
          class="input"
          class:error={touched.email && errors.email}
          placeholder="Enter your email"
          autocomplete="email"
          disabled={isLoading}
          required
        />
        {#if touched.email && errors.email}
          <span class="error-message">{errors.email}</span>
        {/if}
      </div>

      <!-- Username Field (Signup only) -->
      {#if isSignup}
        <div class="field">
          <label for="username" class="label">Username</label>
          <input
            id="username"
            type="text"
            bind:value={formData.username}
            on:input={(e) => handleInput('username', e.target.value)}
            on:blur={() => touched.username = true}
            class="input"
            class:error={touched.username && errors.username}
            placeholder="Choose a username"
            autocomplete="username"
            disabled={isLoading}
            required
          />
          {#if touched.username && errors.username}
            <span class="error-message">{errors.username}</span>
          {/if}
        </div>
      {/if}

      <!-- Password Field -->
      <div class="field">
        <label for="password" class="label">Password</label>
        <div class="password-wrapper">
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            bind:value={formData.password}
            on:input={(e) => handleInput('password', e.target.value)}
            on:blur={() => touched.password = true}
            class="input"
            class:error={touched.password && errors.password}
            placeholder="Enter your password"
            autocomplete={isSignup ? 'new-password' : 'current-password'}
            disabled={isLoading}
            required
          />
          <button
            type="button"
            class="password-toggle"
            on:click={() => showPassword = !showPassword}
            disabled={isLoading}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? '👁️' : '👁️‍🗨️'}
          </button>
        </div>
        {#if touched.password && errors.password}
          <span class="error-message">{errors.password}</span>
        {/if}
      </div>

      <!-- Confirm Password Field (Signup only) -->
      {#if isSignup}
        <div class="field">
          <label for="confirmPassword" class="label">Confirm Password</label>
          <div class="password-wrapper">
            <input
              id="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              bind:value={formData.confirmPassword}
              on:input={(e) => handleInput('confirmPassword', e.target.value)}
              on:blur={() => touched.confirmPassword = true}
              class="input"
              class:error={touched.confirmPassword && errors.confirmPassword}
              placeholder="Confirm your password"
              autocomplete="new-password"
              disabled={isLoading}
              required
            />
            <button
              type="button"
              class="password-toggle"
              on:click={() => showConfirmPassword = !showConfirmPassword}
              disabled={isLoading}
              aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
            >
              {showConfirmPassword ? '👁️' : '👁️‍🗨️'}
            </button>
          </div>
          {#if touched.confirmPassword && errors.confirmPassword}
            <span class="error-message">{errors.confirmPassword}</span>
          {/if}
        </div>
      {/if}

      <!-- Submit Button -->
      <button
        type="submit"
        class="submit-btn"
        disabled={isLoading || !isFormValid}
        aria-label={isSignup ? 'Create account' : 'Sign in'}
      >
        {#if isLoading}
          <span class="spinner"></span>
          {isSignup ? 'Creating Account...' : 'Signing In...'}
        {:else}
          {isSignup ? 'Create Account' : 'Sign In'}
        {/if}
      </button>
    </form>

    <!-- Toggle Mode -->
    <div class="toggle">
      <p>
        {isSignup ? 'Already have an account?' : "Don't have an account?"}
        <button
          type="button"
          class="toggle-btn"
          on:click={toggleMode}
          disabled={isLoading}
        >
          {isSignup ? 'Sign In' : 'Sign Up'}
        </button>
      </p>
    </div>
  </div>
</div>

<style>
  .auth-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
  }

  .auth-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    padding: 2rem;
    width: 100%;
    max-width: 400px;
  }

  .header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .header h1 {
    font-size: 1.875rem;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
  }

  .header p {
    color: #6b7280;
    margin: 0;
  }

  .form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .label {
    font-weight: 500;
    color: #374151;
    font-size: 0.875rem;
  }

  .input {
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 1rem;
    transition: all 0.2s;
    background: white;
  }

  .input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  .input:disabled {
    background-color: #f9fafb;
    cursor: not-allowed;
  }

  .input.error {
    border-color: #ef4444;
  }

  .input.error:focus {
    border-color: #ef4444;
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
  }

  .password-wrapper {
    position: relative;
  }

  .password-toggle {
    position: absolute;
    right: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.125rem;
    padding: 0.25rem;
    border-radius: 4px;
    transition: background-color 0.2s;
  }

  .password-toggle:hover:not(:disabled) {
    background-color: #f3f4f6;
  }

  .password-toggle:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  .error-message {
    color: #ef4444;
    font-size: 0.875rem;
    margin-top: 0.25rem;
  }

  .submit-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 0.875rem;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  .submit-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25);
  }

  .submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .toggle {
    text-align: center;
    margin-top: 1.5rem;
  }

  .toggle p {
    color: #6b7280;
    margin: 0;
  }

  .toggle-btn {
    background: none;
    border: none;
    color: #667eea;
    font-weight: 600;
    cursor: pointer;
    text-decoration: underline;
    padding: 0;
    margin-left: 0.25rem;
  }

  .toggle-btn:hover:not(:disabled) {
    color: #5a67d8;
  }

  .toggle-btn:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  /* Responsive design */
  @media (max-width: 480px) {
    .auth-container {
      padding: 0.5rem;
    }

    .auth-card {
      padding: 1.5rem;
    }

    .header h1 {
      font-size: 1.5rem;
    }
  }

  /* Accessibility improvements */
  @media (prefers-reduced-motion: reduce) {
    .submit-btn,
    .input,
    .password-toggle {
      transition: none;
    }

    .spinner {
      animation: none;
    }

    .submit-btn:hover:not(:disabled) {
      transform: none;
    }
  }

  /* High contrast mode support */
  @media (prefers-contrast: high) {
    .input {
      border-width: 2px;
    }
  }
</style>