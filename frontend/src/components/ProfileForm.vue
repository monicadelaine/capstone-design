<script setup>
import { computed } from 'vue';

const props = defineProps({
  role: {
    type: String,
    required: true,
    validator: (value) => ['student', 'sponsor'].includes(value.toLowerCase())
  },
  initialData: {
    type: Object,
    default: () => ({})
  },
  isEdit: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['submit']);

const sponsorFields = [
  { name: 'first_name', label: 'First Name', type: 'text', rules: 'required' },
  { name: 'last_name', label: 'Last Name', type: 'text', rules: 'required' },
  { name: 'organization', label: 'Organization', type: 'text', required: false },
  { name: 'phone_number', label: 'Phone Number', type: 'tel', required: false }
];

const studentFields = [
  { name: 'first_name', label: 'First Name', type: 'text', rules: 'required' },
  { name: 'last_name', label: 'Last Name', type: 'text', rules: 'required' },
  { name: 'middle_name', label: 'Middle Name', type: 'text', required: false },
  { name: 'preferred_name', label: 'Preferred Name', type: 'text', required: false },
  { name: 'cwid', label: 'CWID', type: 'text', rules: 'required|length:8' },
  { name: 'class_code', label: 'Class Code', type: 'text', required: false },
  { name: 'major_code', label: 'Major Code', type: 'text', required: false }
];

const fields = computed(() => {
  return props.role === 'sponsor' ? sponsorFields : studentFields;
});

const formTitle = computed(() => {
  const action = props.isEdit ? 'Make changes to your profile.' : 'Please fill in your information to continue.';
  return `${action}`;
});

const handleSubmit = (formData) => {
  emit('submit', formData);
};
</script>

<template>
  <div class="profile-form-container">
    <p>{{ formTitle }}</p>
    
    <FormKit
      type="form"
      :actions="false"
      @submit="handleSubmit"
    >
      <div class="form-grid">
        <FormKit
          v-for="field in fields"
          :key="field.name"
          :type="field.type"
          :name="field.name"
          :label="field.label"
          :value="initialData[field.name] || ''"
          :rules="field.rules"
          :validation-messages="{
            required: `${field.label} is required`,
            length: 'CWID must be exactly 8 digits'
          }"
        />
      </div>
      
      <div class="form-actions">
        <FormKit
          type="submit"
          :label="isEdit ? 'Update Profile' : 'Create Profile'"
          input-class="submit-btn"
        />
      </div>
    </FormKit>
  </div>
</template>

<style scoped>
.profile-form-container {
  margin: 0 auto;
  padding: 2rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

h2 {
  margin: 0 0 2rem 0;
  color: var(--text-default);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-grid > :deep(.formkit-wrapper) {
  margin-bottom: 0;
}

.form-actions {
  margin-top: 2rem;
}

.submit-btn {
  border-radius: 8px;
  border: 1px solid transparent;
  padding: 0.6em 1.2em;
  font-size: 1rem;
  font-family: inherit;
  font-weight: bold;
  background-color: var(--accent-primary);
  color: white;
  cursor: pointer;
  transition: border-color 0.25s;
}

.submit-btn:hover {
  background: var(--accent-dark);
}

@media (max-width: 600px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
