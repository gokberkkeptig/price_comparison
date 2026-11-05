<template>
  <q-page class="page-container">
    <!-- Search & Filters -->
    <div class="row q-col-gutter-sm q-mb-md items-end">
      <div class="col-12 col-md-4">
        <q-input
          v-model="filters.query"
          filled
          dense
          clearable
          label="Cerca prodotti..."
          debounce="400"
          @update:model-value="resetAndFetch"
        >
          <template #prepend><q-icon name="search" /></template>
        </q-input>
      </div>
      <div class="col-6 col-md-2">
        <q-select
          v-model="filters.city"
          :options="cityOptions"
          filled
          dense
          clearable
          emit-value
          map-options
          label="Città"
          @update:model-value="resetAndFetch"
        />
      </div>
      <div class="col-6 col-md-2">
        <q-select
          v-model="filters.category"
          :options="categoryOptions"
          filled
          dense
          clearable
          emit-value
          map-options
          label="Categoria"
          @update:model-value="resetAndFetch"
        />
      </div>
      <div class="col-6 col-md-2">
        <q-select
          v-model="filters.store"
          :options="storeOptions"
          filled
          dense
          clearable
          emit-value
          map-options
          label="Supermercato"
          @update:model-value="resetAndFetch"
        />
      </div>
      <div class="col-6 col-md-2">
        <q-select
          v-model="filters.order_by"
          :options="[
            { label: 'Prezzo ↑', value: 'asc' },
            { label: 'Prezzo ↓', value: 'desc' },
          ]"
          filled
          dense
          emit-value
          map-options
          label="Ordina"
          @update:model-value="resetAndFetch"
        />
      </div>
    </div>

    <!-- Products Grid -->
    <div v-if="loading && products.length === 0" class="row q-col-gutter-md">
      <div v-for="n in 8" :key="n" class="col-6 col-sm-4 col-md-3">
        <q-card>
          <q-skeleton height="200px" />
          <q-card-section>
            <q-skeleton type="text" />
            <q-skeleton type="text" width="60%" />
          </q-card-section>
        </q-card>
      </div>
    </div>

    <div v-else-if="products.length === 0 && !loading" class="text-center q-pa-xl">
      <q-icon name="search_off" size="64px" color="grey-5" />
      <p class="text-h6 text-grey-6 q-mt-md">Nessun prodotto trovato</p>
      <p class="text-grey-5">Prova a modificare i filtri di ricerca</p>
    </div>

    <div v-else class="row q-col-gutter-md">
      <div
        v-for="product in products"
        :key="product.product_id"
        class="col-6 col-sm-4 col-md-3"
      >
        <q-card
          class="product-card full-height"
          :class="{ 'compare-selected': compareStore.has(product.product_id) }"
        >
          <q-img
            :src="product.image_url || 'https://via.placeholder.com/300x300?text=No+Image'"
            :ratio="1"
            class="cursor-pointer"
            @click="$router.push({ name: 'product-detail', params: { id: product.product_id } })"
          >
            <template #error>
              <div class="absolute-full flex flex-center bg-grey-3">
                <q-icon name="image" size="48px" color="grey-5" />
              </div>
            </template>
          </q-img>

          <q-card-section
            class="cursor-pointer"
            @click="$router.push({ name: 'product-detail', params: { id: product.product_id } })"
          >
            <div class="text-subtitle2 ellipsis-2-lines" style="min-height: 40px">
              {{ product.name }}
            </div>
            <div class="text-caption text-grey-6 q-mt-xs">
              {{ product.category }} · {{ product.sub_category }}
            </div>
          </q-card-section>

          <q-card-section class="q-pt-none">
            <div class="row items-center justify-between">
              <span class="price-badge">
                {{ product.min_price != null ? `€${product.min_price.toFixed(2)}` : 'N/D' }}
              </span>
              <q-btn
                round
                dense
                flat
                icon="add_shopping_cart"
                color="primary"
                @click.stop="cartStore.addItem(product)"
              />
            </div>
          </q-card-section>

          <!-- Compare button -->
          <q-card-actions class="q-pt-none">
            <q-btn
              flat
              dense
              no-caps
              class="full-width"
              :color="compareStore.has(product.product_id) ? 'negative' : 'accent'"
              :icon="compareStore.has(product.product_id) ? 'remove_circle_outline' : 'compare_arrows'"
              :label="compareStore.has(product.product_id) ? 'Rimuovi dal confronto' : 'Confronta'"
              @click.stop="compareStore.toggle(product.product_id)"
              :disable="!compareStore.has(product.product_id) && compareStore.isFull"
            />
          </q-card-actions>
        </q-card>
      </div>
    </div>

    <!-- Infinite scroll -->
    <div v-if="hasMore" class="row justify-center q-my-lg">
      <q-spinner-dots v-if="loading" size="40px" color="primary" />
      <q-btn
        v-else
        flat
        color="primary"
        label="Carica altri prodotti"
        @click="fetchMore"
      />
    </div>

    <!-- Sticky compare bar -->
    <transition name="slide-up">
      <div v-if="compareStore.count > 0" class="compare-bar">
        <div class="compare-bar__inner row items-center q-gutter-sm">
          <q-icon name="compare_arrows" size="24px" color="white" />
          <span class="text-white text-weight-medium">
            {{ compareStore.count }} prodott{{ compareStore.count === 1 ? 'o' : 'i' }} selezionat{{ compareStore.count === 1 ? 'o' : 'i' }}
          </span>
          <q-space />
          <q-btn
            flat
            dense
            no-caps
            color="white"
            label="Svuota"
            icon="clear"
            @click="compareStore.clear()"
          />
          <q-btn
            unelevated
            no-caps
            color="white"
            text-color="accent"
            label="Vai al confronto"
            icon="arrow_forward"
            :disable="compareStore.count < 2"
            @click="goCompare"
          />
        </div>
      </div>
    </transition>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchProducts, fetchCategories, fetchStores, fetchLocations } from '../services/api'
