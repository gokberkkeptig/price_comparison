<template>
  <q-layout view="hHh lpR fFf">
    <!-- Header -->
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="leftDrawerOpen = !leftDrawerOpen"
          class="lt-md"
        />

        <q-toolbar-title>
          <q-btn flat no-caps to="/" class="text-h6 text-white" label="🛒 Prezzi Spesa" />
        </q-toolbar-title>

        <!-- Desktop nav links -->
        <div class="gt-sm row items-center q-gutter-sm">
          <q-btn flat no-caps to="/" label="Home" icon="home" />
          <q-btn
            flat
            no-caps
            label="Confronta"
            icon="compare_arrows"
            @click="goToCompare"
            :badge="compareCount > 0 ? compareCount : undefined"
          />
          <q-btn
            flat
            no-caps
            to="/checkout"
            icon="shopping_cart"
            :badge="cartStore.totalItems > 0 ? cartStore.totalItems : undefined"
            label="Carrello"
          />
          <template v-if="auth.isLoggedIn">
            <q-btn flat no-caps to="/receipt" label="Scontrino" icon="camera_alt" />
            <q-btn flat round icon="person">
              <q-menu>
                <q-list style="min-width: 150px">
                  <q-item-label header>{{ auth.user?.username }}</q-item-label>
                  <q-separator />
                  <q-item clickable v-close-popup @click="auth.logout()">
                    <q-item-section avatar><q-icon name="logout" /></q-item-section>
                    <q-item-section>Esci</q-item-section>
                  </q-item>
                </q-list>
              </q-menu>
            </q-btn>
          </template>
          <template v-else>
            <q-btn flat no-caps to="/login" label="Accedi" icon="login" />
            <q-btn outline no-caps to="/register" label="Registrati" />
          </template>
        </div>
      </q-toolbar>
    </q-header>

    <!-- Mobile drawer -->
    <q-drawer v-model="leftDrawerOpen" bordered class="lt-md">
      <q-list>
        <q-item-label header class="text-h6 q-py-md">🛒 Prezzi Spesa</q-item-label>
        <q-separator />
        <q-item clickable to="/" exact v-close-popup>
          <q-item-section avatar><q-icon name="home" /></q-item-section>
          <q-item-section>Home</q-item-section>
        </q-item>
        <q-item clickable @click="goToCompare" v-close-popup>
          <q-item-section avatar><q-icon name="compare_arrows" /></q-item-section>
          <q-item-section>
            Confronta
            <q-badge v-if="compareCount > 0" color="accent" floating>{{ compareCount }}</q-badge>
          </q-item-section>
        </q-item>
        <q-item clickable to="/checkout" v-close-popup>
          <q-item-section avatar><q-icon name="shopping_cart" /></q-item-section>
          <q-item-section>
            Carrello
            <q-badge v-if="cartStore.totalItems > 0" color="accent" floating>{{ cartStore.totalItems }}</q-badge>
          </q-item-section>
        </q-item>
        <q-separator />
        <template v-if="auth.isLoggedIn">
          <q-item clickable to="/receipt" v-close-popup>
            <q-item-section avatar><q-icon name="camera_alt" /></q-item-section>
            <q-item-section>Scontrino</q-item-section>
          </q-item>
          <q-item clickable @click="auth.logout()" v-close-popup>
            <q-item-section avatar><q-icon name="logout" /></q-item-section>
            <q-item-section>Esci ({{ auth.user?.username }})</q-item-section>
          </q-item>
        </template>
        <template v-else>
          <q-item clickable to="/login" v-close-popup>
            <q-item-section avatar><q-icon name="login" /></q-item-section>
            <q-item-section>Accedi</q-item-section>
          </q-item>
          <q-item clickable to="/register" v-close-popup>
            <q-item-section avatar><q-icon name="person_add" /></q-item-section>
            <q-item-section>Registrati</q-item-section>
          </q-item>
        </template>
      </q-list>
    </q-drawer>

    <!-- Page content -->
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useCartStore } from '../stores/cart'

const auth = useAuthStore()
const cartStore = useCartStore()
const router = useRouter()

const leftDrawerOpen = ref(false)

// Compare products stored in localStorage
const compareCount = computed(() => {
  try {
    const items = JSON.parse(localStorage.getItem('compareProducts') || '[]')
    return items.length
  } catch {
    return 0
  }
})

function goToCompare() {
  try {
    const items = JSON.parse(localStorage.getItem('compareProducts') || '[]')
    if (items.length === 0) {
      return
    }
    router.push({ name: 'compare', query: { ids: items.join(',') } })
  } catch {
    return
  }
}
</script>
