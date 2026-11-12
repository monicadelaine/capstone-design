import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@auth0/auth0-vue', () => ({
    useAuth0: () => ({ getAccessTokenSilently: vi.fn().mockResolvedValue('test-token') }),
}))

vi.mock('../services/api', () => {
    const apiService = {
        setToken: vi.fn(),
        getAttachments: vi.fn(),
        uploadAttachment: vi.fn(),
        addAttachmentLink: vi.fn(),
        deleteAttachment: vi.fn(),
        downloadAttachment: vi.fn(),
    }
    return { default: apiService, apiService }
})

import apiService from '../services/api'
import ProjectAttachments from './ProjectAttachments.vue'

const pdf = {
    id: 1, project: 7, file: '7/0123456789abcdef.pdf', link: null, original_filename: 'Project Spec.pdf',
    content: null, created_at: '2026-11-01T12:00:00Z',
}
const link = {
    id: 2, project: 7, file: null, link: 'https://example.com/brief', original_filename: '',
    content: null, created_at: '2026-11-02T12:00:00Z',
}

async function mountPanel(props = {}, rows = [pdf, link]) {
    apiService.getAttachments.mockResolvedValue(rows)
    const wrapper = mount(ProjectAttachments, { props: { projectId: 7, ...props } })
    await flushPromises()
    return wrapper
}

function chooseFile(wrapper, file) {
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [file], configurable: true })
    return input.trigger('change')
}

