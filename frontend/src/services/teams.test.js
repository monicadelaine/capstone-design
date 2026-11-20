import { describe, expect, it } from 'vitest'
import { studentsByProject } from './teams'

const person = (id, first, last) => ({ id, first_name: first, last_name: last, email: `${first.toLowerCase()}@crimson.ua.edu` })

describe('studentsByProject', () => {
    it('groups the students by project and sorts each team by last name, then first name', () => {
        const grouped = studentsByProject([
            { id: 'a', project: 5, student_detail: person(1, 'Zed', 'Young') },
            { id: 'b', project: 6, student_detail: person(2, 'Mia', 'Adams') },
            { id: 'c', project: 5, student_detail: person(3, 'Ann', 'Young') },
            { id: 'd', project: 5, student_detail: person(4, 'Bo', 'Able') },
        ])

        expect(Object.keys(grouped).sort()).toEqual(['5', '6'])
        expect(grouped[5].map(s => `${s.first_name} ${s.last_name}`)).toEqual(['Bo Able', 'Ann Young', 'Zed Young'])
        expect(grouped[6]).toHaveLength(1)
    })

    it('accepts a project given as an object', () => {
        const grouped = studentsByProject([{ project: { id: 9 }, student_detail: person(1, 'Ann', 'Lee') }])

        expect(grouped[9]).toHaveLength(1)
    })

    it('skips an assignment that has no student details', () => {
        expect(studentsByProject([{ project: 5, student: 1 }])).toEqual({})
    })

    it('copes with something that is not a list', () => {
        expect(studentsByProject(null)).toEqual({})
        expect(studentsByProject(undefined)).toEqual({})
        expect(studentsByProject({})).toEqual({})
    })
})
