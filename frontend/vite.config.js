import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.{test,spec}.{js,ts}'],
  },
  server: {
    host: true, // listen on all addresses (0.0.0.0) - needed for docker
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true
    },
    proxy: {
      // forward any request starting with /api to the backend container
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
