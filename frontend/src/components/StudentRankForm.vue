<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth0 } from '@auth0/auth0-vue';
import apiService from '../services/api';
import { useProjectsStore } from '../stores/projectsStore';
import { useStudentStore } from '../stores/studentStore';
import ConfirmationModal from './ConfirmationModal.vue';
import { FormKit } from '@formkit/vue';

const { getAccessTokenSilently } = useAuth0()

const router = useRouter();

const projectsStore = useProjectsStore();
const studentStore = useStudentStore();
const isDeadlinePast = computed(() => studentStore.isDeadlinePast);

const showConfirm = ref(false);

const hasRanked = computed(() => studentStore.hasRanked);
const projects = ref([]);
const loading = ref(true);
const error = ref(null);
const isSubmitting = ref(false);
const description = ref('');

const studentProfile = ref(null);

const existingPrefProjectIds = ref(new Set());

const fetchProfileAndProjects = async () => {
  try {
    loading.value = true;
    const token = await getAccessTokenSilently();
    apiService.setToken(token);

    // hydrate student store first so assignment_date/deadline is available
    try {
      await studentStore.fetchProfileAndPrefs();
    } catch (e) {
      console.warn('Failed to refresh student store before ranking form init', e);
    }

    // load projects via projects store + profile
    await projectsStore.fetchProjects();
    const projectsData = projectsStore.projects || [];
    projects.value = projectsData.map(p => ({ ...p, selection: null }));
    const profileRes = await apiService.getProfile();
    studentProfile.value = profileRes?.data ?? profileRes;
    description.value = studentProfile.value?.description ?? '';

    // if we have a student id, fetch preferences and apply them to the projects
    const studentId = studentProfile.value?.id;
    if (!studentId) {
      existingPrefProjectIds.value = new Set();
      // ensure global store is cleared
      studentStore.setPreferences([])
      return;
    }

    const prefsRes = await apiService.client.get('/preferences/');
    const prefs = Array.isArray(prefsRes.data) ? prefsRes.data : [];

    // only keep this student's preferences
    const studentPrefs = prefs.filter(pref => {
      let prefStudent = pref.student;
      if (prefStudent && typeof prefStudent === 'object') prefStudent = prefStudent.id;
      return String(prefStudent) === String(studentId);
    });

    // update global store so other components see the current state
    studentStore.setPreferences(studentPrefs);

    const rankToSelection = { 1: 'high', 2: 'medium', 3: 'low' };

    // apply existing preferences to the projects array
    studentPrefs.forEach(pref => {
      const prefProjectId = pref.project && typeof pref.project === 'object'
        ? pref.project.id
        : pref.project;

      const project = projects.value.find(p => String(p.id) === String(prefProjectId));
      if (project) {
        project.selection = rankToSelection[pref.rank] ?? null;
      }
    });

    // track which project IDs already have preferences for this student
    existingPrefProjectIds.value = new Set(
      studentPrefs.map(pref => {
        const proj = pref.project && typeof pref.project === 'object' ? pref.project.id : pref.project;
        return String(proj);
      })
    );
  } catch (err) {
    error.value = "Error: Could not obtain project data.";
    console.error(err);
  } finally {
    loading.value = false;
  }
}

onMounted(fetchProfileAndProjects);

const togglePreference = (index, rank) => {
  if (isDeadlinePast.value) return;
    if (projects.value[index].selection === rank) {
        projects.value[index].selection = null; // Deselect if clicking the same button
    } else {
        projects.value[index].selection = rank; // Switch to new selection
    }
};

// Calculate counts for validation
const counts = computed(() => {
    return {
        high: projects.value.filter(p => p.selection === 'high').length,
        medium: projects.value.filter(p => p.selection === 'medium').length,
        low: projects.value.filter(p => p.selection === 'low').length,
    };
});

const isFormValid = computed(() => {
    return counts.value.high === 5 && 
            counts.value.medium === 5 && 
            counts.value.low === 5;
});

// Map UI strings to IntegerChoices from model
const rankMap = {
    high: 1,
    medium: 2,
    low: 3
}

