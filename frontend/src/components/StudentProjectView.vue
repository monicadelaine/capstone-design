<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth0 } from '@auth0/auth0-vue';
import StudentProjectCard from './StudentProjectCard.vue';
import ProjectDetailsSidebar from './ProjectDetailsSidebar.vue';
import { useProjectsStore } from '../stores/projectsStore';
import apiService from '../services/api';

const router = useRouter();
const { getAccessTokenSilently } = useAuth0();
const projectsStore = useProjectsStore();

// Reactive State
const posts = computed(() => projectsStore.projects || []);
const loading = computed(() => projectsStore.loading);
const error = computed(() => projectsStore.error);
const selectedProject = ref(null); // For sidebar details

const sponsors = ref(new Map())

// Fetch Logic
const fetchData = async () => {
  try {
    loading.value = true; // Reset loading state if called again
    const token = await getAccessTokenSilently();
    apiService.setToken(token);
    const [projectsRes, sponsorsRes] = await Promise.all([
      apiService.client.get('/projects/?format=json'),
      apiService.client.get('/sponsors/?format=json')
    ]);
    
    // Map sponsor ID to sponsor object
    sponsorsRes.data.forEach(sponsor => {
      sponsors.value.set(sponsor.id, sponsor);
    })

    posts.value = projectsRes.data; 
  } catch (err) {
    error.value = err;
    console.error("Fetch Error:", err);
  } finally {
    loading.value = false;
  }
};

const getSponsorDisplay = (project) => {
  const sponsor = sponsors.value.get(project?.sponsor);
  if (!sponsor) return 'Unknown';
  return sponsor.organization || `${sponsor.first_name || ''} ${sponsor.last_name || ''}`.trim();
}

// Toggle sidebar
const openDetails = (project) => {
  selectedProject.value = project;
}

const closeDetails = () => {
  selectedProject.value = null;
}

onMounted(() => {
  (async () => {
    try {
      const token = await getAccessTokenSilently();
      apiService.setToken(token);
      const [, sponsorsResp] = await Promise.all([
        projectsStore.fetchProjects(),
        apiService.client.get('/sponsors/')
      ]);
      (sponsorsResp.data || []).forEach((sponsor) => {
        sponsors.value.set(sponsor.id, sponsor);
      });
    } catch (err) {
      console.error('StudentProjectView initialization failed', err);
    }
  })();
});
</script>

<template>
  <div>

    <div class="gallery-layout">

      <div class="grid-container" :class="{ 'pane-open': selectedProject}">
        <h1>Project Gallery</h1>
        
        <div v-if="loading" class="status-msg">Fetching projects...</div>
        <div v-else-if="error" class="status-msg error">Error: {{ error.message }}</div>
        <div v-else class="project-grid">
          <StudentProjectCard 
            v-for="project in posts" 
            :key="project.id" 
            :project="project"
            :sponsorDisplay="getSponsorDisplay(project)"
            @click="openDetails(project)"
          />
        </div>
      </div>

      <transition name="slide-fade">
        <aside v-if="selectedProject" class="card-details">
          <ProjectDetailsSidebar
            :project="selectedProject"
            :sponsorDisplay="getSponsorDisplay(selectedProject)"
            @close="closeDetails"
          />
        </aside>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.gallery-layout {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
  min-height: 80vh;
}

.grid-container {
  flex: 1; /* Takes all space when pane is closed */
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

/* When pane is open, force grid to fewer cols */
.grid-container.pane-open .project-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

.card-details {
  width: 450px;
  /* padding: 2rem; */
  border-radius: 16px;
  height: calc(100vh - 4rem);
  background: var(--background-element);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 2rem;
  overflow-y: scroll;
}

/* Smooth transition for opening the pane */
.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s ease;
}
.slide-fade-enter-from, .slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}

.status-msg {
  text-align: center;
  padding: 3rem;
  font-size: 1.2rem;
  color: var(--text-muted);
}
</style>