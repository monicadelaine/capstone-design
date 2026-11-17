import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@auth0/auth0-vue', () => ({
    useAuth0: () => ({ getAccessTokenSilently: vi.fn().mockResolvedValue('test-token') }),
}))

vi.mock('../services/api', () => {
    const apiService = { setToken: vi.fn(), getAssignments: vi.fn(), client: { get: vi.fn() } }
    return { default: apiService, apiService }
})

import apiService from '../services/api'
import { useProjectsStore } from '../stores/projectsStore'
import { useStudentStore } from '../stores/studentStore'
import StudentAssignmentCard from './StudentAssignmentCard.vue'

const person = (id, first, last) => ({ id, first_name: first, last_name: last, email: `${first.toLowerCase()}@crimson.ua.edu` })
const row = (id, student, semester = 1) => ({ id: `${student.id}-11`, student: student.id, semester, project: 11, student_detail: student })

function mountCard({ assigned = true } = {}) {
    setActivePinia(createPinia())
    const students = useStudentStore()
    const projects = useProjectsStore()
    students.profile = { id: 1 }
    students.assignment = assigned ? { id: '1-11', student: 1, semester: 1, project: 11 } : null
    projects.projects = [{ id: 11, name: 'Fleet Route Optimizer', description: 'Routes', sponsor: 4 }]
    projects.projectsLoaded = true
    return mount(StudentAssignmentCard)
}

describe('StudentAssignmentCard: the team (#70)', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        vi.spyOn(console, 'warn').mockImplementation(() => {})
        apiService.client.get.mockResolvedValue({ data: { organization: 'Acme', email: 'pat@acme.example', phone_number: '2055551234' } })
        apiService.getAssignments.mockResolvedValue([
            row('a', person(1, 'Ann', 'Lee')),
            row('b', person(2, 'Bo', 'Ray')),
        ])
    })

    it('shows the project, the sponsor contact, and each teammate with an email link', async () => {
        const wrapper = mountCard()
        await flushPromises()

        const text = wrapper.text()
        expect(text).toContain('Fleet Route Optimizer')
        expect(text).toContain('pat@acme.example')
        expect(text).toContain('Bo Ray')
        const links = wrapper.findAll('.team-member-email')
        expect(links.map(a => a.attributes('href'))).toEqual(['mailto:ann@crimson.ua.edu', 'mailto:bo@crimson.ua.edu'])
    })

    it('marks the signed-in student as "you"', async () => {
        const wrapper = mountCard()
        await flushPromises()

        const names = wrapper.findAll('.team-member-name').map(n => n.text())
        expect(names).toEqual(['Ann Lee (you)', 'Bo Ray'])
    })

    it("asks only for this project's assignments, and never reads the students list", async () => {
        mountCard()
        await flushPromises()

        expect(apiService.getAssignments).toHaveBeenCalledWith({ project: '11' })
        const urls = apiService.client.get.mock.calls.map(c => c[0])
        expect(urls.some(u => String(u).includes('/students'))).toBe(false)
    })

    it("shows only this semester's team", async () => {
        apiService.getAssignments.mockResolvedValue([
            row('a', person(1, 'Ann', 'Lee'), 1),
            row('b', person(2, 'Bo', 'Ray'), 1),
            row('c', person(3, 'Old', 'Timer'), 0),
        ])

        const wrapper = mountCard()
        await flushPromises()

        expect(wrapper.text()).not.toContain('Old Timer')
        expect(wrapper.findAll('.team-member-name')).toHaveLength(2)
    })

    it('says so when the team cannot be loaded, and still shows the project', async () => {
        apiService.getAssignments.mockRejectedValue(new Error('boom'))

        const wrapper = mountCard()
        await flushPromises()

        expect(wrapper.text()).toContain('No team members to show.')
        expect(wrapper.text()).toContain('Fleet Route Optimizer')
    })

    it('shows nothing about a team when there is no assignment', async () => {
        const wrapper = mountCard({ assigned: false })
        await flushPromises()

        expect(wrapper.text()).toContain('No assignment found.')
        expect(apiService.getAssignments).not.toHaveBeenCalled()
    })
})
