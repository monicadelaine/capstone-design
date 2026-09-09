import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ConfirmationModal from './ConfirmationModal.vue'

describe('ConfirmationModal', () => {
    it('does not render when show is false', () => {
        const wrapper = mount(ConfirmationModal, {
            props: { show: false },
        })

        expect(wrapper.find('.overlay').exists()).toBe(false)
    })

    it('renders title and message when visible', () => {
        const wrapper = mount(ConfirmationModal, {
            props: {
                show: true,
                title: 'Delete Project',
                message: 'Are you sure?',
            },
        })

        expect(wrapper.text()).toContain('Delete Project')
        expect(wrapper.text()).toContain('Are you sure?')
    })

    it('emits cancel and confirm events', async () => {
        const wrapper = mount(ConfirmationModal, {
            props: { show: true },
        })

        await wrapper.find('.btn-cancel').trigger('click')
        await wrapper.findAll('button')[1].trigger('click')

        expect(wrapper.emitted('cancel')).toHaveLength(1)
        expect(wrapper.emitted('confirm')).toHaveLength(1)
    })
})
