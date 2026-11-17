<script setup>
import { computed, ref, onMounted } from 'vue'
import { useStudentStore } from '../stores/studentStore'
import { useProjectsStore } from '../stores/projectsStore'
import apiService from '../services/api'
import { useAuth0 } from '@auth0/auth0-vue'

const studentStore = useStudentStore()
const projectsStore = useProjectsStore()
const { getAccessTokenSilently } = useAuth0()

const assignedProjectId = computed(() => studentStore.assignedProjectId)
const assignment = computed(() => studentStore.assignment)
const assignedProject = computed(() => {
    const id = assignedProjectId.value
    if (!id) return null
    return (projectsStore.projects || []).find(p => String(p.id) === String(id)) || null
})

const sponsor = ref(null)
const team = ref([])

const isYou = (a) => a.student === studentStore.profile?.id

const sponsorName = computed(() => {
    if (sponsor && sponsor.value) {
        return sponsor.value.organization ? sponsor.value.organization : `${sponsor.value.first_name || ''}${sponsor.value.first_name && sponsor.value.last_name ? ' ' : ''}${sponsor.value.last_name || ''}`.trim()
    }
    return null
})

onMounted(async () => {
    try {
        const token = await getAccessTokenSilently()
        apiService.setToken(token)

        // Ensure projects are loaded (parent should do this, but be defensive)
        await projectsStore.fetchProjects()

        if (!assignedProjectId.value) return

        const proj = assignedProject.value
        // fetch sponsor details if present
        try {
            const sponsorId = proj?.sponsor
            if (sponsorId) {
                const sResp = await apiService.client.get(`/sponsors/${sponsorId}/`)
                sponsor.value = sResp.data
            }
        } catch (sErr) {
            console.warn('StudentAssignmentCard: failed to load sponsor', sErr)
        }

        // The team: everyone assigned to this project this semester. The API sends each student's name
        // and email with the assignment, and only for the people this student is allowed to see.
        try {
            const rows = await apiService.getAssignments({ project: assignedProjectId.value })
            const semester = assignment.value?.semester
            team.value = (Array.isArray(rows) ? rows : [])
                .filter(a => a.student_detail && (!semester || a.semester === semester))
        } catch (aErr) {
            console.warn('StudentAssignmentCard: failed to load the team', aErr)
            team.value = []
        }
    } catch (e) {
        console.error('StudentAssignmentCard init error', e)
    }
})
</script>

<template>
    <div v-if="assignment && assignedProject" class="inside-wrapper">
        <div class="card">
            <h2>{{ assignedProject.name }}</h2>
            <div class="person-info">
                <div class="person-logo">{{ sponsorName?.charAt(0) }}</div>
                <h4>{{ sponsorName || (assignedProject.sponsor || 'Sponsor') }}</h4>
            </div>
            <hr style="margin-top: 1.5rem"/>
            <h3>Description</h3>
            <p v-if="assignedProject.description">{{ assignedProject.description }}</p>
            <p v-else class="muted">No description provided.</p>

            <h3>Sponsor Contact Info</h3>
            <p v-if="sponsor && sponsor.phone_number">Phone number: <a :href="'tel:' + sponsor.phone_number">{{ sponsor.phone_number }}</a></p>
            <p v-else>Phone number: N/A</p>
            <p v-if="sponsor && sponsor.email">Email: <a :href="'mailto:' + sponsor.email">{{ sponsor.email }}</a></p>
            <p v-else>Email: N/A</p>
        </div>
        <div class="card">
            <h2>Your Team</h2>
            <div class="team-info">
                <div v-for="a in team" :key="a.id" class="person-info">
                    <div class="person-logo">{{ a.student_detail.first_name.charAt(0) }}</div>
                    <div class="team-member-text">
                        <span class="team-member-name">{{ a.student_detail.first_name }} {{ a.student_detail.last_name }}<template v-if="isYou(a)"> (you)</template></span>
                        <a class="team-member-email" :href="'mailto:' + a.student_detail.email">{{ a.student_detail.email }}</a>
                    </div>
                </div>
                <p v-if="team.length === 0" class="muted">No team members to show.</p>
            </div>
        </div>
    </div>
    <div v-else class="info error">
        <p>No assignment found.</p>
    </div>

</template>

<style scoped>
h2 {
    margin-top: 0.5rem;
}
h4 {
    margin-top: 0;
    margin-bottom: 0;
}
.inside-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}
.muted { color: var(--text-muted); }
.person-logo {
  width: 32px;
  height: 32px;
  background: var(--accent-primary);
  color: white;
  flex: 0 0 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-weight: bold;
}
.person-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.team-info {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-evenly;
    gap: 1rem;
    align-items: flex-start;
}
.team-member-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
}
.team-member-name {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.team-member-email {
    font-size: 0.85rem;
    overflow-wrap: anywhere;
}
.student-info ul { list-style: none; padding: 0; }
</style>