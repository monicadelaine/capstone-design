import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defaultConfig, plugin } from '@formkit/vue'

const mocks = vi.hoisted(() => ({
    pushMock: vi.fn(),
    getAccessTokenSilentlyMock: vi.fn(),
    setTokenMock: vi.fn(),
    getProfileMock: vi.fn(),
    getProjectsBySponsorMock: vi.fn(),
    createProjectMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
    useRouter: () => ({ push: mocks.pushMock }),
}))

vi.mock('@auth0/auth0-vue', () => ({
    useAuth0: () => ({ getAccessTokenSilently: mocks.getAccessTokenSilentlyMock }),
}))

vi.mock('../services/api', () => ({
    default: {
        setToken: mocks.setTokenMock,
        getProfile: mocks.getProfileMock,
        getProjectsBySponsor: mocks.getProjectsBySponsorMock,
        createProject: mocks.createProjectMock,
    },
}))

import SponsorProjectForm from './SponsorProjectForm.vue'

const sponsorProfile = {
    type: 'sponsor',
    data: {
        id: 4,
        first_name: 'Ada',
        last_name: 'Lovelace',
        organization: 'Analytical Engines',
        email: 'ada@example.com',
        projects_allowed: 3,
    },
}

function mountForm() {
    return mount(SponsorProjectForm, {
        global: {
            plugins: [[plugin, defaultConfig]],
            stubs: { RouterLink: { template: '<a><slot /></a>' } },
        },
    })
}

async function mountLoaded(existingProjects = []) {
    mocks.getProfileMock.mockResolvedValue(sponsorProfile)
    mocks.getProjectsBySponsorMock.mockResolvedValue(existingProjects)
    const wrapper = mountForm()
    await flushPromises()
    return wrapper
}

// FormKit commits values and runs validation on a short real-time debounce,
// so tests must wait on the clock, not just flush microtasks.
async function settle(ms = 60) {
    await new Promise((resolve) => setTimeout(resolve, ms))
    await flushPromises()
}

async function fillAndSubmit(wrapper) {
    await wrapper.find('textarea[name="availability"]').setValue('Weekday mornings')
    await wrapper.find('input[name="name"]').setValue('Capstone Manager')
    await wrapper
        .find('textarea[name="description"]')
        .setValue('A long enough description of the project for validation.')
    await settle()
    await wrapper.find('form').trigger('submit')
    await settle()

    const confirmButton = wrapper.findAll('button').find((b) => b.text() === 'Confirm')
    const validationMessages = wrapper.findAll('.formkit-message').map((m) => m.text()).join(' | ')
    expect(confirmButton, `confirmation modal should open; FormKit messages: ${validationMessages}`).toBeTruthy()
    await confirmButton.trigger('click')
    await flushPromises()
}

describe('SponsorProjectForm', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mocks.getAccessTokenSilentlyMock.mockResolvedValue('token')
    })

    it('shows who is submitting from the profile instead of asking again', async () => {
        const wrapper = await mountLoaded()

        expect(wrapper.text()).toContain('Submitting as Ada Lovelace, Analytical Engines (ada@example.com)')
        expect(wrapper.find('input[name="company_name"]').exists()).toBe(false)
        expect(wrapper.find('input[name="contact_email"]').exists()).toBe(false)
        expect(wrapper.find('textarea[name="availability"]').exists()).toBe(true)
        expect(mocks.setTokenMock).toHaveBeenCalledWith('token')
    })

    it('disables the form once the sponsor has reached the project limit', async () => {
        const wrapper = await mountLoaded([{ id: 1 }, { id: 2 }, { id: 3 }])

        expect(wrapper.text()).toContain('maximum number of allowed projects')
        expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()
    })

    it('submits the payload, locks the form while pending, then goes to the dashboard', async () => {
        let resolveCreate
        mocks.createProjectMock.mockReturnValue(new Promise((resolve) => { resolveCreate = resolve }))
        const wrapper = await mountLoaded()

        await fillAndSubmit(wrapper)

        expect(mocks.createProjectMock).toHaveBeenCalledWith({
            name: 'Capstone Manager',
            description: 'A long enough description of the project for validation.',
            website: null,
            sponsor: 4,
            sponsor_availability: 'Weekday mornings',
        })
        expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()
        expect(wrapper.find('button[type="submit"]').text()).toContain('Submitting')

        resolveCreate({ id: 10 })
        await flushPromises()

        expect(mocks.pushMock).toHaveBeenCalledWith({
            path: '/sponsor',
            query: { flash: 'success', message: 'Your project proposal has been submitted.' },
        })
        expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeUndefined()
    })

    it('shows the server message inline when the API rejects the proposal', async () => {
        vi.spyOn(console, 'error').mockImplementation(() => {})
        mocks.createProjectMock.mockRejectedValue({
            response: { data: { sponsor: ['You have reached the maximum of 3 projects.'] } },
        })
        const wrapper = await mountLoaded()

        await fillAndSubmit(wrapper)

        expect(wrapper.text()).toContain('Your proposal was not submitted.')
        expect(wrapper.text()).toContain('You have reached the maximum of 3 projects.')
        expect(mocks.pushMock).not.toHaveBeenCalled()
        expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeUndefined()
    })

    it('labels field errors and falls back to the error message', async () => {
        vi.spyOn(console, 'error').mockImplementation(() => {})
        mocks.createProjectMock.mockRejectedValueOnce({
            response: { data: { name: ['Ensure this field has no more than 100 characters.'] } },
        })
        const wrapper = await mountLoaded()

        await fillAndSubmit(wrapper)
        expect(wrapper.text()).toContain('Project name: Ensure this field has no more than 100 characters.')

        mocks.createProjectMock.mockRejectedValueOnce(new Error('Network Error'))
        await fillAndSubmit(wrapper)
        expect(wrapper.text()).toContain('Network Error')
    })
})
