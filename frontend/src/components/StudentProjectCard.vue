<script setup>
defineProps({
  project: {
      type: Object,
      required: true
  },
  sponsorDisplay: {
    type: String,
    required: true
  }
});

// Helper to keep descriptions from breaking the card height
const truncate = (text) => {
  return text && text.length > 120 ? text.substring(0, 120) + '...' : text;
};

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString();
};
</script>

<template>
    <div class="card">
        <div class="card-header">
            <div class="sponsor-info">
                <div class="sponsor-logo">{{ sponsorDisplay.charAt(0).toUpperCase() }}</div> 
                <span class="sponsor-name">{{ sponsorDisplay }}</span>
            </div>

            <!-- hide status-badge for now, not necessary -->
            <!-- <span class="status-badge" :class="project.status?.toLowerCase()">
                {{ project.status }}
            </span> -->
        </div>

        <div class="card-body">
            <h3 class="project-title">{{ project.name }}</h3>
            <p class="project-description">{{ truncate(project.description) }}</p>
        </div>
        
    </div>
</template>

<style scoped>
.card {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sponsor-logo {
  width: 32px;
  height: 32px;
  background: var(--accent-primary);
  color: white;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-weight: bold;
}
.sponsor-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sponsor-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.project-title {
  color: var(--text-default);
  margin: 0;
  font-size: 1.5rem;
  line-height: 2rem;
}

.project-description {
  color: var(--text-subtle);
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0.5rem 0;
}

.status-badge {
  font-size: 0.75rem;
  padding: 4px 12px;
  border-radius: 99px;
  background: #eee;
  text-transform: uppercase;
  font-weight: 600;
}

.status-badge.active { background: #e6f4ea; color: #1e7e34; }

.card-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid var(--border-subtle);
}

.btn-text {
  background: none;
  border: none;
  padding: 0;
  color: var(--accent-primary);
  font-weight: 600;
  cursor: pointer;
}
</style>