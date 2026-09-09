import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import SponsorOutreach from './SponsorOutreach.vue'

function createJsonResponse(ok, data) {
    return {
        ok,
        headers: { get: () => 'application/json' },
        json: async () => data,
    }
}

describe('SponsorOutreach', () => {
    beforeEach(() => {
        vi.restoreAllMocks()
        global.fetch = vi.fn()
    })

    it('requires recipients before submit', async () => {
        const wrapper = mount(SponsorOutreach)

        await wrapper.find('form').trigger('submit.prevent')

        expect(global.fetch).not.toHaveBeenCalled()
        expect(wrapper.text()).toContain('Please enter at least one email address')
    })

    it('submits payload and clears recipients on success', async () => {
        global.fetch.mockResolvedValueOnce(createJsonResponse(true, { status: 'ok' }))
        const wrapper = mount(SponsorOutreach)

        const textInputs = wrapper.findAll('input')
        await textInputs[0].setValue('a@example.com, b@example.com')
        await wrapper.find('select').setValue('fall')
        await textInputs[1].setValue('Fall 2026 (9/20/26)')
        await textInputs[2].setValue('sender@example.com')
        await wrapper.find('form').trigger('submit.prevent')

        const [, options] = global.fetch.mock.calls[0]
        expect(JSON.parse(options.body)).toEqual({
            recipients: 'a@example.com, b@example.com',
            semester: 'fall',
            collection_date: 'Fall 2026 (9/20/26)',
            from_email: 'sender@example.com',
        })
        expect(wrapper.text()).toContain('Sponsor outreach email sent successfully!')
        expect(wrapper.findAll('input')[0].element.value).toBe('')
    })
})
