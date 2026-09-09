<!-- Admin landing page -->
<!-- Roles:
        Send emails
        Assign projects
        Import students
        View student rankings
-->
<script setup>

</script>

<template>
    <h1>Admin Page</h1>
    <!-- TODO: assign proper router destinations for buttons -->
    <div class="wrapper">
        <router-link to="/admin">
            <button>Send emails</button>
        </router-link>
        <router-link to="/admin">
            <button>Assign Projects</button>
        </router-link>
        <router-link to="/admin">
            <button>Import Students</button>
        </router-link>
        <router-link to="/admin">
            <button>View Student Rankings</button>
        </router-link>
    </div>
</template>

<style scoped>
.wrapper {
    margin: 0 auto;
    max-width: var(--max-content-width);
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
button {
    width: 100%;
}
</style>