// Compute payload to match preference model fields
const rankingPayload = computed(() => {
    if (!studentProfile.value) return [];

    return projects.value
        .filter(p => p.selection !== null)
        .map(p => ({
            // Matches the "1-2" format: studentID-projectID
            id: `${studentProfile.value.id}-${p.id}`, 
            student: studentProfile.value.id,
            project: p.id,
            rank: rankMap[p.selection]
        }));
});

const openConfirm = () => { showConfirm.value = true; };

const onConfirm = async () => {
  showConfirm.value = false;
  await submitRankings();
}


const submitRankings = async () => {
  if (isDeadlinePast.value) return;
  if (!isFormValid.value) return;
  isSubmitting.value = true;
  try {
    const token = await getAccessTokenSilently();
    apiService.setToken(token);

    const payload = rankingPayload.value || [];
    const studentId = studentProfile.value?.id;
    const currentProjIds = payload.map(i => String(i.project));

    // Ensure profile description is saved
    try {
      if (studentProfile.value && studentProfile.value.id) {
        // update existing profile (PUT)
        await apiService.updateProfile({ ...studentProfile.value, description: description.value });
      } else {
        // create profile if none exists
        const created = await apiService.createProfile({ description: description.value });
        studentProfile.value = created;
      }
    } catch (profileErr) {
      console.warn('Profile save failed, continuing with preferences:', profileErr.response?.data ?? profileErr);
      // optionally: surface error and abort if you prefer
    }
    // if update/create succeeded, refresh local copy
    await fetchProfileAndProjects();

    // Determine deletes: previously-existing project IDs that are no longer present
    const toDeleteProjIds = [...existingPrefProjectIds.value].filter(id => !currentProjIds.includes(id));

    // Issue deletes first (ignore 404s) and remove them from the local set
    if (toDeleteProjIds.length && studentId) {
      await Promise.all(toDeleteProjIds.map(async projId => {
        const prefId = `${studentId}-${projId}`;
        try {
          await apiService.client.delete(`/preferences/${prefId}/`);
        } catch (e) {
          if (e.response?.status !== 404) throw e;
        } finally {
          existingPrefProjectIds.value.delete(projId);
        }
      }));
    }

    // Partition payload into updates (existing) and creates (new)
    const toUpdate = [];
    const toCreate = [];
    for (const item of payload) {
      const projId = String(item.project);
      if (existingPrefProjectIds.value.has(projId)) toUpdate.push(item);
      else toCreate.push(item);
    }

    // If user had no prefs at all, POST everything (preserves original behavior)
    if (!hasRanked) {
      for (const item of toCreate) {
        await apiService.client.post('/preferences/', item);
        existingPrefProjectIds.value.add(String(item.project));
      }
      // global store will be refreshed below after operations complete
    } else {
      // Update existing prefs (PATCH) in bulk if any
      if (toUpdate.length) {
        try {
          await apiService.client.patch('/preferences/', toUpdate);
        } catch (patchErr) {
          console.warn('Bulk PATCH failed, continuing to create:', patchErr.response?.data ?? patchErr);
          // continue to creation loop
        }
      }

      // Create new prefs one-by-one for robustness; fallback to PATCH on duplicate
      for (const item of toCreate) {
        try {
          await apiService.client.post('/preferences/', item);
          existingPrefProjectIds.value.add(String(item.project));
        } catch (e) {
          const status = e.response?.status;
          if (status === 400 || status === 409 || status === 400) {
            // Try patching this item as a fallback
            try {
              await apiService.client.patch('/preferences/', item);
              existingPrefProjectIds.value.add(String(item.project));
            } catch (innerErr) {
              throw innerErr;
            }
          } else {
            throw e;
          }
        }
      }
    }

    // Refresh local view so UI and tracking sets update
    await fetchProfileAndProjects();
    try {
      // update global student store so sidebar/landing reflect the change immediately
      await studentStore.fetchProfileAndPrefs();
    } catch (e) {
      console.warn('Failed to refresh global student store', e);
    }

    router.push({
      path: '/student',
      query: { flash: 'success', message: 'Your preferences have been saved.' }
    });
  } catch (err) {
    console.error('Submission Error:', err.response?.data ?? err);
    router.push({
      path: '/student',
      query: { flash: 'failure', message: `Error: Preferences may not have been saved.` }
    });
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
<div class="ranking-container">
    <h1>Project Preference Rankings</h1>

    <div v-if="isDeadlinePast" class="info error">
      <p>The ranking deadline has passed. Submissions are closed.</p>
    </div>

    <div class="card">
    <p v-if="isDeadlinePast">Select exactly 5 projects for each priority level.</p>

    <div v-if="loading" class="status-msg">Loading projects...</div>
    <div v-else-if="error" class="status-msg error">{{ error }}</div>

    <div v-else>
      <table class="ranking-grid">
        <thead>
          <tr>
            <th style="text-align: left;">Project Name</th>
            <th>High</th>
            <th>Medium</th>
            <th>Low</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(project, index) in projects" :key="project.id">
            <td class="project-name">{{ project.name }}</td>
            
            <td v-for="rank in ['high', 'medium', 'low']" :key="rank">
              <button 
                type="button"
                :class="['rank-btn', rank, { active: project.selection === rank }]"
                :disabled="isDeadlinePast"
                @click="togglePreference(index, rank)"
              >
                <!-- {{ rank.charAt(0).toUpperCase() }} -->
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <footer class="submission-area">
        <div class="counters">
          <div :class="['counter-box', { complete: counts.high === 5 }]">
            <span>High {{ counts.high }}/5</span>
          </div>
          <div :class="['counter-box', { complete: counts.medium === 5 }]">
            <span>Med {{ counts.medium }}/5</span>
          </div>
          <div :class="['counter-box', { complete: counts.low === 5 }]">
            <span>Low {{ counts.low }}/5</span>
          </div>
        </div>

        <div class="comment-area">
          <p>Provide any additional information. We will not be able to accommodate all requests.</p>
          <FormKit
            type="textarea"
            name="comment"
            v-model="description"
            :disabled="isDeadlinePast"
            validation="length:0,2000"
            />
        </div>

        <button 
          class="submit-button" 
          :disabled="!isFormValid || isSubmitting || isDeadlinePast"
          @click="openConfirm"
        >
          {{ isSubmitting ? 'Saving...' : (hasRanked ? 'Update Project Rankings' : 'Submit Project Rankings') }}
        </button>
        <ConfirmationModal :show="showConfirm" title="Submit rankings?" message="These changes can be updated before the deadline." @confirm="onConfirm" @cancel="() => showConfirm = false" />
        
      </footer>
    </div>
    </div>
  </div>
</template>

<style scoped>
.ranking-container {
  max-width: var(--max-content-width);
  margin: 0 auto;
  /* font-family: sans-serif; */
}

.ranking-container .info {
  margin-bottom: 1.5rem;
}

.ranking-grid {
  width: 100%;
  border-collapse: collapse;
}

.ranking-grid th, .ranking-grid td {
  padding: 15px;
  border-bottom: 1px solid var(--border-subtle);
  text-align: center;
}

.project-name {
  text-align: left !important;
  font-weight: 600;
  width: 60%;
}

.rank-btn {
  width: 25px;
  height: 25px;
  border-radius: 50%;
  padding: 0;
  border: 2px solid #ddd;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.rank-btn:disabled {
  cursor: not-allowed;
}

.rank-btn.high.active { background: var(--accent-primary); border-color: var(--accent-dark); color: white; }
.rank-btn.medium.active { background: var(--accent-primary); border-color: var(--accent-dark); color: white; }
.rank-btn.low.active { background: var(--accent-primary); border-color: var(--accent-dark); color: white; }

.rank-btn:hover:not(.active) {
  border-color: #999;
}

/* FOOTER & COUNTERS */
.submission-area {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.counters {
  width: 100%;
  display: flex;
  gap: 20px;
}

.counter-box {
  width: 100%;
  padding: 10px 20px;
  border-radius: 8px;
  color: var(--text-negative);
  background: var(--background-negative);
  border: 1px solid var(--accent-negative);
  text-align: center;
}

.counter-box.complete {
  border-color: var(--accent-positive);
  background: var(--background-positive);
  color: var(--text-positive);
}

.comment-area {
  width: 100%;
}

.submit-button {
  padding: 1rem 2rem;
  width: 100%;
  color: white;
  cursor: pointer;
}

.submit-button:disabled {
  background: var(--accent-neutral);
  cursor: not-allowed;
}

.helper-text {
  color: #dc2626;
  font-size: 0.9rem;
}

.status-msg.error { color: #dc2626; font-weight: bold; }
</style>