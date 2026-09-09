<script setup>
defineProps({
  project: { type: Object, default: null },
  sponsorDisplay: { type: String, default: 'Unknown' }
});
defineEmits(['close']);
</script>

<template>
  <aside class="details-inner">
    <header class="sidebar-header">
      <button class="close-btn" @click="$emit('close')">✕</button>
      <div class="sponsor-brand">
        <h2>{{ sponsorDisplay }}</h2>
      </div>
      <hr />
    </header>

    <div class="sidebar-body">
      <!-- Hide status tag for now -->
      <!-- <span class="status-tag">{{ project.status }}</span> -->
      <h1 class="project-name">{{ project.name }}</h1>
      
      <section class="info-section">
        <h3>Description</h3>
        <p>{{ project.description }}</p>
      </section>

      <section class="info-section">
        <h3>Details</h3>
        <ul class="details-list">
          <li><strong>Website:</strong> <a :href="project.website" target="_blank">{{ project.website }}</a></li>
          <li><strong>Created:</strong> {{ project.created_at ? new Date(project.created_at).toLocaleDateString() : 'N/A' }}</li>
        </ul>
      </section>
    </div>
  </aside>
</template>

<style scoped>

.details-inner {
  display: flex;
  flex-direction: column;
  height: 100%; /* Fill the .details-pane parent */
  position: relative;
}

h2 {
    margin: 2rem 0 0 0 0;
}

hr {
  color: var(--border-subtle);
}

li {
  font-size: 1.1rem;
}

.sidebar-header {
  padding: 1rem 2rem;
  /* border-bottom: 1px solid var(--border-subtle); */
}

.close-btn {
  color: var(--text-default);
  background: none; border: none; font-size: 1.5rem;
  cursor: pointer; position: absolute; top: 1rem; right: 1rem;
}

.sidebar-body {
  padding: 0 2rem 2rem 2rem;
  overflow-y: auto;
  flex-grow: 1;
}

.info-section h3 {
  font-size: 0.9rem;
  text-transform: uppercase;
  color: var(--text-subtle);
  margin-top: 2rem;
}

.project-name { margin: 1rem 0; font-size: 2rem; line-height: 1.2; }
</style>