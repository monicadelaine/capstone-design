<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuth0 } from '@auth0/auth0-vue';
import apiService from '../services/api';
import ProfileForm from './ProfileForm.vue';

const router = useRouter();
const route = useRoute();
const { getAccessTokenSilently } = useAuth0();

const loading = ref(true);
const saving = ref(false);
const error = ref(null);
const profileData = ref({});
const profileType = ref(null);

const role = computed(() => {
  return profileType.value || 'student';
});

onMounted(async () => {
  try {
    const token = await getAccessTokenSilently();
    apiService.setToken(token);
    
    const response = await apiService.getProfile();
    
    if (response.type && response.data) {
      profileType.value = response.type;
      profileData.value = response.data;
    } else {
      router.push('/profile/create');
    }
  } catch (err) {
    error.value = 'Failed to load profile. Please try again.';
  } finally {
    loading.value = false;
  }
});

const handleSubmit = async (formData) => {
  saving.value = true;
  error.value = null;
  
  try {
    const token = await getAccessTokenSilently();
    apiService.setToken(token);
    
    await apiService.updateProfile(formData);
    
    const redirectPath = role.value === 'sponsor' ? '/sponsor' : '/student';
    router.push(redirectPath);
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to update profile. Please try again.';
  } finally {
    saving.value = false;
  }
};
</script>

<template>
  <div class="profile-edit-container">
    <h1>Edit Profile</h1>
    
    <div v-if="profileData.email" class="info email">
      <strong>Email:</strong> {{ profileData.email }}
    </div>
    
    <div v-if="error" class="info error email">
      {{ error }}
    </div>
    
    <div v-if="loading" class="loading">
      Loading profile...
    </div>
    
    <ProfileForm
      v-else-if="profileType"
      :role="role"
      :initial-data="profileData"
      :is-edit="true"
      @submit="handleSubmit"
    />
    
    <div v-if="saving" class="saving-overlay">
      Saving changes...
    </div>
  </div>
</template>

<style scoped>
.profile-edit-container {
  max-width: var(--max-content-width);
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  color: var(--text-default);
  margin-bottom: 0.5rem;
}


.info.email {
  margin: 1.5rem 0;
  text-align: center;
}

.email-display strong {
  color: var(--text-default);
  margin-right: 0.5rem;
}

.error-message {
  background: var(--background-negative);
  color: var(--text-negative);
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  text-align: center;
}

.loading, .saving-overlay {
  text-align: center;
  color: var(--text-subtle);
  padding: 2rem;
}

.saving-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
</style>
