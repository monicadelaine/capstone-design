<script setup>
import { FormKit } from '@formkit/vue';
import apiService from '../services/api';
import { useAuth0 } from '@auth0/auth0-vue';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import ConfirmationModal from './ConfirmationModal.vue';

const { getAccessTokenSilently } = useAuth0();
const router = useRouter();
const sponsorId = ref(null);
const tooManyProjects = ref(false);
const showConfirm = ref(false);
const pendingSubmission = ref(null);

async function loadProjectLimitState() {
  const token = await getAccessTokenSilently();
  apiService.setToken(token);

  const profileResponse = await apiService.getProfile();
  sponsorId.value = profileResponse.data.id ?? null;

  if (!sponsorId.value) {
    tooManyProjects.value = false;
    return;
  }

  const currentProjects = await apiService.getProjectsBySponsor(sponsorId.value);
  const projectCount = currentProjects.length;
  const projectNumLimit = Number(profileResponse.data.projects_allowed);

  tooManyProjects.value = projectCount >= projectNumLimit;
}

onMounted(async () => {
  try {
    await loadProjectLimitState();
  } catch (error) {
    console.error('Failed to load project limit state:', error);
    tooManyProjects.value = false;
  }
});

const openConfirm = (data) => {
  if (tooManyProjects.value) {
    alert('You have reached the maximum number of allowed projects.');
    return;
  }

  pendingSubmission.value = data;
  showConfirm.value = true;
};

const cancelConfirm = () => {
  showConfirm.value = false;
  pendingSubmission.value = null;
};

async function handleSubmission() {
  const data = pendingSubmission.value;

  if (!data || tooManyProjects.value) {
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
      sponsor_availability: data.sponsor_info.availability
    }

    await apiService.createProject(projectPayload);

    router.push({
      path: '/sponsor',
      query: { flash: 'success', message: 'Your project proposal has been submitted.' }
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
    <h1>Project Submission</h1>
    <div v-if="tooManyProjects" class="warning-block" role="alert">
          You have reached the maximum number of allowed projects, so this form is currently disabled.
    </div>
    <div class="card">
    <div class="form-container">
        <FormKit 
        type="form" 
        id="sponsor-form"
        submit-label="Submit Project Proposal"
        :submit-attrs="{ disabled: tooManyProjects }"
      @submit="openConfirm"
        >

        <div class="form-intro">
          <p>
            Thank you for your interest in sponsoring a computer science capstone projects. Our students have 
            spent 4 years aquiring skills. The opportunity to have a culminating experience that incorporates
            everything they have learned is invaluable. your willingness to be a part of that experience 
            appreciated. At the same time, we are honored to contribute to the university community.
          </p>
          <p>
            When presenting your project, students will want to know the purpose of the system, who will be 
            using it, and what users should be able to do. It is helpful to provide information on how the 
            users will access the systems and how many users you expect.
          </p>
          <p><strong>External Sponsor/Student Agreement</strong></p>
          <p>Project sponsors will: </p>
          <ul>
            <li>Provide students with a list of user interactions and functionality (what the software should do).</li>
            <li>Meet with students weekly to prioritize feature implementation.</li>
            <li>Provide frequent feedback on how well the software meets the business requirements.</li>
            <li>Provide timely answers to questions.</li>
          </ul>
          <p>
            Students will:
          </p>
          <ul>
            <li>Choose tools, language and platforms that are appropriate for the requirements.</li>
            <li>Use Agile Software Development Practices.</li>
            <li>Document non-functional requirements.</li>
            <li>Incorporate feedback from project sponsors.</li>
            <li>Keep accurate records of all meetings and interactions.</li>
        </ul>
        </div>

        <hr />

        <FormKit type="group" name="sponsor_info">
            <h3>Contact Information</h3>
            <FormKit
            type="text"
            name="company_name"
            label="Company/Organization"
            validation="required"
            :disabled="tooManyProjects"
            />

            <FormKit
            type="email"
            name="contact_email"
            label="Primary Contact Email"
            validation="required|email"
            :disabled="tooManyProjects"
            />

            <FormKit
            type="textarea"
            name="availability"
            label="Sponsor Availability"
            validation="required"
            help="State days of the week and the respective times of day you are available (Morning/Afternoon)"
            :disabled="tooManyProjects"
            />
        </FormKit>

        <hr />

        <FormKit type="group" name="project_details">
            <h3>Project Details</h3>
            <FormKit
            type="text"
            name="name"
            label="Project Name"
            validation="required|length:5,100"
            :disabled="tooManyProjects"
            />
            
            <FormKit
            type="url"
            name="website"
            label="Project/Company Website"
            placeholder="https://..."
            validation="url"
            :disabled="tooManyProjects"
            />

            <FormKit
            type="textarea"
            name="description"
            label="Project Description"
            validation="required|length:20,2000"
            :disabled="tooManyProjects"
            />
        </FormKit>
        </FormKit>

          <ConfirmationModal
            :show="showConfirm"
            title="Submit project proposal?"
            message="Confirm that you want to submit this project proposal."
            @confirm="handleSubmission"
            @cancel="cancelConfirm"
          />
    </div>
    </div>
    </div>
</template>

<style scoped>
hr {
    margin-top: 2rem;
}
.container {
  text-align: left;
  max-width: var(--max-content-width);
  margin: 0 auto;
}

.warning-block {
  margin-bottom: 1rem;
  padding: 1rem 1.25rem;
  border: 1px solid #d97706;
  border-radius: 0.5rem;
  background: #fffbeb;
  color: #92400e;
  font-weight: 600;
}
</style>