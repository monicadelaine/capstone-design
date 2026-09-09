import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import EmailForm from './EmailForm.vue'

function createJsonResponse(ok, data) {
    return {
        ok,
        headers: { get: () => 'application/json' },
        json: async () => data,
    }
}

describe('EmailForm', () => {
    beforeEach(() => {
        vi.restoreAllMocks()
        global.fetch = vi.fn()
    })

    it('submits parsed recipients and html_message when checkbox is selected', async () => {
        global.fetch.mockResolvedValueOnce(createJsonResponse(true, { status: 'ok' }))
        const wrapper = mount(EmailForm)

        const inputs = wrapper.findAll('input')
        await inputs[0].setValue('a@example.com, b@example.com')
        await inputs[1].setValue('Hello')
        await wrapper.find('textarea').setValue('<b>Body</b>')
        await wrapper.find('input[type="checkbox"]').setValue(true)
        await wrapper.find('form').trigger('submit.prevent')

        expect(global.fetch).toHaveBeenCalledTimes(1)
        const [, options] = global.fetch.mock.calls[0]
        expect(JSON.parse(options.body)).toEqual({
            subject: 'Hello',
            message: '<b>Body</b>',
            recipients: ['a@example.com', 'b@example.com'],
            html_message: '<b>Body</b>',
        })
        expect(wrapper.text()).toContain('Email sent successfully!')
    })

    it('shows server error message for non-json unsuccessful response', async () => {
        global.fetch.mockResolvedValueOnce({
            ok: false,
            headers: { get: () => 'text/plain' },
        })
        const wrapper = mount(EmailForm)

        const inputs = wrapper.findAll('input')
        await inputs[0].setValue('a@example.com')
        await inputs[1].setValue('Hello')
        await wrapper.find('textarea').setValue('Body')
        await wrapper.find('form').trigger('submit.prevent')

        expect(wrapper.text()).toContain('Server error occurred')
    })

    it('shows caught network error', async () => {
        global.fetch.mockRejectedValueOnce(new Error('Network down'))
        const wrapper = mount(EmailForm)

        const inputs = wrapper.findAll('input')
        await inputs[0].setValue('a@example.com')
        await inputs[1].setValue('Hello')
        await wrapper.find('textarea').setValue('Body')
        await wrapper.find('form').trigger('submit.prevent')

        expect(wrapper.text()).toContain('Network down')
    })
})
