<script setup>
import SponsorProjectCard from './SponsorProjectCard.vue';
import apiService from '../services/api';
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth0 } from '@auth0/auth0-vue';

const { getAccessTokenSilently } = useAuth0();
const route = useRoute();
const router = useRouter();

const currentSponsorId = ref(null);
const projects = ref([]);
const loading = ref(true);
const error = ref(null);
const flash = ref(null);

onMounted(async () => {
    if (route.query?.flash) {
        flash.value = {
            type: route.query.flash,
            message: route.query.message || (route.query.flash === 'success' ? 'Saved successfully.' : 'Operation result.')
        };
        router.replace({ path: route.path, query: {} });
    }

    try {
        const token = await getAccessTokenSilently();
        apiService.setToken(token);

        const profileResponse = await apiService.getProfile();
        currentSponsorId.value = profileResponse?.data?.id ?? null;

        if (!currentSponsorId.value) {
            projects.value = [];
            return;
        }

        const sponsorProjects = await apiService.getProjectsBySponsor(currentSponsorId.value);
        projects.value = Array.isArray(sponsorProjects) ? sponsorProjects : [];
    } catch (err) {
        console.error('Failed to fetch sponsor projects:', err);
        error.value = err;
        projects.value = [];
    } finally {
        loading.value = false;
    }
});
</script>

<template>
    <div class="inside-wrapper">
        <h1>Sponsor Dashboard</h1>
        <div v-if="flash" :class="['info', flash.type === 'success' ? 'success' : 'error']">
            <strong v-if="flash.type === 'success'">Success</strong>
            <strong v-else>Notice</strong>
            <p>{{ flash.message }}</p>
        </div>
        <h2>Projects</h2>
        <div v-if="loading" class="card"><p>Loading projects...</p></div>
        <div v-else-if="error" class="info error">Unable to load projects.</div>

        <div v-else-if="projects.length" class="cards-list">
            <div v-for="project in projects" :key="project.id" class="card-item">
                <SponsorProjectCard :project="project" />
            </div>
    </div>
        <div v-else class="card empty">
            <p>You have no projects submitted yet.</p>
            <p><router-link to="sponsor/submit">Submit a Project →</router-link></p>
        </div>
    </div>
</template>

<style scoped>
h2 {
    margin: 0;
}
.card {
    margin-top: 1rem;
}
.inside-wrapper {
    margin: 0 auto;
    max-width: var(--max-content-width);
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.cards-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    margin-bottom: 2rem;
}

button {
    width: 100%;
}
</style>