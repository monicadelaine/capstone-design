import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiMock = vi.hoisted(() => ({
    getProfile: vi.fn(),
    client: {
        get: vi.fn(),
    },
}))

vi.mock('../services/api', () => ({
    default: apiMock,
}))

import { useStudentStore } from './studentStore'

describe('studentStore', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        apiMock.getProfile.mockReset()
        apiMock.client.get.mockReset()
    })

    it('computes getter values from preferences and assignment', () => {
        const store = useStudentStore()
        store.preferences = [{ project: 5 }, { project: { id: 6 } }]
        store.assignment = { project: { id: 99 } }
        store.assignmentDate = '2100-01-01T00:00:00Z'

        expect(store.existingPrefProjectIds).toEqual(['5', '6'])
        expect(store.assignedProjectId).toBe('99')
        expect(store.isDeadlinePast).toBe(false)
    })

    it('handles profile without student id', async () => {
        const store = useStudentStore()
        apiMock.getProfile.mockResolvedValueOnce({ data: { type: 'student', id: null } })

        await store.fetchProfileAndPrefs()

        expect(store.profile).toEqual({ type: 'student', id: null })
        expect(store.preferences).toEqual([])
        expect(store.hasRanked).toBe(false)
        expect(store.isAssigned).toBe(false)
        expect(store.assignment).toBe(null)
    })

    it('loads preferences, assignment, and semester', async () => {
        const store = useStudentStore()
        apiMock.getProfile.mockResolvedValueOnce({ data: { id: 10, type: 'student' } })
        apiMock.client.get
            .mockResolvedValueOnce({
                data: [
                    { id: '1', student: 10, project: 2 },
                    { id: '2', student: { id: 11 }, project: 3 },
                ],
            })
            .mockResolvedValueOnce({
                data: [{ id: 'a1', student: 10, project: 2 }],
            })
            .mockResolvedValueOnce({
                data: { id: 7, assignment_date: '2099-01-01T00:00:00Z' },
            })

        await store.fetchProfileAndPrefs()

        expect(store.preferences).toEqual([{ id: '1', student: 10, project: 2 }])
        expect(store.hasRanked).toBe(true)
        expect(store.isAssigned).toBe(true)
        expect(store.assignment).toEqual({ id: 'a1', student: 10, project: 2 })
        expect(store.currentSemester).toEqual({ id: 7, assignment_date: '2099-01-01T00:00:00Z' })
        expect(store.assignmentDate).toBe('2099-01-01T00:00:00Z')
    })

    it('falls back when assignment or semester fetch fails', async () => {
        const store = useStudentStore()
        apiMock.getProfile.mockResolvedValueOnce({ data: { id: 10, type: 'student' } })
        apiMock.client.get
            .mockResolvedValueOnce({ data: [] })
            .mockRejectedValueOnce(new Error('assignments fail'))
            .mockRejectedValueOnce(new Error('semester fail'))

        await store.fetchProfileAndPrefs()

        expect(store.isAssigned).toBe(false)
        expect(store.assignment).toBe(null)
        expect(store.currentSemester).toBe(null)
        expect(store.assignmentDate).toBe(null)
    })

    it('stores and rethrows top-level fetch errors', async () => {
        const store = useStudentStore()
        const err = new Error('profile failed')
        apiMock.getProfile.mockRejectedValueOnce(err)

        await expect(store.fetchProfileAndPrefs()).rejects.toThrow('profile failed')
        expect(store.error).toBe(err)
        expect(store.loading).toBe(false)
    })

    it('clear resets all state', () => {
        const store = useStudentStore()
        store.profile = { id: 1 }
        store.preferences = [{ id: 1 }]
        store.hasRanked = true
        store.isAssigned = true
        store.assignment = { id: 'a' }
        store.currentSemester = { id: 1 }
        store.assignmentDate = 'x'
        store.loading = true
        store.error = new Error('x')

        store.clear()

        expect(store.profile).toBe(null)
        expect(store.preferences).toEqual([])
        expect(store.hasRanked).toBe(false)
        expect(store.isAssigned).toBe(false)
        expect(store.assignment).toBe(null)
        expect(store.currentSemester).toBe(null)
        expect(store.assignmentDate).toBe(null)
        expect(store.loading).toBe(false)
        expect(store.error).toBe(null)
    })
})
