<script setup>
import Sidebar from './components/Sidebar.vue';
import { useAuth0 } from '@auth0/auth0-vue';
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import apiService from './services/api';

const { isAuthenticated, isLoading, user, logout: auth0Logout } = useAuth0();
const route = useRoute();

const ROLE_KEY = 'https://backend-api-capstone/roles';

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


</style>
