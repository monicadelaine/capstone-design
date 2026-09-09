import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiMock = vi.hoisted(() => ({
    client: {
        get: vi.fn(),
    },
}))

vi.mock('../services/api', () => ({
    default: apiMock,
}))

import { useProjectsStore } from './projectsStore'

describe('projectsStore', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        apiMock.client.get.mockReset()
    })

    it('fetches projects once and marks loaded', async () => {
        const store = useProjectsStore()
        apiMock.client.get.mockResolvedValueOnce({ data: [{ id: 1, name: 'A' }] })

        await store.fetchProjects()

        expect(apiMock.client.get).toHaveBeenCalledWith('/projects/?format=json')
        expect(store.projects).toEqual([{ id: 1, name: 'A' }])
        expect(store.projectsLoaded).toBe(true)
        expect(store.loading).toBe(false)
    })

    it('does not refetch when already loaded', async () => {
        const store = useProjectsStore()
        store.projectsLoaded = true

        await store.fetchProjects()

        expect(apiMock.client.get).not.toHaveBeenCalled()
    })

    it('captures error and rethrows fetch failures', async () => {
        const store = useProjectsStore()
        const err = new Error('request failed')
        apiMock.client.get.mockRejectedValueOnce(err)

        await expect(store.fetchProjects()).rejects.toThrow('request failed')
        expect(store.error).toBe(err)
        expect(store.loading).toBe(false)
    })

    it('clear resets the store state', () => {
        const store = useProjectsStore()
        store.projects = [{ id: 1 }]
        store.projectsLoaded = true
        store.loading = true
        store.error = new Error('x')

        store.clear()

        expect(store.projects).toEqual([])
        expect(store.projectsLoaded).toBe(false)
        expect(store.loading).toBe(false)
        expect(store.error).toBe(null)
    })
})
