<script setup>
import { ref } from 'vue';

const recipients = ref('');
const date = ref('');
const time = ref('');
const projectName = ref('');
const projectDescription = ref('');
const contactName = ref('');
const contactEmail = ref('');
const zoomDetails = ref('');
const fromEmail = ref('');
const status = ref('');
const error = ref('');

const sendProjectPresentation = async () => {
  if (!recipients.value.trim()) {
    error.value = 'Please enter at least one email address';
    return;
  }

  status.value = 'Sending...';
  error.value = '';

  const payload = {
    recipients: recipients.value,
    date: date.value,
    time: time.value,
    project_name: projectName.value,
    project_description: projectDescription.value,
    contact_name: contactName.value,
    contact_email: contactEmail.value,
    zoom_details: zoomDetails.value
  };

  if (fromEmail.value.trim()) {
    payload.from_email = fromEmail.value.trim();
  }

  try {
    const response = await fetch('http://localhost:8000/api/v1/emails/project-presentation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      if (response.ok) {
        status.value = 'Project presentation email sent successfully!';
        clearForm();
      } else {
        error.value = 'Server error occurred';
        status.value = '';
      }
      return;
    }

    const result = await response.json();

    if (response.ok) {
      status.value = 'Project presentation email sent successfully!';
      clearForm();
    } else {
      error.value = JSON.stringify(result);
      status.value = '';
    }
  } catch (err) {
    error.value = err.message;
    status.value = '';
  }
};

const clearForm = () => {
  recipients.value = '';
  date.value = '';
  time.value = '';
  projectName.value = '';
  projectDescription.value = '';
  contactName.value = '';
  contactEmail.value = '';
  zoomDetails.value = '';
};
</script>

<template>
  <div class="project-presentation">
    <h1>Send Project Presentation Email</h1>
    <p>Send the project presentation invitation email to sponsors.</p>
    
    <form @submit.prevent="sendProjectPresentation">
      <label>
        Recipient Email(s)
        <input 
          v-model="recipients" 
          type="text" 
          placeholder="email1@example.com, email2@example.com" 
        />
      </label>

      <label>
        Date
        <input v-model="date" type="text" placeholder="Tuesday Jan 14, 2025" />
      </label>

      <label>
        Time
        <input v-model="time" type="text" placeholder="3:45 - 4:00" />
      </label>

      <label>
        Project Name
        <input v-model="projectName" type="text" placeholder="Project Name" />
      </label>

      <label>
        Project Description
        <textarea v-model="projectDescription" placeholder="Description of the project"></textarea>
      </label>

      <label>
        Contact Name
        <input v-model="contactName" type="text" placeholder="John Doe" />
      </label>

      <label>
        Contact Email
        <input v-model="contactEmail" type="email" placeholder="john@example.com" />
      </label>

      <label>
        Zoom Details
        <textarea v-model="zoomDetails" placeholder="Zoom meeting link and details"></textarea>
      </label>

      <label>
        From Email (optional)
        <input v-model="fromEmail" type="email" placeholder="sender@example.com" />
      </label>

      <button type="submit">Send Presentation Email</button>
    </form>

    <p v-if="status" class="success">{{ status }}</p>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.project-presentation {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  margin-bottom: 10px;
}

p {
  color: #666;
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 15px;
  font-weight: bold;
}

input, textarea {
  width: 100%;
  padding: 8px;
  margin-top: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

textarea {
  height: 80px;
}

button {
  padding: 10px 20px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #218838;
}

.success {
  margin-top: 15px;
  padding: 10px;
  background-color: #d4edda;
  color: #155724;
  border-radius: 4px;
}

.error {
  margin-top: 15px;
  padding: 10px;
  background-color: #f8d7da;
  color: #721c24;
  border-radius: 4px;
}
</style>
