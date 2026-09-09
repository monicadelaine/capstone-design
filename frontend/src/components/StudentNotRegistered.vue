<script setup>
import { useAuth0 } from '@auth0/auth0-vue';

const { logout } = useAuth0();

const handleLogout = () => {
  logout({ logoutParams: { returnTo: window.location.origin } });
};
</script>

<template>
  <div class="error-container">
    <div class="error-card">
      <div class="error-icon">⚠️</div>
      <h1>Access Denied</h1>
      <p class="error-message">
        Your email was not found in the capstone database. You are likely not in the 
        <strong>CS capstone design class, CS 495</strong>.
      </p>
      <p class="help-text">
        If you are in the class and need access to this site, contact your professor 
        or the admin of the CS Capstone Class.
      </p>
      <div class="actions">
        <button @click="handleLogout" class="btn-primary">Logout</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  background: var(--background-default);
}

.error-card {
  background: white;
  padding: 3rem;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  text-align: center;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

h1 {
  color: #991b1b;
  font-size: 2rem;
  margin-bottom: 1rem;
}

.error-message {
  font-size: 1.1rem;
  margin-bottom: 1rem;
  line-height: 1.6;
  color: var(--text-default);
}

.help-text {
  font-size: 0.95rem;
  color: var(--text-subtle);
  margin-bottom: 2rem;
  line-height: 1.6;
}

.actions {
  margin-top: 2rem;
}

.btn-primary {
  background-color: var(--accent-primary);
  color: white;
  padding: 0.75rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  filter: brightness(0.9);
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
