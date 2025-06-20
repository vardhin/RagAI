<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { Bot, Mail, User, Lock, Eye, EyeOff, X, Loader2 } from 'lucide-svelte';

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
    fullName: ''
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
      pattern: /^[a-zA-Z0-9.]+@gmail\.com$/,
      message: 'Please enter a valid Gmail address (format: yourname@gmail.com)'
    },
    fullName: {
      required: true,
      minLength: 2,
      maxLength: 50,
      pattern: /^[a-zA-Z\s]+$/,
      message: 'Full name must contain only letters and spaces, 2-50 characters'
    },
    password: {
      required: true,
      minLength: 8,
      maxLength: 30,
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?])[A-Za-z\d!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]{8,30}$/,
      message: 'Password must be 8-30 characters with at least one lowercase letter, one uppercase letter, one number, and one special character (!@#$%^&*()_+-=[]{};\':"\\|,.<>/?)'
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
      ? ['email', 'fullName', 'password', 'confirmPassword']
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
      // Fix the endpoint paths to match backend
      const endpoint = isSignup ? '/signup' : '/signin';
      const payload = isSignup 
        ? {
            email: formData.email.trim(),
            password: formData.password,
            confirm_password: formData.confirmPassword,
            full_name: formData.fullName.trim()
          }
        : {
            email: formData.email.trim(),
            password: formData.password
          };

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        credentials: 'include'
      });


      let data;
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        throw new Error(`Server returned non-JSON response: ${text}`);
      }


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
        
        // Handle user info differently for signup vs signin
        if (isSignup) {
          // For signup, use the form data
          const userInfo = {
            email: formData.email.trim(),
            full_name: formData.fullName.trim()
          };
          localStorage.setItem('user', JSON.stringify(userInfo));
        } else {
          // For signin, fetch user profile from backend
          try {
            const profileResponse = await fetch(`${API_BASE_URL}/profile`, {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${data.access_token}`,
                'Content-Type': 'application/json',
              },
              credentials: 'include'
            });

            if (profileResponse.ok) {
              const profileData = await profileResponse.json();
              const userInfo = {
                email: profileData.email || formData.email.trim(),
                full_name: profileData.full_name || 'User'
              };
              localStorage.setItem('user', JSON.stringify(userInfo));
            } else {
              // Fallback if profile fetch fails
              const userInfo = {
                email: formData.email.trim(),
                full_name: 'User'
              };
              localStorage.setItem('user', JSON.stringify(userInfo));
            }
          } catch (profileError) {
            console.error('Failed to fetch user profile:', profileError);
            // Fallback if profile fetch fails
            const userInfo = {
              email: formData.email.trim(),
              full_name: 'User'
            };
            localStorage.setItem('user', JSON.stringify(userInfo));
          }
        }
      }

      // Show success message
      showNotification(`${isSignup ? 'Account created' : 'Signed in'} successfully!`, 'success');
      
      // Redirect to dashboard or home page
      await goto('/app');

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
      fullName: ''
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
        goto('/app');
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
      <div class="logo">
        <div class="logo-icon">
          <Bot size={24} color="white" />
        </div>
        <span class="logo-text">RAG AI</span>
      </div>
      <h1>{isSignup ? 'Create Account' : 'Welcome Back'}</h1>
      <p>{isSignup ? 'Sign up to get started with RAG AI' : 'Sign in to your account'}</p>
    </div>

    <!-- Form -->
    <form on:submit|preventDefault={handleSubmit} class="form" class:signin={!isSignup}>
      <!-- Email Field -->
      <div class="field-group">
        <label for="email" class="field-label">
          <span class="label-text">Email Address</span>
          <span class="required">*</span>
        </label>
        <div class="input-wrapper">
          <div class="input-icon">
            <Mail size={20} />
          </div>
          <input
            id="email"
            type="email"
            bind:value={formData.email}
            on:input={(e) => handleInput('email', e.target.value)}
            on:blur={() => touched.email = true}
            class="field-input"
            class:error={touched.email && errors.email}
            class:success={touched.email && !errors.email && formData.email}
            placeholder="Enter your email address"
            autocomplete="email"
            disabled={isLoading}
            required
          />
        </div>
        {#if touched.email && errors.email}
          <div class="error-message">
            <X size={16} />
            {errors.email}
          </div>
        {/if}
      </div>

      <!-- Full Name Field (Signup only) -->
      {#if isSignup}
        <div class="field-group">
          <label for="fullName" class="field-label">
            <span class="label-text">Full Name</span>
            <span class="required">*</span>
          </label>
          <div class="input-wrapper">
            <div class="input-icon">
              <User size={20} />
            </div>
            <input
              id="fullName"
              type="text"
              bind:value={formData.fullName}
              on:input={(e) => handleInput('fullName', e.target.value)}
              on:blur={() => touched.fullName = true}
              class="field-input"
              class:error={touched.fullName && errors.fullName}
              class:success={touched.fullName && !errors.fullName && formData.fullName}
              placeholder="Enter your full name"
              autocomplete="name"
              disabled={isLoading}
              required
            />
          </div>
          {#if touched.fullName && errors.fullName}
            <div class="error-message">
              <X size={16} />
              {errors.fullName}
            </div>
          {/if}
        </div>
      {/if}

      <!-- Password Field -->
      <div class="field-group">
        <label for="password" class="field-label">
          <span class="label-text">Password</span>
          <span class="required">*</span>
        </label>
        <div class="input-wrapper">
          <div class="input-icon">
            <Lock size={20} />
          </div>
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            bind:value={formData.password}
            on:input={(e) => handleInput('password', e.target.value)}
            on:blur={() => touched.password = true}
            class="field-input"
            class:error={touched.password && errors.password}
            class:success={touched.password && !errors.password && formData.password}
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
            {#if showPassword}
              <Eye size={20} />
            {:else}
              <EyeOff size={20} />
            {/if}
          </button>
        </div>
        {#if touched.password && errors.password}
          <div class="error-message">
            <X size={16} />
            {errors.password}
          </div>
        {/if}
      </div>

      <!-- Confirm Password Field (Signup only) -->
      {#if isSignup}
        <div class="field-group">
          <label for="confirmPassword" class="field-label">
            <span class="label-text">Confirm Password</span>
            <span class="required">*</span>
          </label>
          <div class="input-wrapper">
            <div class="input-icon">
              <Lock size={20} />
            </div>
            <input
              id="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              bind:value={formData.confirmPassword}
              on:input={(e) => handleInput('confirmPassword', e.target.value)}
              on:blur={() => touched.confirmPassword = true}
              class="field-input"
              class:error={touched.confirmPassword && errors.confirmPassword}
              class:success={touched.confirmPassword && !errors.confirmPassword && formData.confirmPassword}
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
              {#if showConfirmPassword}
                <Eye size={20} />
              {:else}
                <EyeOff size={20} />
              {/if}
            </button>
          </div>
          {#if touched.confirmPassword && errors.confirmPassword}
            <div class="error-message">
              <X size={16} />
              {errors.confirmPassword}
            </div>
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
          <Loader2 size={16} class="spinner" />
          {isSignup ? 'Creating Account...' : 'Signing In...'}
        {:else}
          {isSignup ? 'Create Account' : 'Sign In'}
        {/if}
      </button>
    </form>

    <!-- Toggle Mode -->
    <div class="toggle-section">
      <div class="divider">
        <span>or</span>
      </div>
      <p class="toggle-text">
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
  :root {
    --primary-600: #4f46e5;
    --primary-700: #4338ca;
    --primary-50: #eef2ff;
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
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    --border-radius: 6px;
    --border-radius-lg: 10px;
    --spacing-unit: 1rem;
  }

  /* Disable scrolling */
  :global(html, body) {
    overflow: hidden;
    height: 100vh;
    padding: 0%;
    margin: 0%;

  }

  * {
    box-sizing: border-box;
  }

  .auth-container {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow: hidden;
  }

  .auth-card {
    background: white;
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-xl);
    padding: 1.5rem 2rem;
    width: 100%;
    max-width: 800px;
    border: 1px solid var(--gray-200);
    max-height: 95vh;
    overflow-y: auto;
  }

  .header {
    text-align: center;
    margin-bottom: 1.5rem;
  }

  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .logo-icon {
    background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-lg);
  }

  .logo-text {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--gray-800);
    letter-spacing: -0.025em;
  }

  .header h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--gray-900);
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.025em;
  }

  .header p {
    color: var(--gray-500);
    margin: 0;
    font-size: 0.9375rem;
  }

  .form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem 1.5rem;
  }

  /* Make submit button and toggle section span full width */
  .submit-btn {
    grid-column: 1 / -1;
  }

  /* Single column layout for signin */
  .form.signin {
    grid-template-columns: 1fr;
    max-width: 400px;
    margin: 0 auto;
  }

  .field-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .field-label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-weight: 500;
    color: var(--gray-700);
    font-size: 0.8125rem;
    margin-bottom: 0.125rem;
  }

  .label-text {
    font-weight: 500;
  }

  .required {
    color: var(--red-500);
  }

  .input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .input-icon {
    position: absolute;
    left: 0.875rem;
    color: var(--gray-400);
    z-index: 1;
    pointer-events: none;
    transition: color 0.2s ease;
  }

  .field-input {
    width: 100%;
    padding: 0.75rem 0.875rem 0.75rem 2.5rem;
    border: 2px solid var(--gray-200);
    border-radius: var(--border-radius);
    font-size: 0.9375rem;
    transition: all 0.2s ease;
    background: white;
    color: var(--gray-900);
    line-height: 1.4;
  }

  .field-input::placeholder {
    color: var(--gray-400);
    font-size: 0.875rem;
  }

  .field-input:focus {
    outline: none;
    border-color: var(--primary-600);
    box-shadow: 0 0 0 3px var(--primary-50);
  }

  .field-input:focus + .input-icon,
  .field-input:not(:placeholder-shown) + .input-icon {
    color: var(--primary-600);
  }

  .field-input:disabled {
    background-color: var(--gray-50);
    cursor: not-allowed;
    color: var(--gray-500);
  }

  .field-input.error {
    border-color: var(--red-500);
    background-color: var(--red-50);
  }

  .field-input.error:focus {
    border-color: var(--red-500);
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
  }

  .field-input.success {
    border-color: var(--green-500);
  }

  .password-toggle {
    position: absolute;
    right: 0.875rem;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.375rem;
    border-radius: var(--border-radius);
    transition: all 0.2s ease;
    color: var(--gray-400);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .password-toggle:hover:not(:disabled) {
    background-color: var(--gray-100);
    color: var(--gray-600);
  }

  .password-toggle:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  .error-message {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    color: var(--red-500);
    font-size: 0.8125rem;
    margin-top: 0.125rem;
    padding: 0.375rem 0.625rem;
    background-color: var(--red-50);
    border-radius: var(--border-radius);
    border-left: 3px solid var(--red-500);
  }

  .submit-btn {
    background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
    color: white;
    border: none;
    padding: 0.875rem;
    border-radius: var(--border-radius);
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
    min-height: 2.75rem;
    letter-spacing: 0.025em;
  }

  .submit-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: var(--shadow-lg);
    background: linear-gradient(135deg, var(--primary-700), var(--primary-600));
  }

  .submit-btn:active:not(:disabled) {
    transform: translateY(0);
  }

  .submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  :global(.spinner) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .toggle-section {
    margin-top: 1.5rem;
    grid-column: 1 / -1;
  }

  .divider {
    text-align: center;
    margin: 1rem 0;
    position: relative;
  }

  .divider::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 1px;
    background: var(--gray-200);
  }

  .divider span {
    background: white;
    color: var(--gray-400);
    padding: 0 1rem;
    font-size: 0.8125rem;
    position: relative;
  }

  .toggle-text {
    text-align: center;
    color: var(--gray-600);
    margin: 0;
    font-size: 0.875rem;
  }

  .toggle-btn {
    background: none;
    border: none;
    color: var(--primary-600);
    font-weight: 600;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    margin-left: 0.25rem;
    border-radius: var(--border-radius);
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .toggle-btn:hover:not(:disabled) {
    color: var(--primary-700);
    background-color: var(--primary-50);
  }

  .toggle-btn:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .form {
      grid-template-columns: 1fr;
      max-width: 400px;
      margin: 0 auto;
    }
    
    .auth-card {
      max-width: 480px;
      padding: 1.25rem 1.5rem;
    }
  }

  @media (max-width: 480px) {
    .auth-container {
      padding: 0.5rem;
    }

    .auth-card {
      padding: 1rem 1.25rem;
      max-width: 100%;
    }

    .header h1 {
      font-size: 1.25rem;
    }

    .logo-text {
      font-size: 1.125rem;
    }

    .field-input {
      padding: 0.625rem 0.75rem 0.625rem 2.25rem;
    }

    .input-icon {
      left: 0.75rem;
    }
  }

  /* Accessibility improvements */
  @media (prefers-reduced-motion: reduce) {
    .submit-btn,
    .field-input,
    .password-toggle,
    .toggle-btn {
      transition: none;
    }

    :global(.spinner) {
      animation: none;
    }

    .submit-btn:hover:not(:disabled) {
      transform: none;
    }
  }

  /* High contrast mode support */
  @media (prefers-contrast: high) {
    .field-input {
      border-width: 3px;
    }
  }

  /* Focus visible for better keyboard navigation */
  .field-input:focus-visible,
  .password-toggle:focus-visible,
  .submit-btn:focus-visible,
  .toggle-btn:focus-visible {
    outline: 2px solid var(--primary-600);
    outline-offset: 2px;
  }
</style>