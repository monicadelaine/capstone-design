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
})
