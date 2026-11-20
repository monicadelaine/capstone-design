import { flushPromises, shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@auth0/auth0-vue', () => ({
    useAuth0: () => ({ getAccessTokenSilently: vi.fn().mockResolvedValue('test-token') }),
}))

vi.mock('../services/api', () => {
    const apiService = { setToken: vi.fn(), getProfile: vi.fn(), getCurrentSemester: vi.fn(), client: { get: vi.fn() } }
    return { default: apiService, apiService }
})

import apiService from '../services/api'
import StudentAssignment from './StudentAssignment.vue'
import StudentAssignmentCard from './StudentAssignmentCard.vue'

// The API only returns assignments once the instructor has approved a proposal, so a student with no
// assignment rows is a student whose assignments are not published yet.
function serve(assignments) {
    apiService.getProfile.mockResolvedValue({ data: { id: 1 } })
    apiService.getCurrentSemester.mockResolvedValue({ id: 1, assignment_date: '2099-01-01T00:00:00Z' })
    apiService.client.get.mockImplementation(async (url) => {
        if (url.startsWith('/assignments/')) return { data: assignments }
        return { data: [] }
    })
}

async function mountPage() {
    setActivePinia(createPinia())
    const wrapper = shallowMount(StudentAssignment)
    await flushPromises()
    return wrapper
}

describe('StudentAssignment: nothing before the assignments are published (#70)', () => {
    beforeEach(() => vi.clearAllMocks())

    it('tells the student no assignment has been made, and shows no team', async () => {
        serve([])

        const wrapper = await mountPage()

        expect(wrapper.text()).toContain('No assignment has been made.')
        expect(wrapper.findComponent(StudentAssignmentCard).exists()).toBe(false)
    })

    it('shows the assignment once there is one', async () => {
        serve([{ id: '1-11', student: 1, semester: 1, project: 11 }])

        const wrapper = await mountPage()

        expect(wrapper.findComponent(StudentAssignmentCard).exists()).toBe(true)
        expect(wrapper.text()).not.toContain('No assignment has been made.')
    })
})
