/* eslint-env node */
import { configure } from 'quasar/wrappers'

export default configure(function (/* ctx */) {
  return {
    boot: ['pinia-persist', 'axios'],

    css: ['app.scss'],

    extras: [
      'roboto-font',
      'material-icons',
    ],

    build: {
      target: { browser: ['es2022', 'firefox115', 'chrome115', 'safari14'] },
      vueRouterMode: 'history',
      env: {
        API_URL: process.env.API_URL || 'http://localhost:5000/api',
      },
    },

    devServer: {
      port: 9000,
      open: false,
    },

    framework: {
      config: {
        brand: {
          primary: '#1B5E20',
          secondary: '#43A047',
          accent: '#FF6F00',
          dark: '#1d1d1d',
          positive: '#4CAF50',
          negative: '#E53935',
          info: '#2196F3',
          warning: '#FFC107',
        },
        notify: {
          position: 'top-right',
          timeout: 3000,
        },
      },
      plugins: ['Notify', 'Dialog', 'Loading', 'LocalStorage'],
    },

    animations: [],

    ssr: { pwa: false },
    pwa: {},
    capacitor: {},
    electron: {},
  }
})
