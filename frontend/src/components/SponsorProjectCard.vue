<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
    project: {
        type: Object,
        required: true,
    },
});

const showDetails = ref(false);

const previewDescription = computed(() => {
    const description = props.project.description || 'No description provided.';
    if (description.length <= 140) return description;
    return `${description.slice(0, 140)}...`;
});

const statusPillClass = computed(() => {
    const status = String(props.project.status || '').toLowerCase();

    if (status === 'cancelled') {
        return 'status-cancelled';
    }

    if (status === 'complete') {
        return 'status-completed';
    }

    return 'status-active';
});

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return 'N/A';
    return date.toLocaleDateString();
}

</script>

<template>
    <article class="card">
        <header class="card-header">
            <h2 class="project-name">{{ props.project.name || 'Untitled Project' }}</h2>
            <span :class="['status-pill', statusPillClass]">{{ props.project.status || 'Unknown' }}</span>
        </header>

        <!-- <p class="description">{{ previewDescription }}</p> -->

        <div class="quick-meta">
            <span><strong>Created:</strong> {{ formatDate(props.project.created_at) }}</span>
        </div>

        <dl v-if="showDetails" class="details">
            <div>
                <dt>Description</dt>
                <dd>{{ props.project.description || 'No description provided.' }}</dd>
            </div>
            <div>
                <dt>Availability</dt>
                <dd>{{ props.project.sponsor_availability || 'Not provided' }}</dd>
            </div>
            <div>
                <dt>Website</dt>
                <dd>
                    <a
                        v-if="props.project.website"
                        :href="props.project.website"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        {{ props.project.website }}
                    </a>
                    <div v-else>Not provided</div>
                </dd>
            </div>
        </dl>

        <button
            class="toggle-btn"
            type="button"
            @click="showDetails = !showDetails"
            :aria-expanded="showDetails"
        >
            {{ showDetails ? 'Hide details' : 'View details' }}
        </button>
    </article>
</template>

<style scoped>

h2 {
    margin-top: 0rem;
    margin-bottom: 0.5rem;
    font-size: 2rem;
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    gap: 0.75rem;
}

.status-pill {
    font-size: 0.9rem;
    border-radius: 999px;
    padding: 0.2rem 0.6rem;
    white-space: nowrap;
}

.status-active {
    background: var(--background-info);
    color: var(--text-info);
    border: 1px solid var(--accent-info);
}

.status-cancelled {
    background: var(--background-negative);
    color: var(--text-negative);
    border: 1px solid var(--accent-negative);
}

.status-completed {
    background: var(--background-positive);
    color: var(--text-positive);
    border: 1px solid var(--accent-positive);
}

.description {
    margin: 0 0 0.7rem 0;
}

.quick-meta {
    font-size: 0.9rem;
}

.toggle-btn {
    margin-top: 0.75rem;
    background: transparent;
    color: var(--text-link);
    padding: 0;
    cursor: pointer;
    font-weight: 600;
}

.toggle-btn:hover {
    color: var(--text-link-hover);
}

.details {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}


.details dt {
    font-size: 0.8rem;
    text-transform: uppercase;
    color: var(--text-subtle);
    margin-bottom: 0.15rem;
}

.details dd {
    margin: 0;
    word-break: break-word;
}

</style>