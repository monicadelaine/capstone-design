<!-- migrated to django admin portal; no longer in use -->

<script setup>
import { ref } from 'vue';

const recipients = ref('');
const semester = ref('spring');
const collectionDate = ref('Spring 2025 (1/14/25)');
const fromEmail = ref('');
const status = ref('');
const error = ref('');

const sendSponsorOutreach = async () => {
  if (!recipients.value.trim()) {
    error.value = 'Please enter at least one email address';
    return;
  }

  status.value = 'Sending...';
  error.value = '';

  const payload = {
    recipients: recipients.value,
    semester: semester.value,
    collection_date: collectionDate.value
  };

  if (fromEmail.value.trim()) {
    payload.from_email = fromEmail.value.trim();
  }

  try {
    const response = await fetch('http://localhost:8000/api/v1/emails/sponsor-outreach', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      if (response.ok) {
        status.value = 'Sponsor outreach email sent successfully!';
        recipients.value = '';
      } else {
        error.value = 'Server error occurred';
        status.value = '';
      }
      return;
    }

    const result = await response.json();

    if (response.ok) {
      status.value = 'Sponsor outreach email sent successfully!';
      recipients.value = '';
    } else {
      error.value = JSON.stringify(result);
      status.value = '';
    }
  } catch (err) {
    error.value = err.message;
    status.value = '';
  }
};
</script>

<template>
  <div class="sponsor-outreach">
    <h1>Send Sponsor Outreach Email</h1>
    <p>Send the UA CS Capstone project opportunity email to sponsors.</p>
    
    <form @submit.prevent="sendSponsorOutreach">
      <label>
        Recipient Email(s)
        <input 
          v-model="recipients" 
          type="text" 
          placeholder="email1@example.com, email2@example.com" 
        />
      </label>

      <label>
        Semester
        <select v-model="semester">
          <option value="spring">Spring</option>
          <option value="fall">Fall</option>
        </select>
      </label>

      <label>
        Collection Date
        <input v-model="collectionDate" type="text" placeholder="Spring 2025 (1/14/25)" />
      </label>

      <label>
        From Email (optional)
        <input v-model="fromEmail" type="email" placeholder="sender@example.com" />
      </label>

      <button type="submit">Send Outreach Email</button>
    </form>

    <p v-if="status" class="success">{{ status }}</p>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.sponsor-outreach {
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

input, select {
  width: 100%;
  padding: 8px;
  margin-top: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
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
