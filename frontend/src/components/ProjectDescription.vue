<script setup>
    import { computed } from 'vue';
    import { useRoute } from 'vue-router';

    const route = useRoute();

    const project = computed(() => window.history.state.project || {});

    // Function to turn that ISO string into something readable
    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        
        // Using Intl.DateTimeFormat
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    };
</script>

<template>
    <div v-if="project.id" class="description-wrapper">
        <h1> {{ project.name }}</h1>
        <p> Created on {{ formatDate(project.created_at) }}</p>
        <!-- TODO: Parse project.sponsor into a name, not the ID -->
        <p>Sponsor: {{ project.sponsor }}</p>
        <!-- TODO: Parse project.status into a readable string, not its shortened version -->
        <p>Status: {{ project.status }}</p>
        <p v-if="project.website">Website: <a :href="project.website" target="_blank" rel="noopener noreferrer">{{ project.website }}</a></p>
        <hr />
        <h2>Project Description</h2>
        <p> {{ project.description }}</p>
        <router-link to="/projects">Back to List</router-link>
    </div>
    <div v-else>
        <p>No project data found. <router-link to="/projects">Back to List</router-link></p>
    </div>
</template>

<style scoped>
.description-wrapper {
    text-align: left;
}
</style>