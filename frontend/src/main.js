import { createApp } from 'vue'
import { createAuth0 } from '@auth0/auth0-vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { plugin, defaultConfig } from '@formkit/vue'
import '@formkit/themes/genesis'
import { createPinia } from 'pinia'

const auth0 = createAuth0({
        domain: import.meta.env.VITE_AUTH0_DOMAIN,
        clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
        authorizationParams: {
                redirect_uri: window.location.origin,
                audience: import.meta.env.VITE_AUTH0_AUDIENCE
        },
        onRedirectCallback: (appState) => {
                // Just send them back to the root; the Login.vue watcher will redirect by role
                router.push(appState?.returnTo ?? '/');
        }
})

const app = createApp(App)

const pinia = createPinia()
app.use(auth0)
app.use(router)
app.use(pinia)
app.use(plugin, defaultConfig)

app.mount('#app')

export { auth0 }
