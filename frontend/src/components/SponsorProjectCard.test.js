import { shallowMount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProjectAttachments from './ProjectAttachments.vue'
import SponsorProjectCard from './SponsorProjectCard.vue'

describe('SponsorProjectCard', () => {
    const project = { id: 5, name: 'Wildlife Sighting Map', status: 'Pending', created_at: '2026-10-01T00:00:00Z' }

    it('does not load files until the details are opened', () => {
        const wrapper = shallowMount(SponsorProjectCard, { props: { project } })

        expect(wrapper.findComponent(ProjectAttachments).exists()).toBe(false)
    })

    it('lets the sponsor manage files for their own project once details are open', async () => {
        const wrapper = shallowMount(SponsorProjectCard, { props: { project } })
        await wrapper.find('.toggle-btn').trigger('click')

        const panel = wrapper.findComponent(ProjectAttachments)
        expect(panel.exists()).toBe(true)
        expect(panel.props('projectId')).toBe(5)
        expect(panel.props('canEdit')).toBe(true)
    })

    describe('assigned students (#71)', () => {
        const team = [
            { id: 1, first_name: 'Ann', last_name: 'Lee', email: 'ann@crimson.ua.edu' },
            { id: 2, first_name: 'Bo', last_name: 'Ray', email: 'bo@crimson.ua.edu' },
        ]

        it('lists each student with a link to their email, without opening the details', () => {
            const wrapper = shallowMount(SponsorProjectCard, { props: { project, students: team } })

            const rows = wrapper.findAll('.team-list li')
            expect(rows.map(r => r.find('.team-name').text())).toEqual(['Ann Lee', 'Bo Ray'])
            expect(rows[0].find('a').attributes('href')).toBe('mailto:ann@crimson.ua.edu')
            expect(rows[1].find('a').text()).toBe('bo@crimson.ua.edu')
        })

        it('says so when nobody is assigned yet', () => {
            const wrapper = shallowMount(SponsorProjectCard, { props: { project, students: [] } })

            expect(wrapper.text()).toContain('No students assigned yet.')
            expect(wrapper.find('.team-list').exists()).toBe(false)
        })

        it('does not pretend nobody is assigned when the students could not be loaded', () => {
            const wrapper = shallowMount(SponsorProjectCard, { props: { project, students: null } })

            expect(wrapper.text()).toContain('Assigned students could not be loaded.')
            expect(wrapper.text()).not.toContain('No students assigned yet.')
        })
    })
})
