<script setup>
import { computed, onMounted } from 'vue';
import { useAuth0 } from '@auth0/auth0-vue';
import apiService from '../services/api';
import { useStudentStore } from '../stores/studentStore';
import { useProjectsStore } from '../stores/projectsStore';
import StudentAssignmentCard from './StudentAssignmentCard.vue';

const studentStore = useStudentStore();
const projectsStore = useProjectsStore();
const { getAccessTokenSilently } = useAuth0();

const isAssigned = computed(() => studentStore.isAssigned);

onMounted(async () => {
    try {
        const token = await getAccessTokenSilently();
        apiService.setToken(token);
        // Ensure both profile/prefs and projects are loaded
        await Promise.all([
            studentStore.fetchProfileAndPrefs(),
            projectsStore.fetchProjects()
        ]);
    } catch (e) {
        console.warn('StudentAssignment: failed to initialize', e);
    }
});

</script>

<template>
    <div class="assignment-wrapper">
        <h1>Student Assignment</h1>
        <div v-if="isAssigned">
            <StudentAssignmentCard />
        </div>
        <div v-else class="info error">
            <p>No assignment has been made.</p>
        </div>
    </div>
</template>

<style scoped>
.assignment-wrapper {
    margin: 0 auto;
    max-width: var(--max-content-width);
}
</style>