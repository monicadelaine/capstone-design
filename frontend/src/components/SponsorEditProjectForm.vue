<script setup>
import { useAuth0 } from '@auth0/auth0-vue';
import { FormKit } from '@formkit/vue';
import { onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import ConfirmationModal from './ConfirmationModal.vue';
import apiService from '../services/api';

const { getAccessTokenSilently } = useAuth0();
const router = useRouter();
const sponsorId = ref(null);
const sponsorProjects = ref([]);
const projectOptions = ref([]);
const loading = ref(true);
const showConfirm = ref(false);
const pendingSubmission = ref(null);
const formData = ref({
  project_details: {
    name: '',
    website: '',
    description: '',
    availability: ''
  }
})

onMounted(async () => {
  try {
    const token = await getAccessTokenSilently();
    apiService.setToken(token);
    const profileResponse = await apiService.getProfile();
    sponsorId.value = profileResponse.data.id ?? null;

    if (!sponsorId.value) {
      sponsorProjects.value = [];
      return;
    }

    if (sponsorId.value) {
      sponsorProjects.value = await apiService.getProjectsBySponsor(sponsorId.value);
      projectOptions.value = sponsorProjects.value.map(project => ({
        label: project.name,
        value: project.id
      }));
      formData.value.project = sponsorProjects.value?.[0]?.id ?? null;
    }
  } finally {
    loading.value = false;
  }
});

function loadProject(projectId) {
  const project = sponsorProjects.value.find(p => p.id === projectId)
  if (!project) return

  formData.value.project_details.name = project.name ?? ''
  formData.value.project_details.website = project.website ?? ''
  formData.value.project_details.description = project.description ?? ''
  formData.value.project_details.availability = project.sponsor_availability ?? ''
}

watch(
  () => formData.value.project,
  (id) => {
    if (id) loadProject(id)
  }
)

const openConfirm = (data) => {
  pendingSubmission.value = data;
  showConfirm.value = true;
}

const cancelConfirm = () => {
  showConfirm.value = false;
  pendingSubmission.value = null;
}

async function handleSubmission() {
  const data = pendingSubmission.value;

  if (!data) {
    cancelConfirm();
    return;
  }

  showConfirm.value = false;
  pendingSubmission.value = null;

  try {
    const projectPayload = {
      name: data.project_details.name,
      description: data.project_details.description,
      website: data.project_details.website || null,
      sponsor: sponsorId.value,
      sponsor_availability: data.project_details.availability
    }

    const projectId = data.project;
    await apiService.putProject(projectPayload, projectId);

    router.push({
      path: '/sponsor',
      query: { flash: 'success', message: 'Your project has been updated.' }
    });

  } catch (error) {
    console.error("Submission failed:", error)
    if (error instanceof Error) {
      alert(error.message);
    } else {
      // fallback for unexpected errors
      alert("Submission failed.");
    }
  }
}

</script>

<template>
    <div class="container">
    <h1>Edit Project</h1>
    <div class="card">
    <div class="form-container">
        <p v-if="loading">Loading projects...</p>

        <div v-else-if="sponsorProjects.length === 0">
          <p>You have no projects submitted yet.</p>
          <p><router-link  to="/sponsor/submit">Submit a Project →</router-link></p>
        </div>

        <FormKit 
        v-else
        type="form" 
        id="sponsor-form"
        v-model="formData"
        submit-label="Edit Your Project"
        @submit="openConfirm"
        >

        <FormKit
            type="select"
            name="project"
            label="Select a Project"
            :options="projectOptions"
            validation="required"
            />

            <hr />

        <FormKit type="group" name="project_details" class="project_details">
            <FormKit
            type="text"
            name="name"
            label="Project Name"
            validation="required|length:5,100"
            />
            
            <FormKit
            type="url"
            name="website"
            label="Project/Company Website"
            placeholder="https://..."
            validation="url"
            />

            <FormKit
            type="textarea"
            name="description"
            label="Project Description"
            validation="required|length:20,2000"
            />

            <FormKit
            type="textarea"
            name="availability"
            label="Sponsor Availability"
            validation="required"
            help="State days of the week and the respective times of day you are available (Morning/Afternoon)"
            />
        </FormKit>

        <ConfirmationModal
          :show="showConfirm"
          title="Save project changes?"
          message="Confirm that you want to save these edits to the project."
          @confirm="handleSubmission"
          @cancel="cancelConfirm"
        />
        </FormKit>
    </div>
    </div>
    </div>
</template>

<style scoped>
hr {
  margin: 2rem 0;
}

.container {
  text-align: left;
  max-width: var(--max-content-width);
  margin: 0 auto;
}

.form-container :deep(.formkit-outer) {
  margin-bottom: 1.5rem;
}
</style>