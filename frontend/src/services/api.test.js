import { beforeEach, describe, expect, it, vi } from 'vitest'

async function loadApiWithClient(fakeClient) {
    vi.resetModules()
    vi.doMock('axios', () => ({
        default: {
            create: vi.fn(() => fakeClient),
        },
    }))
    return import('./api')
}

describe('apiService', () => {
    let fakeClient

    beforeEach(() => {
        fakeClient = {
            defaults: { headers: { common: {} } },
            get: vi.fn(),
            post: vi.fn(),
            put: vi.fn(),
            delete: vi.fn(),
        }
    })

    it('sets and clears bearer token header', async () => {
        const { apiService } = await loadApiWithClient(fakeClient)

        apiService.setToken('abc123')
        expect(fakeClient.defaults.headers.common.Authorization).toBe('Bearer abc123')

        apiService.clearToken()
        expect(fakeClient.defaults.headers.common.Authorization).toBeUndefined()
    })

    it('returns data from profile endpoints', async () => {
        const { apiService } = await loadApiWithClient(fakeClient)
        fakeClient.get.mockResolvedValueOnce({ data: { id: 1 } })
        fakeClient.post.mockResolvedValueOnce({ data: { id: 2 } })
        fakeClient.put.mockResolvedValueOnce({ data: { id: 3 } })

        await expect(apiService.getProfile()).resolves.toEqual({ id: 1 })
        await expect(apiService.createProfile({ a: 1 })).resolves.toEqual({ id: 2 })
        await expect(apiService.updateProfile({ a: 1 })).resolves.toEqual({ id: 3 })
    })

    it('builds sponsor project URL with optional semester query', async () => {
        const { apiService } = await loadApiWithClient(fakeClient)
        fakeClient.get.mockResolvedValue({ data: [] })

        await apiService.getProjectsBySponsor(10)
        await apiService.getProjectsBySponsor(10, 3)

        expect(fakeClient.get).toHaveBeenNthCalledWith(1, '/sponsors/10/projects/')
        expect(fakeClient.get).toHaveBeenNthCalledWith(2, '/sponsors/10/projects/?semester_id=3')
    })

    it('normalizes student response into minimal shape', async () => {
        const { apiService } = await loadApiWithClient(fakeClient)
        fakeClient.get.mockResolvedValueOnce({
            data: {
                id: 7,
                first_name: 'Ada',
                last_name: 'Lovelace',
                extra: 'ignore',
            },
        })

        await expect(apiService.getStudent(7)).resolves.toEqual({
            id: 7,
            first_name: 'Ada',
            last_name: 'Lovelace',
            name: 'Ada Lovelace',
        })
    })

    it('returns map for getStudents and tolerates failed student fetches', async () => {
        const { apiService } = await loadApiWithClient(fakeClient)
        vi.spyOn(apiService, 'getStudent')
            .mockResolvedValueOnce({ id: 1, first_name: 'A', last_name: null, name: 'A' })
            .mockRejectedValueOnce(new Error('boom'))

        const map = await apiService.getStudents([1, 2, 1, null])

        expect(map).toEqual({
            '1': { id: 1, first_name: 'A', last_name: null, name: 'A' },
            '2': null,
        })
    })
    describe('attachments', () => {
        it('lists the attachments of one project', async () => {
            const { apiService } = await loadApiWithClient(fakeClient)
            fakeClient.get.mockResolvedValueOnce({ data: [{ id: 1 }] })

            await expect(apiService.getAttachments(7)).resolves.toEqual([{ id: 1 }])
            expect(fakeClient.get).toHaveBeenCalledWith('/attachments/', { params: { project: 7 } })
        })

        it('uploads a file as multipart form data', async () => {
            const { apiService } = await loadApiWithClient(fakeClient)
            fakeClient.post.mockResolvedValueOnce({ data: { id: 2 } })
            const file = new File(['%PDF'], 'spec.pdf')

            await expect(apiService.uploadAttachment(7, file)).resolves.toEqual({ id: 2 })

            const [url, body, config] = fakeClient.post.mock.calls[0]
            expect(url).toBe('/attachments/')
            expect(body).toBeInstanceOf(FormData)
            expect(body.get('project')).toBe('7')
            expect(body.get('file')).toBe(file)
            expect(config.headers['Content-Type']).toBe('multipart/form-data')
        })

        it('adds a link to a project', async () => {
            const { apiService } = await loadApiWithClient(fakeClient)
            fakeClient.post.mockResolvedValueOnce({ data: { id: 3 } })

            await apiService.addAttachmentLink(7, 'https://example.com')

            expect(fakeClient.post).toHaveBeenCalledWith('/attachments/', { project: 7, link: 'https://example.com' })
        })

        it('deletes an attachment', async () => {
            const { apiService } = await loadApiWithClient(fakeClient)
            fakeClient.delete.mockResolvedValueOnce({})

            await apiService.deleteAttachment(4)

            expect(fakeClient.delete).toHaveBeenCalledWith('/attachments/4/')
        })

        it('downloads a file as a blob through the authenticated client', async () => {
            const { apiService } = await loadApiWithClient(fakeClient)
            const blob = new Blob(['x'])
            fakeClient.get.mockResolvedValueOnce({ data: blob })

            await expect(apiService.downloadAttachment(4)).resolves.toBe(blob)
            expect(fakeClient.get).toHaveBeenCalledWith('/attachments/4/download/', { responseType: 'blob' })
        })
    })
})
