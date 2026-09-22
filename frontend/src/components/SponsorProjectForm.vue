<script setup>
import { FormKit } from '@formkit/vue';
import apiService from '../services/api';
import { useAuth0 } from '@auth0/auth0-vue';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import ConfirmationModal from './ConfirmationModal.vue';

const { getAccessTokenSilently } = useAuth0();
const router = useRouter();
const sponsorId = ref(null);
const profile = ref(null);
const tooManyProjects = ref(false);
const showConfirm = ref(false);
const pendingSubmission = ref(null);
const submitting = ref(false);
const submitError = ref(null);

// Inputs are locked while the sponsor is at their limit or a submission is in flight.
const formDisabled = computed(() => tooManyProjects.value || submitting.value);

// "Ada Lovelace, Analytical Engines (ada@example.com)" from the sponsor profile.
const submittingAs = computed(() => {
  const p = profile.value;
  if (!p) return '';
  const name = [p.first_name, p.last_name].filter(Boolean).join(' ');
  const who = [name, p.organization].filter(Boolean).join(', ');
  return p.email ? `${who} (${p.email})` : who;
});

// Labels for server-side field errors that map to inputs on this form.
const FIELD_LABELS = {
  name: 'Project name',
  description: 'Project description',
  website: 'Website',
  sponsor_availability: 'Sponsor availability',
};

/** Turn an API failure into text the sponsor can act on. */
function describeError(error) {
  const data = error?.response?.data;

  if (data && typeof data === 'object') {
    const messages = Object.entries(data).flatMap(([field, value]) => {
      const list = Array.isArray(value) ? value : [value];
      const label = FIELD_LABELS[field];
      return list.map((msg) => (label ? `${label}: ${msg}` : String(msg)));
    });
    if (messages.length) return messages.join(' ');
  }

  if (typeof data === 'string' && data.trim()) return data;
  return error?.message || 'Submission failed. Please try again.';
}

async function loadProjectLimitState() {
  const token = await getAccessTokenSilently();
  apiService.setToken(token);

  const profileResponse = await apiService.getProfile();
  profile.value = profileResponse.data ?? null;
  sponsorId.value = profileResponse.data?.id ?? null;

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

  if (!data || tooManyProjects.value || submitting.value) {
    cancelConfirm();
    return;
  }

  showConfirm.value = false;
  pendingSubmission.value = null;
  submitError.value = null;
  submitting.value = true;

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
    console.error('Submission failed:', error);
    submitError.value = describeError(error);
  } finally {
    submitting.value = false;
  }
}

</script>

<template>
    <div class="container">
    <h1>Project Submission</h1>
    <div v-if="tooManyProjects" class="warning-block" role="alert">
          You have reached the maximum number of allowed projects, so this form is currently disabled.
    </div>
    <div v-if="submitError" class="info error" role="alert">
          <strong>Your proposal was not submitted.</strong>
          <p>{{ submitError }}</p>
    </div>
    <div class="card">
    <div class="form-container">
        <FormKit 
        type="form" 
        id="sponsor-form"
        :submit-label="submitting ? 'Submitting...' : 'Submit Project Proposal'"
        :submit-attrs="{ disabled: formDisabled }"
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
            <h3>Sponsor Availability</h3>
            <p v-if="submittingAs" class="submitting-as">
              Submitting as <strong>{{ submittingAs }}</strong>.
              <router-link to="/profile/edit">Edit profile</router-link>
            </p>

            <FormKit
            type="textarea"
            name="availability"
            label="Sponsor Availability"
            validation="required"
            help="State days of the week and the respective times of day you are available (Morning/Afternoon)"
            :disabled="formDisabled"
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
            :disabled="formDisabled"
            />
            
            <FormKit
            type="url"
            name="website"
            label="Project/Company Website"
            placeholder="https://..."
            validation="url"
            :disabled="formDisabled"
            />

            <FormKit
            type="textarea"
            name="description"
            label="Project Description"
            validation="required|length:20,2000"
            :disabled="formDisabled"
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

.info.error {
  margin-bottom: 1rem;
}

.submitting-as {
  margin-bottom: 1rem;
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