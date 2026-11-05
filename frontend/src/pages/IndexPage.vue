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

    <!-- Compare bar -->
    <q-banner v-if="compareList.length > 0" class="bg-accent text-white q-mb-md" rounded>
      <template #avatar><q-icon name="compare_arrows" /></template>
      {{ compareList.length }}/4 prodotti selezionati per il confronto
      <template #action>
        <q-btn flat label="Confronta" @click="goCompare" :disable="compareList.length < 2" />
        <q-btn flat label="Annulla" @click="clearCompare" />
      </template>
    </q-banner>

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
        <q-card class="product-card full-height">
          <!-- Compare checkbox -->
          <q-checkbox
            :model-value="isInCompare(product.product_id)"
            @update:model-value="toggleCompare(product.product_id)"
            class="absolute-top-right q-ma-xs"
            style="z-index: 1"
            dense
            color="accent"
            :disable="!isInCompare(product.product_id) && compareList.length >= 4"
          />

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
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchProducts, fetchCategories, fetchStores, fetchLocations } from '../services/api'
import { useCartStore } from '../stores/cart'

const router = useRouter()
const cartStore = useCartStore()

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

// Compare
const compareList = ref(JSON.parse(localStorage.getItem('compareProducts') || '[]'))

function isInCompare(id) {
  return compareList.value.includes(id)
}

function toggleCompare(id) {
  const idx = compareList.value.indexOf(id)
  if (idx >= 0) {
    compareList.value.splice(idx, 1)
  } else if (compareList.value.length < 4) {
    compareList.value.push(id)
  }
  localStorage.setItem('compareProducts', JSON.stringify(compareList.value))
}

function clearCompare() {
  compareList.value = []
  localStorage.setItem('compareProducts', '[]')
}

function goCompare() {
  router.push({ name: 'compare', query: { ids: compareList.value.join(',') } })
}

// Fetch products
async function loadProducts(append = false) {
  loading.value = true
  try {
    const params = { ...filters, page: page.value, per_page: 20 }
    // Remove empty values
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

// Load filter options
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
