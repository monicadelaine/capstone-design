<script setup>
import Sidebar from './components/Sidebar.vue';
import { useAuth0 } from '@auth0/auth0-vue';
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import apiService from './services/api';

const { isAuthenticated, isLoading, user, logout: auth0Logout } = useAuth0();
const route = useRoute();

const ROLE_KEY = 'https://backend-api-capstone/roles';
const showDebug = ref(false);

function getUserRole() {
  if (!user.value) return null;
  const roles = user.value[ROLE_KEY];
  if (Array.isArray(roles) && roles.length > 0) {
    return roles[0].toLowerCase();
  }
  if (typeof roles === 'string') {
    return roles.toLowerCase();
  }
  return null;
}

const userRole = computed(() => getUserRole());
const userName = computed(() => {
  // return 'nickname', i.e. the user's email before the domain
  return user.value.nickname || 'User';
});

const showSidebar = computed(() => {
  // Don't show sidebar on login page
  if (route.path === '/' || route.name === 'Login') return false;
  return isAuthenticated.value && !isLoading.value;
});

const showFullWidth = computed(() => {
  // Full width on login page or when not authenticated
  if (route.path === '/' || route.name === 'Login') return true;
  return !isAuthenticated.value || isLoading.value;
});

const handleLogout = () => {
  auth0Logout({ logoutParams: { returnTo: window.location.origin } });
};

const toggleDebug = () => {
  showDebug.value = !showDebug.value;
};


// userName: prefer backend, fallback to auth0 nickname

</script>

<template>
  <div class="app-container">
    <Sidebar 
      v-if="showSidebar" 
      :user-role="userRole" 
      :user-name="userName" 
      @logout="handleLogout"
    />
    <div class="wrapper" :class="{ 'full-width': showFullWidth }">
      <!-- <header class="header">
        <router-link to="/">Home</router-link>
      </header> -->
      <div class="content">
        <router-view />
      </div> 
    </div>
    
    <!-- Debug Overlay -->
    <div v-if="showDebug" class="debug-overlay">
      <div class="debug-header">
        <span>DEBUG INFO</span>
        <button @click="toggleDebug" class="debug-close">×</button>
      </div>
      <div class="debug-content">
        <div class="debug-row">
          <span class="debug-label">Authenticated:</span>
          <span class="debug-value">{{ isAuthenticated ? '✓ Yes' : '✗ No' }}</span>
        </div>
        <div class="debug-row">
          <span class="debug-label">Loading:</span>
          <span class="debug-value">{{ isLoading ? 'Yes' : 'No' }}</span>
        </div>
        <div class="debug-row">
          <span class="debug-label">User Email:</span>
          <span class="debug-value">{{ user?.email || 'N/A' }}</span>
        </div>
        <div class="debug-row">
          <span class="debug-label">User Name:</span>
          <span class="debug-value">{{ user?.name || 'N/A' }}</span>
        </div>
        <div class="debug-row">
          <span class="debug-label">Roles:</span>
          <span class="debug-value">{{ userRole || 'NONE' }}</span>
        </div>
        <div class="debug-row">
          <span class="debug-label">Current Route:</span>
          <span class="debug-value">{{ route.path }}</span>
        </div>
        <div class="debug-row">
          <span class="debug-label">Raw Token Roles:</span>
          <span class="debug-value">{{ user?.[ROLE_KEY] || 'NONE' }}</span>
        </div>
        <div class="debug-row">
          <span class="debug-label">Full User Object:</span>
          <pre class="debug-json">{{ JSON.stringify(user, null, 2) }}</pre>
        </div>
      </div>
    </div>
    
    <!-- Debug Toggle Button -->
    <button 
      v-if="!showDebug" 
      @click="toggleDebug" 
      class="debug-toggle"
    >
      DEBUG
    </button>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}
.app-container {
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: row;
  min-height: 100vh;
  width: 100%;
}
.wrapper {
  margin-top: 0;
  margin-bottom: 0;
  margin-right: auto;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
  width: calc(100% - 240px);
  z-index: 10;
  box-shadow: -4px 0 15px rgba(0, 0, 0, 0.4);

  height: 100vh;
  position: fixed;
  top: 0;
  right: 0;
  overflow-y: auto;
}
.wrapper.full-width {
  margin-left: 0;
  width: 100%;
  box-shadow: none;
}
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 240px;
}
.content {
  padding: 0rem 2rem 2rem 2rem;
  margin: 0 auto;
  width: 100%;
}
.header {
  width: 100%;
  padding: 1rem;
  background: #ffffff;
  display: flex;
  gap: 20px;
}
.navbar a {
  color: white;
  text-decoration: none;
}

/* Debug Overlay Styles */
.debug-toggle {
  position: fixed;
  bottom: 10px;
  right: 10px;
  z-index: 9999;
  background: #9e1b32;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
}

.debug-overlay {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.9);
  color: #0f0;
  padding: 0;
  border-radius: 8px;
  font-family: monospace;
  font-size: 12px;
  max-width: 350px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #333;
  border-radius: 8px 8px 0 0;
  font-weight: bold;
  border-bottom: 1px solid #555;
}

.debug-close {
  background: none;
  border: none;
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.debug-content {
  padding: 15px;
}

.debug-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid #333;
}

.debug-row:last-child {
  border-bottom: none;
}

.debug-label {
  color: #888;
}

.debug-value {
  color: #0f0;
  text-align: right;
  word-break: break-all;
  max-width: 200px;
}

.debug-json {
  color: #0f0;
  font-size: 10px;
  margin: 5px 0;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
