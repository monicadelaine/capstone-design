<!-- Student Landing Page -->
<!-- Roles:
        Submit project ranking
        View project descriptions
-->

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth0 } from '@auth0/auth0-vue';
import apiService from '../services/api';
import { useStudentStore } from '../stores/studentStore';
import { useProjectsStore } from '../stores/projectsStore';

const route = useRoute();
const router = useRouter();
const flash = ref(null);

const { getAccessTokenSilently } = useAuth0();

const topPreferences = ref([]);
const loading = ref(true);
const studentStore = useStudentStore();
const projectsStore = useProjectsStore();
const hasRanked = computed(() => studentStore.hasRanked);
const isAssigned = computed(() => studentStore.isAssigned);
const assignedProjectTitle = computed(() => {
  const assignment = studentStore.assignment
  if (!assignment) return null
  const projId = assignment.project && typeof assignment.project === 'object' ? assignment.project.id : assignment.project
  if (!projId) return null
  const proj = (projectsStore.projects || []).find(p => String(p.id) === String(projId))
  return proj ? proj.name : null
})
const deadlineDate = computed(() => {
  const value = studentStore.assignmentDate;
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
})

const days = ref('00');
const hours = ref('00');
const minutes = ref('00');
const seconds = ref('00');

let _timer = null;
const pad = (n) => String(n).padStart(2, '0');

const updateCountdown = () => {
  const deadline = deadlineDate.value;
  if (!deadline) {
    days.value = '00';
    hours.value = '00';
    minutes.value = '00';
    seconds.value = '00';
    return;
  }

  const now = new Date();
  let diff = Math.max(0, deadline - now); // ms
  if (diff <= 0) {
    days.value = '00';
    hours.value = '00';
    minutes.value = '00';
    seconds.value = '00';
    return;
  }

  const d = Math.floor(diff / 86_400_000);
  diff %= 86_400_000;
  const h = Math.floor(diff / 3_600_000);
  diff %= 3_600_000;
  const m = Math.floor(diff / 60_000);
  diff %= 60_000;
  const s = Math.floor(diff / 1000);

  days.value = pad(d);
  hours.value = pad(h);
  minutes.value = pad(m);
  seconds.value = pad(s);
};

onMounted(async () => {
  // before loading, check for flash:
  if (route.query?.flash) {
    flash.value = {
      type: route.query.flash,
      message: route.query.message || (route.query.flash === 'success' ? 'Saved successfully.' : 'Operation result.')
    };
    // remove query parameters without navigating
    router.replace({ path: route.path, query: {} });
  }

  // update countdown information
  updateCountdown();
  _timer = setInterval(updateCountdown, 1000);

  try {
    const token = await getAccessTokenSilently();
    apiService.setToken(token);

    await Promise.all([
      projectsStore.fetchProjects(),
      studentStore.fetchProfileAndPrefs()
    ]);

    const studentPrefs = studentStore.preferences || [];
    if (!studentPrefs.length) {
      loading.value = false;
      return;
    }

    // build project map from projects store
    const projectById = Object.fromEntries((projectsStore.projects || []).map(p => [String(p.id), p]));

    studentPrefs.sort((a, b) => (a.rank || 999) - (b.rank || 999));
    topPreferences.value = studentPrefs.slice(0, 5).map(pref => {
      const projId = pref.project && typeof pref.project === 'object' ? pref.project.id : pref.project;
      const proj = projectById[String(projId)];
      return {
        id: projId,
        name: proj?.name ?? (pref.project?.name ?? 'Unknown'),
        description: proj?.description ?? ''
      };
    });
  } catch (e) {
    console.error('Failed to load top preferences', e);
  } finally {
    loading.value = false;
  }
});
onUnmounted(() => {
  if (_timer) clearInterval(_timer);
});
</script>

<template>
<div class="outside-wrapper">
  <h1>Student Dashboard</h1>
  <div class="inside-wrapper">
    <div v-if="flash" :class="['info', flash.type === 'success' ? 'success' : 'error']">
        <strong v-if="flash.type === 'success'">Success</strong>
        <strong v-else>Notice</strong>
        <p>{{ flash.message }}</p>
    </div>
    <div class="card">
        <h2>Submission Deadline Countdown</h2>
        <hr />
        <div v-if="deadlineDate" class="timer">
          <div class="time-segment">
            <div class="time-value">{{ days }}</div>
            <div class="time-label">Days</div>
          </div>
          <div class="time-separator">:</div>
          <div class="time-segment">
            <div class="time-value">{{ hours }}</div>
            <div class="time-label">Hours</div>
          </div>
          <div class="time-separator">:</div>
          <div class="time-segment">
            <div class="time-value">{{ minutes }}</div>
            <div class="time-label">Minutes</div>
          </div>
          <div class="time-separator">:</div>
          <div class="time-segment">
            <div class="time-value">{{ seconds }}</div>
            <div class="time-label">Seconds</div>
          </div>
        </div>
        <span v-else>No submission deadline set.</span>
    </div>
    <div class="card">
        <h2>Top 5 Rankings</h2>
        <hr />
        <div v-if="loading"><p>Loading...</p></div>
        <div v-else-if="hasRanked && topPreferences.length">
            <ul class="preference-list">
                <li v-for="p in topPreferences" :key="p.id">
                <p>{{ p.name }}</p>
                </li>
            </ul>
            <span v-if="!studentStore.isDeadlinePast"><router-link class="redirect" to="/student/submit">Edit your preferences →</router-link></span>
        </div>
        <div v-else>
            <span>You don't have any rankings yet. <router-link class="redirect" to="/student/submit">Submit rankings now →</router-link></span>
        </div>
    </div>
    
    <div class="card">
      <h2>Project Assignment</h2>
      <hr />
      <div v-if="isAssigned">
        <p>Assigned project: <strong>{{ assignedProjectTitle || 'Assigned project' }}</strong></p>
        <span><router-link class="redirect" to="/student/assignment">View assignment →</router-link></span>
      </div>
      <div v-else>
        <span>{{ studentStore.isDeadlinePast ? 'No assignment has been made yet.' : 'Due date has not passed yet.' }}</span>
      </div>
    </div>
  </div>
</div>
</template>

<style scoped>
hr {
    margin: 0.5rem 0 1rem 0;
    /* display: none; */
}
h2 {
    margin-top: 0rem;
    margin-bottom: 0.5rem;
    font-size: 2rem;
}
.redirect {
    color: var(--text-link)
}
.outside-wrapper {
  margin: 0 auto;
  max-width: var(--max-content-width);
  display: flex;
  flex-direction: column;
}
.inside-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}
button {
    width: 100%;
}
strong {
    font-weight: 800;
    font-size: 1.1rem;
    line-height: 2rem;
}

.countdown-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
}

.time-segment {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 20%;
}

.time-value {
  font-family: "Noto Sans Mono";
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
  color: var(--text-default);
}

.time-label {
  margin-top: 0.35rem;
  font-size: 0.875rem;
  color: var(--text-subtle);
  text-transform: uppercase;
}

.time-separator {
  font-size: 2.2rem;
  font-weight: 700;
  color: var(--text-accent);
  display: flex;
  align-items: center;
}

@media (max-width: 720px) {
  .time-value { font-size: 1.6rem; }
  .time-segment { min-width: 48px; }
  .time-separator { font-size: 1.6rem; }
}
</style>