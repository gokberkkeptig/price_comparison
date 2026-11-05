import { defineStore } from 'pinia'
import { Notify } from 'quasar'

const MAX_COMPARE = 6

export const useCompareStore = defineStore('compare', {
  state: () => ({
    ids: [],
  }),

  getters: {
    count: (state) => state.ids.length,
    isEmpty: (state) => state.ids.length === 0,
    isFull: (state) => state.ids.length >= MAX_COMPARE,
    has: (state) => (id) => state.ids.includes(id),
  },

  actions: {
    toggle(id) {
      const idx = this.ids.indexOf(id)
      if (idx >= 0) {
        this.ids.splice(idx, 1)
      } else {
        if (this.ids.length >= MAX_COMPARE) {
          Notify.create({
            type: 'warning',
            message: `Puoi confrontare al massimo ${MAX_COMPARE} prodotti`,
          })
          return
        }
        this.ids.push(id)
      }
    },

    remove(id) {
      const idx = this.ids.indexOf(id)
      if (idx >= 0) this.ids.splice(idx, 1)
    },

    clear() {
      this.ids = []
    },
  },

  persist: true,
})