describe('ProjectAttachments', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    describe('listing', () => {
        it('lists files by their original name and links as anchors', async () => {
            const wrapper = await mountPanel()

            expect(apiService.getAttachments).toHaveBeenCalledWith(7)
            expect(wrapper.text()).toContain('Project Spec.pdf')
            expect(wrapper.text()).not.toContain('0123456789abcdef')
            const anchor = wrapper.find('a[href="https://example.com/brief"]')
            expect(anchor.exists()).toBe(true)
            expect(anchor.attributes('rel')).toContain('noopener')
            expect(anchor.attributes('target')).toBe('_blank')
        })

        it('hides rows that only hold exported email text', async () => {
            const wrapper = await mountPanel({}, [{ id: 3, project: null, file: null, link: null, content: 'Subject: x' }])

            expect(wrapper.text()).toContain('No files or links yet.')
        })

        it('does not turn a non-http link into an anchor', async () => {
            const wrapper = await mountPanel({}, [{ ...link, link: 'javascript:alert(1)' }])

            expect(wrapper.find('a').exists()).toBe(false)
        })

        it('shows an error when the list cannot be loaded', async () => {
            apiService.getAttachments.mockRejectedValue(new Error('boom'))
            const wrapper = mount(ProjectAttachments, { props: { projectId: 7 } })
            await flushPromises()

            expect(wrapper.find('[role="alert"]').text()).toContain('Could not load')
        })

        it('reloads when the project changes', async () => {
            const wrapper = await mountPanel()
            await wrapper.setProps({ projectId: 8 })
            await flushPromises()

            expect(apiService.getAttachments).toHaveBeenLastCalledWith(8)
        })
    })

    describe('read-only view', () => {
        it('offers download but no upload, link or remove controls', async () => {
            const wrapper = await mountPanel({ canEdit: false })

            expect(wrapper.text()).toContain('Download')
            expect(wrapper.find('input[type="file"]').exists()).toBe(false)
            expect(wrapper.find('input[type="url"]').exists()).toBe(false)
            expect(wrapper.text()).not.toContain('Remove')
        })
    })

    describe('uploading', () => {
        it('rejects a disallowed file type without calling the server', async () => {
            const wrapper = await mountPanel({ canEdit: true })
            await chooseFile(wrapper, new File(['x'], 'run.exe'))
            await wrapper.find('form').trigger('submit')

            expect(wrapper.find('[role="alert"]').text()).toContain('not allowed')
            expect(apiService.uploadAttachment).not.toHaveBeenCalled()
        })

        it('rejects a file over 25 MB without calling the server', async () => {
            const wrapper = await mountPanel({ canEdit: true })
            const big = new File(['x'], 'deck.pptx')
            Object.defineProperty(big, 'size', { value: 25 * 1024 * 1024 + 1 })
            await chooseFile(wrapper, big)
            await wrapper.find('form').trigger('submit')

            expect(wrapper.find('[role="alert"]').text()).toContain('25 MB')
            expect(apiService.uploadAttachment).not.toHaveBeenCalled()
        })

        it('asks for a file when none is chosen', async () => {
            const wrapper = await mountPanel({ canEdit: true })
            await wrapper.find('form').trigger('submit')

            expect(wrapper.find('[role="alert"]').text()).toContain('Choose a file')
        })

        it('uploads a valid file and refreshes the list', async () => {
            apiService.uploadAttachment.mockResolvedValue({ id: 9 })
            const wrapper = await mountPanel({ canEdit: true })
            const file = new File(['%PDF'], 'Spec.PDF')
            await chooseFile(wrapper, file)
            await wrapper.find('form').trigger('submit')
            await flushPromises()

            expect(apiService.uploadAttachment).toHaveBeenCalledWith(7, file)
            expect(apiService.getAttachments).toHaveBeenCalledTimes(2)
            expect(wrapper.find('[role="status"]').text()).toContain('Uploaded Spec.PDF')
        })

        it('shows the message the server sends back', async () => {
            apiService.uploadAttachment.mockRejectedValue({ response: { status: 400, data: { file: ['File size must be 25 MB or less.'] } } })
            const wrapper = await mountPanel({ canEdit: true })
            await chooseFile(wrapper, new File(['x'], 'a.pdf'))
            await wrapper.find('form').trigger('submit')
            await flushPromises()

            expect(wrapper.find('[role="alert"]').text()).toBe('File size must be 25 MB or less.')
        })

        it('explains a 413 from the proxy', async () => {
            apiService.uploadAttachment.mockRejectedValue({ response: { status: 413, data: '<html>' } })
            const wrapper = await mountPanel({ canEdit: true })
            await chooseFile(wrapper, new File(['x'], 'a.pdf'))
            await wrapper.find('form').trigger('submit')
            await flushPromises()

            expect(wrapper.find('[role="alert"]').text()).toContain('too large for the server')
        })
    })

    describe('adding a link', () => {
        it('rejects text that is not an http(s) link', async () => {
            const wrapper = await mountPanel({ canEdit: true })
            await wrapper.find('input[type="url"]').setValue('javascript:alert(1)')
            await wrapper.findAll('form')[1].trigger('submit')

            expect(wrapper.find('[role="alert"]').text()).toContain('http')
            expect(apiService.addAttachmentLink).not.toHaveBeenCalled()
        })

        it('adds a valid link, trimmed, and refreshes the list', async () => {
            apiService.addAttachmentLink.mockResolvedValue({ id: 10 })
            const wrapper = await mountPanel({ canEdit: true })
            await wrapper.find('input[type="url"]').setValue('  https://example.com/doc  ')
            await wrapper.findAll('form')[1].trigger('submit')
            await flushPromises()

            expect(apiService.addAttachmentLink).toHaveBeenCalledWith(7, 'https://example.com/doc')
            expect(apiService.getAttachments).toHaveBeenCalledTimes(2)
            expect(wrapper.find('input[type="url"]').element.value).toBe('')
        })
    })

    describe('downloading', () => {
        it('fetches the file with the token and saves it under its original name', async () => {
            const blob = new Blob(['%PDF'])
            apiService.downloadAttachment.mockResolvedValue(blob)
            const createUrl = vi.fn(() => 'blob:test')
            const revokeUrl = vi.fn()
            vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: createUrl, revokeObjectURL: revokeUrl }))
            const saved = []
            const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () { saved.push(this.download) })

            const wrapper = await mountPanel()
            await wrapper.findAll('button').find((b) => b.text() === 'Download').trigger('click')
            await flushPromises()

            expect(apiService.downloadAttachment).toHaveBeenCalledWith(1)
            expect(createUrl).toHaveBeenCalledWith(blob)
            expect(saved).toEqual(['Project Spec.pdf'])
            expect(revokeUrl).toHaveBeenCalledWith('blob:test')
            click.mockRestore()
            vi.unstubAllGlobals()
        })

        it('shows an error when the download fails', async () => {
            apiService.downloadAttachment.mockRejectedValue(new Error('403'))
            const wrapper = await mountPanel()
            await wrapper.findAll('button').find((b) => b.text() === 'Download').trigger('click')
            await flushPromises()

            expect(wrapper.find('[role="alert"]').text()).toContain('Could not download')
        })
    })

    describe('removing', () => {
        it('asks first, then removes and refreshes', async () => {
            apiService.deleteAttachment.mockResolvedValue()
            const wrapper = await mountPanel({ canEdit: true })

            await wrapper.findAll('button').find((b) => b.text() === 'Remove').trigger('click')
            expect(wrapper.find('.overlay').exists()).toBe(true)
            expect(apiService.deleteAttachment).not.toHaveBeenCalled()

            await wrapper.findAll('.overlay button')[1].trigger('click')
            await flushPromises()

            expect(apiService.deleteAttachment).toHaveBeenCalledWith(1)
            expect(apiService.getAttachments).toHaveBeenCalledTimes(2)
        })

        it('does nothing when the confirmation is cancelled', async () => {
            const wrapper = await mountPanel({ canEdit: true })

            await wrapper.findAll('button').find((b) => b.text() === 'Remove').trigger('click')
            await wrapper.find('.overlay .btn-cancel').trigger('click')

            expect(apiService.deleteAttachment).not.toHaveBeenCalled()
            expect(wrapper.find('.overlay').exists()).toBe(false)
        })
    })
})
