/**
 * API service — wraps axios calls for all backend endpoints.
 */
import { api } from '../boot/axios'

// Products
export function fetchProducts(params = {}) {
  return api.get('/products', { params })
}

export function fetchProduct(id) {
  return api.get(`/products/${id}`)
}

// Filters
export function fetchCategories() {
  return api.get('/products/categories')
}

export function fetchStores() {
  return api.get('/products/stores')
}

export function fetchLocations() {
  return api.get('/products/locations')
}

// Compare
export function compareProducts(ids) {
  return api.get('/compare', { params: { ids: ids.join(',') } })
}

// Cart
export function calculateCart(cart) {
  return api.post('/cart/calculate', { cart })
}

// Receipt
export function scanReceipt(imageBase64) {
  return api.post('/receipt/scan', { image: imageBase64 })
}

export function confirmReceipt(receiptData) {
  return api.post('/receipt/confirm', receiptData)
}

// Auth — handled by the store directly, but exposed here for flexibility
export function login(login, password) {
  return api.post('/auth/login', { login, password })
}

export function register(username, email, password) {
  return api.post('/auth/register', { username, email, password })
}

export function getMe() {
  return api.get('/auth/me')
}
