import { defineStore } from 'pinia'
import apiService from '../services/api'

export const useProjectsStore = defineStore('projects', {
  state: () => ({
    projects: [],
    projectsLoaded: false,
    loading: false,
    error: null
  }),
  actions: {
    async fetchProjects() {
      if (this.projectsLoaded) return
      this.loading = true
      this.error = null
      try {
        const res = await apiService.client.get('/projects/?format=json')
        this.projects = res.data
        this.projectsLoaded = true
      } catch (e) {
        this.error = e
        console.error('projectsStore.fetchProjects error', e)
        throw e
      } finally {
        this.loading = false
      }
    },
    clear() {
      this.projects = []
      this.projectsLoaded = false
      this.loading = false
      this.error = null
    }
  }
})