import { useCartStore } from '../stores/cart'
import { useCompareStore } from '../stores/compare'

const router = useRouter()
const cartStore = useCartStore()
const compareStore = useCompareStore()

const products = ref([])
const loading = ref(false)
const page = ref(1)
const totalPages = ref(1)
const hasMore = ref(false)

const filters = reactive({
  query: '',
  category: null,
  store: null,
  city: null,
  order_by: 'asc',
})

const categoryOptions = ref([])
const storeOptions = ref([])
const cityOptions = ref([])

function goCompare() {
  router.push({ name: 'compare', query: { ids: compareStore.ids.join(',') } })
}

// Fetch products
async function loadProducts(append = false) {
  loading.value = true
  try {
    const params = { ...filters, page: page.value, per_page: 20 }
    Object.keys(params).forEach((k) => {
      if (!params[k] && params[k] !== 0) delete params[k]
    })

    const { data } = await fetchProducts(params)

    if (append) {
      products.value.push(...data.products)
    } else {
      products.value = data.products
    }
    totalPages.value = data.total_pages
    hasMore.value = page.value < data.total_pages
  } catch (err) {
    console.error('Error loading products:', err)
  } finally {
    loading.value = false
  }
}

function resetAndFetch() {
  page.value = 1
  loadProducts(false)
}

function fetchMore() {
  page.value += 1
  loadProducts(true)
}

async function loadFilters() {
  try {
    const [catRes, storeRes, locRes] = await Promise.all([
      fetchCategories(),
      fetchStores(),
      fetchLocations(),
    ])
    categoryOptions.value = catRes.data.categories.map((c) => ({
      label: c.name,
      value: c.name,
    }))
    storeOptions.value = storeRes.data.stores.map((s) => ({
      label: s.name.charAt(0).toUpperCase() + s.name.slice(1),
      value: s.name,
    }))
    cityOptions.value = locRes.data.locations.map((l) => ({
      label: l.city,
      value: l.city,
    }))
  } catch (err) {
    console.error('Error loading filters:', err)
  }
}

onMounted(() => {
  loadFilters()
  loadProducts()
})
</script>

<style lang="scss" scoped>
.compare-selected {
  outline: 2px solid var(--q-accent);
  outline-offset: -2px;
}

.compare-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--q-accent);
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.2);
}

.compare-bar__inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 10px 16px;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>
