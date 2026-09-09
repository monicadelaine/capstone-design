<script setup>
import { FormKit } from '@formkit/vue';
import apiService from '../services/api';
import { ref, onMounted, watch } from 'vue';
import { useAuth0 } from '@auth0/auth0-vue';
import { useRouter } from 'vue-router';
import ConfirmationModal from './ConfirmationModal.vue';

const { getAccessTokenSilently } = useAuth0()
const router = useRouter();

const projectOptions = ref([]);
const sponsorId = ref(null);
const selectedSemesterId = ref(null);
const semesters = ref([]);
const sponsorProjects = ref([]);
const selectedProjectId = ref(null);
const showConfirm = ref(false);
const pendingSubmission = ref(null);

onMounted(async () => {
  try {
    const token = await getAccessTokenSilently();
    apiService.setToken(token);

    const profile = await apiService.getProfile();
    sponsorId.value = profile?.data?.id ?? null;

    const currentSemester = await apiService.getCurrentSemester();
    const allSemesters = await apiService.getSemesters();
    semesters.value = allSemesters.map(s => ({
      label: `${s.semester} ${s.year}`,
      value: s.id
    }));
    selectedSemesterId.value = currentSemester?.id ?? allSemesters?.[0]?.id ?? null;

    if (sponsorId.value && selectedSemesterId.value) {
      sponsorProjects.value = await apiService.getProjectsBySponsor(sponsorId.value, selectedSemesterId.value);
      projectOptions.value = sponsorProjects.value.map(project => ({
        label: project.name,
        value: project.id
      }));
    }
  } catch (error) {
    console.error("Error loading projects:", error);
  }
});

watch(selectedSemesterId, async (newId) => {
  if (!newId || !sponsorId.value) return;

  sponsorProjects.value = await apiService.getProjectsBySponsor(
    sponsorId.value,
    newId
  );

  projectOptions.value = sponsorProjects.value.map(project => ({
    label: project.name,
    value: project.id
  }));
});

const openConfirm = (data) => {
  pendingSubmission.value = data;
  showConfirm.value = true;
};

const cancelConfirm = () => {
  showConfirm.value = false;
  pendingSubmission.value = null;
};

async function handleSubmission() {
  const data = pendingSubmission.value;

  if (!data) {
    cancelConfirm();
    return;
  }

  showConfirm.value = false;
  pendingSubmission.value = null;

  try {
    const token = await getAccessTokenSilently();
    apiService.setToken(token);
    
    const feedbackPayload = {
      text: data.sponsor_info.feedback,
      sponsor: sponsorId.value,
      project: data.project,
      semester: selectedSemesterId.value
    }

    await apiService.createFeedback(feedbackPayload);

    router.push({
      path: '/sponsor',
      query: { flash: 'success', message: 'Your feedback has been submitted.' }
    });

  } catch (error) {
    console.error("Submission failed:", error)
    const errorMessage = error?.response?.data
      ? JSON.stringify(error.response.data)
      : (error?.message || "Submission failed.");

    if (error instanceof Error) {
      alert(errorMessage);
    } else {
      alert("Submission failed.");
    }
  }
}

</script>

<template>
    <div class="container">
    <h1>Feedback Submission</h1>
    <div class="card">
    <div class="form-container">
        <FormKit 
        type="form" 
        id="sponsor-form"
        submit-label="Submit Sponsor Feedback"
        @submit="openConfirm"
        >

        <!-- Semester Selection Dropdown -->
         <FormKit
            type="select"
            name="semester"
            label="Select Semester"
            v-model="selectedSemesterId"
            :options="semesters"
         />
         <hr />

        <!-- Project Selection -->
        <FormKit
            type="radio"
            name="project"
            label="Select a Project"
            v-model="selectedProjectId"
            :options="projectOptions"
            validation="required"
            />

        <FormKit type="group" name="sponsor_info">
            <FormKit
            type="textarea"
            name="feedback"
            label="Feedback"
            validation="required"
            />
        </FormKit>
        </FormKit>

        <ConfirmationModal
          :show="showConfirm"
          title="Submit sponsor feedback?"
          message="Confirm that you want to submit this feedback."
          @confirm="handleSubmission"
          @cancel="cancelConfirm"
        />
    </div>
    </div>
    </div>
</template>

<style scoped>
hr {
  margin: 2rem 0;
}

/* override formkit radio buttons */
:deep(.formkit-fieldset) {
  border: none !important;
  padding: 0;
  margin: 0;
}
:deep(.formkit-legend) {
  display: block;
  margin-bottom: 0.5rem;
  padding: 0;
  font-size: 1rem;
}
:deep(.formkit-options){
  border: var(--fk-border);
  border-radius: var(--fk-border-radius);
  padding: 1rem !important;
}

.container {
  text-align: left;
  max-width: var(--max-content-width);
  margin: 0 auto;
}

.card {
  padding: 1.5rem;
}

.form-container :deep(.formkit-outer) {
  margin-bottom: 1rem;
}

</style>