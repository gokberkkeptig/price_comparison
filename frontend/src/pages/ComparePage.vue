<template>
  <q-page class="page-container">
    <q-btn flat icon="arrow_back" label="Indietro" class="q-mb-md" @click="$router.back()" />

    <h1 class="text-h5 q-mb-md">Confronta Prodotti</h1>

    <div v-if="loading" class="row q-col-gutter-md">
      <div v-for="n in 3" :key="n" class="col-12 col-sm-4">
        <q-card>
          <q-skeleton height="200px" />
          <q-card-section>
            <q-skeleton type="text" />
            <q-skeleton type="text" width="60%" />
          </q-card-section>
        </q-card>
      </div>
    </div>

    <div v-else-if="products.length === 0" class="text-center q-pa-xl">
      <q-icon name="compare_arrows" size="64px" color="grey-5" />
      <p class="text-h6 text-grey-6 q-mt-md">Nessun prodotto da confrontare</p>
      <q-btn color="primary" to="/" label="Torna alla home" class="q-mt-sm" />
    </div>

    <div v-else>
      <div class="row q-col-gutter-md">
        <div
          v-for="product in products"
          :key="product.product_id"
          class="col-12 col-sm-6 col-md-3"
        >
          <q-card
            :class="{ 'border-positive': product.product_id === cheapestId }"
            class="full-height"
            :style="product.product_id === cheapestId ? 'border: 2px solid #4CAF50' : ''"
          >
            <q-badge
              v-if="product.product_id === cheapestId"
              color="positive"
              floating
              label="🏆 Miglior prezzo"
            />

            <q-img
              :src="product.image_url || 'https://via.placeholder.com/300x300?text=No+Image'"
              :ratio="1"
            >
              <template #error>
                <div class="absolute-full flex flex-center bg-grey-3">
                  <q-icon name="image" size="48px" color="grey-5" />
                </div>
              </template>
            </q-img>

            <q-card-section>
              <div class="text-subtitle1 text-weight-bold">{{ product.name }}</div>
              <div class="text-caption text-grey-6">
                {{ product.category }} · {{ product.sub_category }}
              </div>
            </q-card-section>

            <q-separator />

            <q-card-section>
              <div class="text-subtitle2 q-mb-sm">Prezzi:</div>
              <q-list dense>
                <q-item
                  v-for="price in sortedPrices(product)"
                  :key="price.price_id"
                  class="q-px-none"
                >
                  <q-item-section>
                    <span class="text-capitalize">{{ price.store }}</span>
                    <span class="text-caption text-grey-6">{{ price.city }}</span>
                  </q-item-section>
                  <q-item-section side>
                    <span
                      class="text-weight-bold"
                      :class="price.price === product.min_price ? 'text-positive' : ''"
                    >
                      €{{ price.price.toFixed(2) }}
                    </span>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card-section>

            <q-card-section class="q-pt-none">
              <div class="text-h6 price-badge">
                Da €{{ product.min_price != null ? product.min_price.toFixed(2) : 'N/D' }}
              </div>
            </q-card-section>

            <q-card-actions>
              <q-btn
                flat
                color="primary"
                icon="add_shopping_cart"
                label="Aggiungi"
                @click="cartStore.addItem(product)"
                class="full-width"
              />
            </q-card-actions>
          </q-card>
        </div>
      </div>

      <div class="text-center q-mt-lg">
        <q-btn
          outline
          color="negative"
          label="Svuota confronto"
          icon="clear_all"
          @click="clearAndGoHome"
        />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { compareProducts } from '../services/api'
import { useCartStore } from '../stores/cart'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()

const products = ref([])
const cheapestId = ref(null)
const loading = ref(true)

function sortedPrices(product) {
  return [...(product.prices || [])].sort((a, b) => a.price - b.price)
}

function clearAndGoHome() {
  localStorage.setItem('compareProducts', '[]')
  router.push('/')
}

onMounted(async () => {
  const ids = route.query.ids
  if (!ids) {
    loading.value = false
    return
  }

  try {
    const idArray = ids.split(',').map(Number).filter(Boolean)
    if (idArray.length === 0) {
      loading.value = false
      return
    }
    const { data } = await compareProducts(idArray)
    products.value = data.products
    cheapestId.value = data.cheapest_product_id
  } catch (err) {
    console.error('Error comparing products:', err)
  } finally {
    loading.value = false
  }
})
</script>
