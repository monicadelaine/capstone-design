import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ProjectPresentation from './ProjectPresentation.vue'

function createJsonResponse(ok, data) {
    return {
        ok,
        headers: { get: () => 'application/json' },
        json: async () => data,
    }
}

describe('ProjectPresentation', () => {
    beforeEach(() => {
        vi.restoreAllMocks()
        global.fetch = vi.fn()
    })

    it('requires recipients', async () => {
        const wrapper = mount(ProjectPresentation)

        await wrapper.find('form').trigger('submit.prevent')

        expect(global.fetch).not.toHaveBeenCalled()
        expect(wrapper.text()).toContain('Please enter at least one email address')
    })

    it('submits payload with optional from_email and clears form on success', async () => {
        global.fetch.mockResolvedValueOnce(createJsonResponse(true, { status: 'ok' }))
        const wrapper = mount(ProjectPresentation)

        const inputs = wrapper.findAll('input')
        await inputs[0].setValue('sponsor@example.com')
        await inputs[1].setValue('2026-10-10')
        await inputs[2].setValue('10:00 AM')
        await inputs[3].setValue('Design Manager')
        const textareas = wrapper.findAll('textarea')
        await textareas[0].setValue('Project description')
        await inputs[4].setValue('Dr. Ada')
        await inputs[5].setValue('ada@example.com')
        await textareas[1].setValue('https://zoom.us/j/123')
        await inputs[6].setValue('faculty@example.com')

        await wrapper.find('form').trigger('submit.prevent')

        const [, options] = global.fetch.mock.calls[0]
        expect(JSON.parse(options.body)).toEqual({
            recipients: 'sponsor@example.com',
            date: '2026-10-10',
            time: '10:00 AM',
            project_name: 'Design Manager',
            project_description: 'Project description',
            contact_name: 'Dr. Ada',
            contact_email: 'ada@example.com',
            zoom_details: 'https://zoom.us/j/123',
            from_email: 'faculty@example.com',
        })
        expect(wrapper.text()).toContain('Project presentation email sent successfully!')
        expect(wrapper.findAll('input')[0].element.value).toBe('')
    })

    it('shows server-side error payload when response is not ok', async () => {
        global.fetch.mockResolvedValueOnce(createJsonResponse(false, { error: 'bad request' }))
        const wrapper = mount(ProjectPresentation)

        await wrapper.findAll('input')[0].setValue('sponsor@example.com')
        await wrapper.find('form').trigger('submit.prevent')

        expect(wrapper.text()).toContain('{"error":"bad request"}')
    })
})
