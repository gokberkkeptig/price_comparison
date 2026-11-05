<template>
  <q-page class="page-container">
    <q-btn flat icon="arrow_back" label="Indietro" class="q-mb-md" @click="$router.back()" />

    <div v-if="loading" class="row q-col-gutter-lg">
      <div class="col-12 col-md-5">
        <q-skeleton height="350px" />
      </div>
      <div class="col-12 col-md-7">
        <q-skeleton type="text" class="text-h4" />
        <q-skeleton type="text" width="40%" class="q-mt-sm" />
        <q-skeleton height="200px" class="q-mt-md" />
      </div>
    </div>

    <div v-else-if="product" class="row q-col-gutter-lg">
      <!-- Product image -->
      <div class="col-12 col-md-5">
        <q-card>
          <q-img
            :src="product.image_url || 'https://via.placeholder.com/400x400?text=No+Image'"
            :ratio="1"
          >
            <template #error>
              <div class="absolute-full flex flex-center bg-grey-3">
                <q-icon name="image" size="80px" color="grey-5" />
              </div>
            </template>
          </q-img>
        </q-card>
      </div>

      <!-- Product info -->
      <div class="col-12 col-md-7">
        <h1 class="text-h4 q-mb-xs">{{ product.name }}</h1>
        <div class="text-subtitle1 text-grey-7 q-mb-md">
          {{ product.category }} · {{ product.sub_category }}
        </div>

        <q-btn
          color="primary"
          icon="add_shopping_cart"
          label="Aggiungi al carrello"
          @click="cartStore.addItem(product)"
          class="q-mb-lg"
        />

        <!-- Prices table -->
        <h2 class="text-h6 q-mb-sm">Prezzi per supermercato</h2>
        <q-table
          :rows="priceRows"
          :columns="priceColumns"
          row-key="price_id"
          flat
          bordered
          dense
          :pagination="{ rowsPerPage: 0 }"
          hide-pagination
        >
          <template #body-cell-price="props">
            <q-td :props="props">
              <span
                :class="{
                  'price-badge--cheapest': props.row.price === minPrice,
                  'price-badge': true,
                }"
              >
                €{{ props.row.price.toFixed(2) }}
              </span>
              <q-badge
                v-if="props.row.price === minPrice"
                color="positive"
                label="Miglior prezzo"
                class="q-ml-sm"
              />
            </q-td>
          </template>
          <template #body-cell-store="props">
            <q-td :props="props">
              <span class="text-capitalize text-weight-medium">{{ props.row.store }}</span>
            </q-td>
          </template>
        </q-table>
      </div>
    </div>

    <div v-else class="text-center q-pa-xl">
      <q-icon name="error_outline" size="64px" color="grey-5" />
      <p class="text-h6 text-grey-6 q-mt-md">Prodotto non trovato</p>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchProduct } from '../services/api'
import { useCartStore } from '../stores/cart'

const route = useRoute()
const cartStore = useCartStore()

const product = ref(null)
const loading = ref(true)

const priceColumns = [
  { name: 'store', label: 'Supermercato', field: 'store', align: 'left', sortable: true },
  { name: 'city', label: 'Città', field: 'city', align: 'left', sortable: true },
  { name: 'price', label: 'Prezzo', field: 'price', align: 'left', sortable: true },
  { name: 'last_updated', label: 'Aggiornato', field: 'last_updated_display', align: 'left' },
]

const priceRows = computed(() => {
  if (!product.value?.prices) return []
  return product.value.prices
    .map((p) => ({
      ...p,
      last_updated_display: p.last_updated
        ? new Date(p.last_updated).toLocaleDateString('it-IT')
        : '-',
    }))
    .sort((a, b) => a.price - b.price)
})

const minPrice = computed(() => {
  if (!priceRows.value.length) return null
  return Math.min(...priceRows.value.map((p) => p.price))
})

onMounted(async () => {
  try {
    const { data } = await fetchProduct(route.params.id)
    product.value = data.product
  } catch (err) {
    console.error('Error loading product:', err)
  } finally {
    loading.value = false
  }
})
</script>
