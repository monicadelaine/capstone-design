import { shallowMount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProjectAttachments from './ProjectAttachments.vue'
import ProjectDetailsSidebar from './ProjectDetailsSidebar.vue'

describe('ProjectDetailsSidebar', () => {
    it('shows the project files and links to students, without edit controls', () => {
        const wrapper = shallowMount(ProjectDetailsSidebar, {
            props: { project: { id: 12, name: 'Fleet Route Optimizer', description: 'd' }, sponsorDisplay: 'Acme' },
        })

        const panel = wrapper.findComponent(ProjectAttachments)
        expect(panel.exists()).toBe(true)
        expect(panel.props('projectId')).toBe(12)
        expect(panel.props('canEdit')).toBe(false)
    })
})
