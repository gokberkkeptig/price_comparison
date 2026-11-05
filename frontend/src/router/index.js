import { route } from 'quasar/wrappers'
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('../pages/IndexPage.vue'),
      },
      {
        path: 'product/:id',
        name: 'product-detail',
        component: () => import('../pages/ProductDetail.vue'),
        props: true,
      },
      {
        path: 'compare',
        name: 'compare',
        component: () => import('../pages/ComparePage.vue'),
      },
      {
        path: 'checkout',
        name: 'checkout',
        component: () => import('../pages/CheckoutPage.vue'),
      },
      {
        path: 'receipt',
        name: 'receipt',
        component: () => import('../pages/ReceiptScan.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'login',
        name: 'login',
        component: () => import('../pages/LoginPage.vue'),
        meta: { guest: true },
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('../pages/RegisterPage.vue'),
        meta: { guest: true },
      },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('../pages/ErrorNotFound.vue'),
  },
]

export default route(function (/* { store, ssrContext } */) {
  const Router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior() {
      return { top: 0 }
    },
  })

  // Navigation guards
  Router.beforeEach((to, _from, next) => {
    const auth = useAuthStore()

    if (to.meta.requiresAuth && !auth.isLoggedIn) {
      next({ name: 'login', query: { redirect: to.fullPath } })
    } else if (to.meta.guest && auth.isLoggedIn) {
      next({ name: 'home' })
    } else {
      next()
    }
  })

  return Router
})
