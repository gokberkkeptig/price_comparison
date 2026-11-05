import { defineStore } from 'pinia'
import { Notify } from 'quasar'

export const useCartStore = defineStore('cart', {
  state: () => ({
    // { [product_id]: { quantity, name, image_url, min_price } }
    items: {},
  }),

  getters: {
    totalItems(state) {
      return Object.values(state.items).reduce((sum, item) => sum + item.quantity, 0)
    },

    cartList(state) {
      return Object.entries(state.items).map(([id, item]) => ({
        product_id: parseInt(id),
        ...item,
      }))
    },

    // Cart as { product_id: quantity } for the API
    cartPayload(state) {
      const payload = {}
      for (const [id, item] of Object.entries(state.items)) {
        payload[id] = item.quantity
      }
      return payload
    },

    isEmpty(state) {
      return Object.keys(state.items).length === 0
    },
  },

  actions: {
    addItem(product) {
      const id = String(product.product_id)
      if (this.items[id]) {
        this.items[id].quantity += 1
      } else {
        this.items[id] = {
          quantity: 1,
          name: product.name,
          image_url: product.image_url,
          min_price: product.min_price || null,
        }
      }
      Notify.create({
        type: 'positive',
        message: `${product.name} aggiunto al carrello`,
        icon: 'shopping_cart',
      })
    },

    removeItem(productId) {
      const id = String(productId)
      delete this.items[id]
    },

    updateQuantity(productId, quantity) {
      const id = String(productId)
      if (this.items[id]) {
        if (quantity <= 0) {
          delete this.items[id]
        } else {
          this.items[id].quantity = quantity
        }
      }
    },

    clearCart() {
      this.items = {}
      Notify.create({ type: 'info', message: 'Carrello svuotato' })
    },
  },

  persist: true,
})
