<template>
  <q-page class="page-container">
    <h1 class="text-h5 q-mb-md">🛒 Carrello</h1>

    <!-- Empty cart -->
    <div v-if="cartStore.isEmpty" class="text-center q-pa-xl">
      <q-icon name="shopping_cart" size="64px" color="grey-5" />
      <p class="text-h6 text-grey-6 q-mt-md">Il carrello è vuoto</p>
      <q-btn color="primary" to="/" label="Vai ai prodotti" class="q-mt-sm" />
    </div>

    <template v-else>
      <!-- Cart items -->
      <q-card class="q-mb-lg">
        <q-list separator>
          <q-item v-for="item in cartStore.cartList" :key="item.product_id">
            <q-item-section avatar>
              <q-avatar rounded size="56px">
                <q-img
                  :src="item.image_url || 'https://via.placeholder.com/56?text=?'"
                  :ratio="1"
                />
              </q-avatar>
            </q-item-section>

            <q-item-section>
              <q-item-label>{{ item.name }}</q-item-label>
              <q-item-label caption>
                {{ item.min_price != null ? `Da €${item.min_price.toFixed(2)}` : '' }}
              </q-item-label>
            </q-item-section>

            <q-item-section side class="row items-center q-gutter-xs">
              <q-btn
                round
                dense
                flat
                icon="remove"
                size="sm"
                @click="cartStore.updateQuantity(item.product_id, item.quantity - 1)"
              />
              <span class="text-body1 text-weight-medium q-mx-sm">{{ item.quantity }}</span>
              <q-btn
                round
                dense
                flat
                icon="add"
                size="sm"
                @click="cartStore.updateQuantity(item.product_id, item.quantity + 1)"
              />
              <q-btn
                round
                dense
                flat
                icon="delete"
                color="negative"
                size="sm"
                class="q-ml-sm"
                @click="cartStore.removeItem(item.product_id)"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </q-card>

      <div class="row q-gutter-sm q-mb-lg">
        <q-btn outline color="negative" label="Svuota carrello" icon="delete_sweep" @click="cartStore.clearCart()" />
        <q-btn color="primary" label="Calcola confronto prezzi" icon="calculate" @click="calculate" :loading="calculating" />
      </div>

      <!-- Store comparison results -->
      <div v-if="results" class="q-mt-lg">
        <h2 class="text-h6 q-mb-sm">💰 Confronto per Supermercato</h2>

        <div class="row q-col-gutter-md q-mb-lg">
          <div
            v-for="summary in results.store_summaries"
            :key="summary.store"
            class="col-12 col-sm-6 col-md-4"
          >
            <q-card
              :class="summary.store === results.cheapest_store ? '' : ''"
              :style="summary.store === results.cheapest_store ? 'border: 2px solid #4CAF50' : ''"
            >
              <q-card-section>
                <div class="row items-center justify-between">
                  <div>
                    <div class="text-subtitle1 text-capitalize text-weight-bold">
                      {{ summary.store }}
                    </div>
                    <div class="text-caption text-grey-6">
                      {{ summary.available_products }}/{{ summary.total_products }} prodotti disponibili
                    </div>
                  </div>
                  <q-badge
                    v-if="summary.store === results.cheapest_store"
                    color="positive"
                    label="🏆 Più economico"
                  />
                </div>
                <div class="text-h5 q-mt-sm" :class="summary.store === results.cheapest_store ? 'text-positive' : ''">
                  €{{ summary.total.toFixed(2) }}
                </div>
                <q-linear-progress
                  v-if="!summary.complete"
                  :value="summary.available_products / summary.total_products"
                  color="warning"
                  class="q-mt-sm"
                />
                <div v-if="!summary.complete" class="text-caption text-warning q-mt-xs">
                  Alcuni prodotti non disponibili
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <!-- Detailed breakdown -->
        <h2 class="text-h6 q-mb-sm">Dettaglio prodotti</h2>
        <q-table
          :rows="detailRows"
          :columns="detailColumns"
          row-key="product_id"
          flat
          bordered
          dense
          :pagination="{ rowsPerPage: 0 }"
          hide-pagination
          wrap-cells
        />
      </div>
    </template>
  </q-page>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useCartStore } from '../stores/cart'
import { calculateCart } from '../services/api'

const cartStore = useCartStore()
const results = ref(null)
const calculating = ref(false)

async function calculate() {
  calculating.value = true
  results.value = null
  try {
    const { data } = await calculateCart(cartStore.cartPayload)
    results.value = data
  } catch (err) {
    console.error('Error calculating cart:', err)
  } finally {
    calculating.value = false
  }
}

// Build dynamic columns: product name + one column per store
const detailColumns = computed(() => {
  if (!results.value) return []
  const cols = [
    { name: 'name', label: 'Prodotto', field: 'name', align: 'left' },
    { name: 'qty', label: 'Qtà', field: 'quantity', align: 'center' },
  ]
  for (const store of results.value.stores) {
    cols.push({
      name: store,
      label: store.charAt(0).toUpperCase() + store.slice(1),
      field: store,
      align: 'center',
      format: (val) => (val != null ? `€${val.toFixed(2)}` : '-'),
    })
  }
  return cols
})

const detailRows = computed(() => {
  if (!results.value) return []
  return results.value.products.map((p) => {
    const row = { product_id: p.product_id, name: p.name, quantity: p.quantity }
    for (const store of results.value.stores) {
      const priceEntry = p.prices.find((pr) => pr.store === store)
      row[store] = priceEntry ? priceEntry.subtotal : null
    }
    return row
  })
})
</script>
