import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => {
    const routeMock = { path: '/student' }
    const pushMock = vi.fn()
    const getAccessTokenSilentlyMock = vi.fn()
    const setTokenMock = vi.fn()
    const fetchProfileAndPrefsMock = vi.fn()
    const studentStoreMock = {
        hasRanked: false,
        isAssigned: false,
        isDeadlinePast: false,
        fetchProfileAndPrefs: fetchProfileAndPrefsMock,
    }

    return {
        routeMock,
        pushMock,
        getAccessTokenSilentlyMock,
        setTokenMock,
        fetchProfileAndPrefsMock,
        studentStoreMock,
    }
})

vi.mock('vue-router', () => ({
    useRouter: () => ({ push: mocks.pushMock }),
    useRoute: () => mocks.routeMock,
}))

vi.mock('@auth0/auth0-vue', () => ({
    useAuth0: () => ({ getAccessTokenSilently: mocks.getAccessTokenSilentlyMock }),
}))

vi.mock('../services/api', () => ({
    default: { setToken: mocks.setTokenMock },
}))

vi.mock('../stores/studentStore', () => ({
    useStudentStore: () => mocks.studentStoreMock,
}))

import Sidebar from './Sidebar.vue'

describe('Sidebar', () => {
    beforeEach(() => {
        mocks.pushMock.mockReset()
        mocks.getAccessTokenSilentlyMock.mockReset().mockResolvedValue('token123')
        mocks.setTokenMock.mockReset()
        mocks.fetchProfileAndPrefsMock.mockReset()
        mocks.routeMock.path = '/student'
        mocks.studentStoreMock.hasRanked = false
        mocks.studentStoreMock.isAssigned = false
        mocks.studentStoreMock.isDeadlinePast = false
    })

    it('renders student menu and submit rankings label before deadline', async () => {
        const wrapper = mount(Sidebar, {
            props: { userRole: 'student', userName: 'Alice' },
        })

        await Promise.resolve()

        expect(wrapper.text()).toContain('Dashboard')
        expect(wrapper.text()).toContain('Project Gallery')
        expect(wrapper.text()).toContain('Submit Rankings')
        expect(wrapper.text()).not.toContain('View Assignment')

        expect(mocks.getAccessTokenSilentlyMock).toHaveBeenCalled()
        expect(mocks.setTokenMock).toHaveBeenCalledWith('token123')
        expect(mocks.fetchProfileAndPrefsMock).toHaveBeenCalled()
    })

    it('renders edit rankings for student who already ranked', () => {
        mocks.studentStoreMock.hasRanked = true
        const wrapper = mount(Sidebar, {
            props: { userRole: 'student', userName: 'Alice' },
        })

        expect(wrapper.text()).toContain('Edit Rankings')
    })

    it('renders assignment link only after deadline when assigned', () => {
        mocks.studentStoreMock.isDeadlinePast = true
        mocks.studentStoreMock.isAssigned = true
        const wrapper = mount(Sidebar, {
            props: { userRole: 'student', userName: 'Alice' },
        })

        expect(wrapper.text()).toContain('View Assignment')
        expect(wrapper.text()).not.toContain('Submit Rankings')
    })

    it('renders sponsor menu and edit profile action', () => {
        const wrapper = mount(Sidebar, {
            props: { userRole: 'sponsor', userName: 'Sponsor User' },
        })

        expect(wrapper.text()).toContain('Submit Project')
        expect(wrapper.text()).toContain('Edit Project')
        expect(wrapper.text()).toContain('Submit Feedback')
        expect(wrapper.text()).toContain('Edit Profile')
        expect(mocks.getAccessTokenSilentlyMock).not.toHaveBeenCalled()
    })

    it('navigates on nav item click and emits logout', async () => {
        const wrapper = mount(Sidebar, {
            props: { userRole: 'sponsor', userName: 'Sponsor User' },
        })

        const navItems = wrapper.findAll('.nav-item')
        await navItems[1].trigger('click')
        expect(mocks.pushMock).toHaveBeenCalledWith('/sponsor/submit')

        await wrapper.find('.logout-link').trigger('click')
        expect(wrapper.emitted('logout')).toHaveLength(1)
    })
})
