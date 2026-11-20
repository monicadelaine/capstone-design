import { flushPromises, shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@auth0/auth0-vue', () => ({
    useAuth0: () => ({ getAccessTokenSilently: vi.fn().mockResolvedValue('test-token') }),
}))

vi.mock('vue-router', () => ({
    useRoute: () => ({ query: {}, path: '/sponsor' }),
    useRouter: () => ({ replace: vi.fn() }),
}))

vi.mock('../services/api', () => {
    const apiService = {
        setToken: vi.fn(),
        getProfile: vi.fn(),
        getProjectsBySponsor: vi.fn(),
        getCurrentSemester: vi.fn(),
        getAssignments: vi.fn(),
    }
    return { default: apiService, apiService }
})

import apiService from '../services/api'
import SponsorLanding from './SponsorLanding.vue'
import SponsorProjectCard from './SponsorProjectCard.vue'

const student = (id, first, last) => ({ id, first_name: first, last_name: last, email: `${first.toLowerCase()}@crimson.ua.edu` })

async function mountDashboard() {
    const wrapper = shallowMount(SponsorLanding, { global: { stubs: { 'router-link': true } } })
    await flushPromises()
    return wrapper
}

const cards = (wrapper) => wrapper.findAllComponents(SponsorProjectCard)

describe('SponsorLanding: assigned students', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        vi.spyOn(console, 'error').mockImplementation(() => {})
        apiService.getProfile.mockResolvedValue({ data: { id: 3 } })
        apiService.getProjectsBySponsor.mockResolvedValue([
            { id: 11, name: 'Fleet Route Optimizer' },
            { id: 12, name: 'Wildlife Sighting Map' },
        ])
        apiService.getCurrentSemester.mockResolvedValue({ id: 9 })
        apiService.getAssignments.mockResolvedValue([
            { id: '1-11', project: 11, student_detail: student(1, 'Zed', 'Young') },
            { id: '2-11', project: 11, student_detail: student(2, 'Ann', 'Adams') },
        ])
    })

    it("asks for this semester's assignments and gives each project its own students", async () => {
        const wrapper = await mountDashboard()

        expect(apiService.getAssignments).toHaveBeenCalledWith({ semester: 9 })
        expect(cards(wrapper)[0].props('students').map(s => s.last_name)).toEqual(['Adams', 'Young'])
        expect(cards(wrapper)[1].props('students')).toEqual([])
    })

    it('asks for every semester when there is no current one', async () => {
        apiService.getCurrentSemester.mockResolvedValue({})

        await mountDashboard()

        expect(apiService.getAssignments).toHaveBeenCalledWith({})
    })

    it('still shows the projects, with the students marked unavailable, when they cannot be loaded', async () => {
        apiService.getAssignments.mockRejectedValue(new Error('boom'))

        const wrapper = await mountDashboard()

        expect(cards(wrapper)).toHaveLength(2)
        expect(cards(wrapper)[0].props('students')).toBeNull()
    })
})
