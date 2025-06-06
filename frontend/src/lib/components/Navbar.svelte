<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  let user = null;
  let isAuthenticated = false;
  let showUserMenu = false;

  onMount(() => {
    checkAuthStatus();
  });

  function checkAuthStatus() {
    if (browser) {
      const token = localStorage.getItem('access_token');
      const userData = localStorage.getItem('user');
      
      if (token && userData) {
        try {
          user = JSON.parse(userData);
          isAuthenticated = true;
        } catch (error) {
          console.error('Error parsing user data:', error);
          handleSignOut();
        }
      }
    }
  }

  function handleSignOut() {
    if (browser) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
    user = null;
    isAuthenticated = false;
    showUserMenu = false;
    goto('/sign');
  }

  function toggleUserMenu() {
    showUserMenu = !showUserMenu;
  }

  // Close menu when clicking outside
  function handleOutsideClick(event) {
    if (!event.target.closest('.user-menu-container')) {
      showUserMenu = false;
    }
  }
</script>

<svelte:window on:click={handleOutsideClick} />

<nav class="navbar">
  <div class="nav-container">
    <!-- Brand -->
    <div class="brand">
      <a href="/" class="brand-link">
        <h2>RAG AI</h2>
      </a>
    </div>

    <!-- User Actions -->
    <div class="nav-actions">
      {#if isAuthenticated}
        <div class="user-menu-container">
          <button class="user-button" on:click={toggleUserMenu}>
            <div class="user-avatar">
              {user?.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <span class="user-name">{user?.full_name || user?.email || 'User'}</span>
            <svg class="chevron" class:rotated={showUserMenu} viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>

          {#if showUserMenu}
            <div class="user-dropdown">
              <div class="user-info">
                <div class="user-details">
                  <p class="user-display-name">{user?.full_name || 'User'}</p>
                  <p class="user-email">{user?.email}</p>
                </div>
              </div>
              <div class="menu-divider"></div>
              <button class="menu-item" on:click={handleSignOut}>
                <svg viewBox="0 0 20 20" fill="currentColor" class="menu-icon">
                  <path fill-rule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clip-rule="evenodd" />
                </svg>
                Sign Out
              </button>
            </div>
          {/if}
        </div>
      {:else}
        <a href="/sign" class="sign-in-btn">Sign In</a>
      {/if}
    </div>
  </div>
</nav>

<style>
  .navbar {
    background: white;
    border-bottom: 1px solid #e5e7eb;
    position: sticky;
    top: 0;
    z-index: 50;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  }

  .nav-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 4rem;
  }

  .brand-link {
    text-decoration: none;
    color: inherit;
  }

  .brand h2 {
    margin: 0;
    color: #1f2937;
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .nav-actions {
    display: flex;
    align-items: center;
  }

  .sign-in-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s;
  }

  .sign-in-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .user-menu-container {
    position: relative;
  }

  .user-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: none;
    border: none;
    padding: 0.5rem;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .user-button:hover {
    background-color: #f3f4f6;
  }

  .user-avatar {
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
  }

  .user-name {
    color: #374151;
    font-weight: 500;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chevron {
    width: 1rem;
    height: 1rem;
    color: #6b7280;
    transition: transform 0.2s;
  }

  .chevron.rotated {
    transform: rotate(180deg);
  }

  .user-dropdown {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25);
    min-width: 200px;
    z-index: 50;
  }

  .user-info {
    padding: 1rem;
  }

  .user-display-name {
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.25rem 0;
  }

  .user-email {
    color: #6b7280;
    font-size: 0.875rem;
    margin: 0;
  }

  .menu-divider {
    height: 1px;
    background-color: #e5e7eb;
  }

  .menu-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    text-align: left;
    cursor: pointer;
    color: #374151;
    transition: background-color 0.2s;
  }

  .menu-item:hover {
    background-color: #f3f4f6;
  }

  .menu-icon {
    width: 1rem;
    height: 1rem;
    color: #6b7280;
  }

  @media (max-width: 768px) {
    .nav-container {
      padding: 0 1rem;
    }

    .user-name {
      display: none;
    }

    .brand h2 {
      font-size: 1.25rem;
    }
  }
</style>