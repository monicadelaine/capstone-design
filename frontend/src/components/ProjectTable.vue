<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import 'tabulator-tables/dist/css/tabulator.min.css';

const route = useRoute(); // track route changes
const posts = ref([]);
const loading = ref(true);
const error = ref(null);
const tableContainer = ref(null);
let tabulator = null;

// Fetch data function
const fetchData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await axios.get('http://localhost:8000/api/v1/projects/?format=json');
    posts.value = response.data;
  } catch (err) {
    error.value = err;
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const props = defineProps({
  sponsorId: {
    type: String,
    required: false,
    default: null
  }
});

const filteredPosts = computed(() => {
  if (!props.sponsorId) {
    return posts.value; // show all if no sponsorId
  }
  return posts.value.filter(
    post => String(post.sponsor) === String(props.sponsorId)
  );
});

onMounted(() => {
  // Initialize Tabulator
  tabulator = new Tabulator(tableContainer.value, {
    data: [], // initially empty
    layout: "fitColumns",
    columns: [
      { title: "ID", field: "id", width: 50 },
      { title: "Name", field: "name" },
      { title: "Description", field: "description" },
      { title: "Availability", field: "sponsor_availability" },
      { title: "Website", field: "website" },
      { title: "Created", field: "created_at" },
      { title: "Status", field: "status" },
    ],
  });

  fetchData(); // initial load
});

// Watch route changes and refresh table
watch(
  () => route.fullPath, 
  () => {
    if (tabulator) tabulator.setData([]); // clear old data
    fetchData();
  }
);

// Update table when posts change
watch(filteredPosts, (newData) => {
  if (tabulator) tabulator.setData(newData);
}, { deep: true });
</script>

<template>
  <div>
    <h5 v-if="loading">Fetching projects...</h5>
    <div v-if="error">Error: {{ error.message }}</div>
    <div ref="tableContainer"></div>
  </div>
</template>