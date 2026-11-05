import { createApp } from 'vue'
import { Quasar, Notify, Dialog, Loading, LocalStorage } from 'quasar'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

// Import icon libraries
import '@quasar/extras/roboto-font/roboto-font.css'
import '@quasar/extras/material-icons/material-icons.css'

// Import Quasar css
import 'quasar/src/css/index.sass'

// App-specific css
import './css/app.scss'

import App from './App.vue'
import router from './router'

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(Quasar, {
  plugins: { Notify, Dialog, Loading, LocalStorage },
  config: {
    brand: {
      primary: '#1B5E20',
      secondary: '#43A047',
      accent: '#FF6F00',
    },
    notify: {
      position: 'top-right',
      timeout: 3000,
    },
  },
})

app.use(pinia)
app.use(router)

app.mount('#q-app')
