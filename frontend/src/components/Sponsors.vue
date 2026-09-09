<template>
  <div>
    <h1>Sponsors</h1>
    <h5 v-if="loading">Fetching data...</h5>
    <div v-if="error">Error: {{ error.message }}</div>
    <div ref="tableContainer"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import 'tabulator-tables/dist/css/tabulator.min.css'; // Theme required for table to be visible, can use CSS overrides to adjust

// 1. Define reactive state for data, loading, and errors
const posts = ref(null);
const loading = ref(true);
const error = ref(null);
const tableContainer = ref(null); // Reference to DOM element
let tabulator = null; // Hold Tabulator instance

// 2. Define the asynchronous fetching function
const fetchData = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/v1/sponsors/?format=json'); // Example API endpoint
    posts.value = response.data; // Axios automatically parses JSON into the .data property
  } catch (err) {
    error.value = err;
    console.error(err);
  } finally {
    loading.value = false;
  }
};

// 3. Call the fetch function when the component mounts
onMounted(() => {
  // Initialize Tabulator with no data
  tabulator = new Tabulator(tableContainer.value, {
    data: [], // Start empty
    layout: "fitColumns",
    columns: [
      { title: "ID", field: "id", width: 50 },
      { title: "First Name", field: "first_name", sorter: "string" },
      { title: "Last Name", field: "last_name", sorter: "string" },
      { title: "Organization", field: "organization", sorter: "string" },
      { title: "Email", field: "email", sorter: "string" },
      { title: "Phone Number", field: "phone_number", sorter: "string" },
      { title: "Date Created", field: "created_at", sorter: "string" },
    ],
  });

  // Wait for table to be built, then fetch
  tabulator.on("tableBuilt", () => {
    fetchData();
  });
});

// Watch for data changes and update table automatically
watch(posts, (newData) => {
  if (tabulator) {
    tabulator.setData(newData);
  }
}, { deep: true });
</script>
