import { defineStore } from 'pinia'
import { api } from '../boot/axios'
import { Notify } from 'quasar'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    user: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
  },

  actions: {
    async login(login, password) {
      try {
        const { data } = await api.post('/auth/login', { login, password })
        this.token = data.token
        this.user = data.user
        localStorage.setItem('token', data.token)
        Notify.create({ type: 'positive', message: 'Accesso eseguito con successo' })
        return true
      } catch (err) {
        const message = err.response?.data?.error || 'Errore durante il login'
        Notify.create({ type: 'negative', message })
        return false
      }
    },

    async register(username, email, password) {
      try {
        const { data } = await api.post('/auth/register', { username, email, password })
        this.token = data.token
        this.user = data.user
        localStorage.setItem('token', data.token)
        Notify.create({ type: 'positive', message: 'Registrazione completata!' })
        return true
      } catch (err) {
        const message = err.response?.data?.error || 'Errore durante la registrazione'
        Notify.create({ type: 'negative', message })
        return false
      }
    },

    async fetchMe() {
      if (!this.token) return
      try {
        const { data } = await api.get('/auth/me')
        this.user = data.user
      } catch {
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      Notify.create({ type: 'info', message: 'Logout effettuato' })
    },

    // Restore session from localStorage on app start
    init() {
      const token = localStorage.getItem('token')
      if (token) {
        this.token = token
        this.fetchMe()
      }
    },
  },

  persist: {
    paths: ['token', 'user'],
  },
})
