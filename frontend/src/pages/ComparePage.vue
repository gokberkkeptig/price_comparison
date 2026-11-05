<template>
  <q-page class="page-container">
    <q-btn flat icon="arrow_back" label="Torna ai prodotti" class="q-mb-md" @click="$router.push('/')" />

    <h1 class="text-h5 q-mb-md">Confronta Prodotti</h1>

    <!-- Loading -->
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

    <!-- Empty state -->
    <div v-else-if="products.length === 0" class="text-center q-pa-xl">
      <q-icon name="compare_arrows" size="64px" color="grey-5" />
      <p class="text-h6 text-grey-6 q-mt-md">Nessun prodotto da confrontare</p>
      <p class="text-grey-5">Seleziona almeno 2 prodotti dalla home</p>
      <q-btn color="primary" to="/" label="Torna alla home" class="q-mt-sm" />
    </div>

    <div v-else>
      <!-- ═══════ FILTERS ═══════ -->
      <div class="row q-col-gutter-sm q-mb-lg items-end">
        <div class="col-6 col-sm-4 col-md-3">
          <q-select
            v-model="filterCity"
            :options="cityOptions"
            filled
            dense
            clearable
            emit-value
            map-options
            label="Filtra per città"
          >
            <template #prepend><q-icon name="location_on" /></template>
          </q-select>
        </div>
        <div class="col-6 col-sm-4 col-md-3">
          <q-select
            v-model="filterStore"
            :options="storeOptions"
            filled
            dense
            clearable
            emit-value
            map-options
            label="Filtra per supermercato"
          >
            <template #prepend><q-icon name="store" /></template>
          </q-select>
        </div>
        <div class="col-6 col-sm-4 col-md-3">
          <q-select
            v-model="sortBy"
            :options="[
              { label: 'Prezzo ↑ (crescente)', value: 'asc' },
              { label: 'Prezzo ↓ (decrescente)', value: 'desc' },
            ]"
            filled
            dense
            emit-value
            map-options
            label="Ordina prezzi"
          >
            <template #prepend><q-icon name="sort" /></template>
          </q-select>
        </div>
      </div>

      <!-- ═══════ PRODUCT CARDS ═══════ -->
      <div class="row q-col-gutter-md q-mb-lg">
        <div
          v-for="product in products"
          :key="product.product_id"
          class="col-12 col-sm-6"
          :class="products.length <= 3 ? 'col-md-4' : 'col-md-3'"
        >
          <q-card
            class="full-height"
            :style="product.product_id === cheapestFilteredId ? 'border: 2px solid var(--q-positive)' : ''"
          >
            <q-badge
              v-if="product.product_id === cheapestFilteredId"
              color="positive"
              floating
              label="🏆 Miglior prezzo"
            />

            <q-btn
              round dense flat icon="close" size="sm" color="grey-6"
              class="absolute-top-right q-ma-xs" style="z-index: 1"
              @click="removeProduct(product.product_id)"
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
              <div class="text-h6 q-mt-sm price-badge">
                Da €{{ filteredMinPrice(product) }}
              </div>
            </q-card-section>

            <q-separator />

            <q-card-section>
              <div class="text-subtitle2 q-mb-xs">Prezzi per supermercato:</div>
              <q-list dense separator>
                <q-item
                  v-for="price in filteredSortedPrices(product)"
                  :key="price.price_id"
                  class="q-px-none"
                >
                  <q-item-section>
                    <q-item-label class="text-capitalize">{{ price.store }}</q-item-label>
                    <q-item-label caption>{{ price.city }}</q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <span
                      class="text-weight-bold"
                      :class="isLowestFiltered(product, price.price) ? 'text-positive' : ''"
                    >
                      €{{ price.price.toFixed(2) }}
                    </span>
                  </q-item-section>
                </q-item>
                <q-item v-if="filteredSortedPrices(product).length === 0" class="q-px-none">
                  <q-item-section class="text-grey-5 text-caption">
                    Nessun prezzo per i filtri selezionati
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card-section>

            <q-card-actions>
              <q-btn
                flat color="primary" icon="add_shopping_cart"
                label="Aggiungi al carrello" no-caps class="full-width"
                @click="cartStore.addItem(product)"
              />
            </q-card-actions>
          </q-card>
        </div>
      </div>

      <!-- ═══════ SUMMARY TABLE ═══════ -->
      <h2 class="text-h6 q-mb-sm">Riepilogo confronto</h2>
      <q-table
        :rows="summaryRows"
        :columns="summaryColumns"
        row-key="store_city"
        flat bordered dense
        :pagination="{ rowsPerPage: 0 }"
        hide-pagination
        class="q-mb-lg"
      >
        <template #body-cell="props">
          <q-td :props="props">
            <template v-if="props.col.name === 'store_city'">
              <span class="text-weight-medium text-capitalize">{{ props.value }}</span>
            </template>
            <template v-else-if="props.value !== null && props.value !== undefined">
              <span
                :class="{ 'text-positive text-weight-bold': isMinForProduct(props.col.field, props.value) }"
              >
                €{{ props.value.toFixed(2) }}
              </span>
            </template>
            <template v-else>
              <span class="text-grey-5">—</span>
            </template>
          </q-td>
        </template>
      </q-table>

      <!-- ═══════ SHOPPING PLAN ═══════ -->
      <q-separator class="q-my-lg" />
      <h2 class="text-h6 q-mb-sm">
        <q-icon name="shopping_bag" class="q-mr-xs" />
        Pianifica la spesa
      </h2>
      <p class="text-body2 text-grey-7 q-mb-md">
        Seleziona uno o più supermercati per vedere il costo totale di questi prodotti.
      </p>

      <div class="row q-col-gutter-sm q-mb-md">
        <div v-for="sc in storeCityList" :key="sc.key" class="col-auto">
          <q-btn
            :outline="!selectedStores.includes(sc.key)"
            :unelevated="selectedStores.includes(sc.key)"
            :color="selectedStores.includes(sc.key) ? 'primary' : 'grey-7'"
            no-caps
            @click="toggleStore(sc.key)"
          >
            <q-icon name="store" class="q-mr-xs" />
            {{ sc.label }}
          </q-btn>
        </div>
      </div>

      <!-- Totals per selected store -->
      <div v-if="selectedStores.length > 0" class="row q-col-gutter-md q-mb-lg">
        <div
          v-for="sc in selectedStoreDetails"
          :key="sc.key"
          class="col-12 col-sm-6 col-md-4"
        >
          <q-card
            :class="sc.key === cheapestStoreKey ? 'bg-positive text-white' : ''"
            :style="sc.key === cheapestStoreKey ? '' : 'border: 1px solid #e0e0e0'"
          >
            <q-card-section>
              <div class="row items-center q-mb-sm">
                <q-icon :name="sc.key === cheapestStoreKey ? 'emoji_events' : 'store'" size="28px" class="q-mr-sm" />
                <div>
                  <div class="text-subtitle1 text-weight-bold text-capitalize">{{ sc.label }}</div>
                  <div :class="sc.key === cheapestStoreKey ? 'text-white-7' : 'text-caption text-grey-6'">
                    {{ sc.available }}/{{ products.length }} prodotti disponibili
                  </div>
                </div>
              </div>

              <q-list dense>
                <q-item v-for="item in sc.items" :key="item.name" class="q-px-none">
                  <q-item-section>
                    <q-item-label :class="sc.key === cheapestStoreKey ? '' : ''">
                      {{ item.name }}
                    </q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <span v-if="item.price !== null" class="text-weight-medium">
                      €{{ item.price.toFixed(2) }}
                    </span>
                    <span v-else class="text-grey-5">—</span>
                  </q-item-section>
                </q-item>
              </q-list>

              <q-separator :dark="sc.key === cheapestStoreKey" class="q-my-sm" />

              <div class="row items-center justify-between">
                <span class="text-subtitle1 text-weight-bold">Totale</span>
                <span class="text-h5 text-weight-bold">€{{ sc.total.toFixed(2) }}</span>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- ═══════ MIX OTTIMALE ═══════ -->
      <div v-if="selectedStores.length >= 2" class="q-mb-lg">
        <q-separator class="q-my-md" />
        <h2 class="text-h6 q-mb-xs">
          <q-icon name="auto_awesome" color="accent" class="q-mr-xs" />
          Mix ottimale
        </h2>
        <p class="text-body2 text-grey-7 q-mb-md">
          Per ogni prodotto, il prezzo migliore tra i supermercati selezionati.
        </p>

        <q-table
          :rows="bestMixRows"
          :columns="bestMixColumns"
          row-key="name"
          flat bordered dense
          :pagination="{ rowsPerPage: 0 }"
          hide-pagination
        >
          <template #body-cell-price="props">
            <q-td :props="props">
              <span class="text-weight-bold text-positive">
                €{{ props.value.toFixed(2) }}
              </span>
            </q-td>
          </template>
          <template #body-cell-store="props">
            <q-td :props="props">
              <q-badge
                :color="storeColor(props.row.storeLabel)"
                :label="props.row.storeLabel"
                class="text-capitalize cursor-pointer"
              >
                <q-badge
                  v-if="props.row.altStores.length > 0"
                  color="white"
                  text-color="dark"
                  :label="'+' + props.row.altStores.length"
                  class="q-ml-xs"
                  style="font-size: 10px"
                />
                <q-tooltip v-if="props.row.altStores.length > 0" class="text-body2">
                  Stesso prezzo anche a:<br>
                  <span v-for="(alt, i) in props.row.altStores" :key="i">
                    • {{ alt }}<br>
                  </span>
                </q-tooltip>
              </q-badge>
            </q-td>
          </template>
          <template #bottom>
            <div class="row full-width items-center justify-between q-pa-sm">
              <span class="text-subtitle1 text-weight-bold">Totale mix ottimale</span>
              <span class="text-h5 text-weight-bold text-positive">
                €{{ bestMixTotal.toFixed(2) }}
              </span>
            </div>
            <div v-if="bestSingleTotal !== null" class="row full-width items-center q-px-sm q-pb-sm">
              <span class="text-caption text-grey-7">
                Risparmio vs miglior singolo supermercato:
                <strong class="text-positive">
                  €{{ (bestSingleTotal - bestMixTotal).toFixed(2) }}
                </strong>
              </span>
            </div>
          </template>
        </q-table>
      </div>

      <div v-else-if="selectedStores.length === 0" class="text-center q-pa-md text-grey-6">
        <q-icon name="touch_app" size="32px" class="q-mb-xs" /><br>
        Seleziona almeno un supermercato per calcolare i totali
      </div>

      <div class="text-center q-mt-lg q-mb-md">
        <q-btn
          outline color="negative" label="Svuota confronto"
          icon="clear_all" no-caps @click="clearAndGoHome"
        />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { compareProducts } from '../services/api'
import { useCartStore } from '../stores/cart'
import { useCompareStore } from '../stores/compare'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()
const compareStore = useCompareStore()

const products = ref([])
const cheapestId = ref(null)
const loading = ref(true)

// ── Filters ──
const filterCity = ref(null)
const filterStore = ref(null)
const sortBy = ref('asc')

const cityOptions = computed(() => {
  const cities = new Set()
  for (const p of products.value) {
    for (const pr of p.prices || []) {
      if (pr.city) cities.add(pr.city)
    }
  }
  return Array.from(cities).sort().map((c) => ({ label: c, value: c }))
})

const storeOptions = computed(() => {
  const stores = new Set()
  for (const p of products.value) {
    for (const pr of p.prices || []) {
      if (pr.store) stores.add(pr.store)
    }
  }
  return Array.from(stores).sort().map((s) => ({
    label: s.charAt(0).toUpperCase() + s.slice(1),
    value: s,
  }))
})

function filteredSortedPrices(product) {
  let prices = [...(product.prices || [])]
  if (filterCity.value) prices = prices.filter((p) => p.city === filterCity.value)
  if (filterStore.value) prices = prices.filter((p) => p.store === filterStore.value)
  prices.sort((a, b) => sortBy.value === 'asc' ? a.price - b.price : b.price - a.price)
  return prices
}

function filteredMinPrice(product) {
  const prices = filteredSortedPrices(product)
  if (prices.length === 0) return 'N/D'
  return Math.min(...prices.map((p) => p.price)).toFixed(2)
}

function isLowestFiltered(product, price) {
  const prices = filteredSortedPrices(product)
  if (prices.length === 0) return false
  return price === Math.min(...prices.map((p) => p.price))
}

const cheapestFilteredId = computed(() => {
  let bestId = null
  let bestPrice = null
  for (const product of products.value) {
    const prices = filteredSortedPrices(product)
    if (prices.length === 0) continue
    const min = Math.min(...prices.map((p) => p.price))
    if (bestPrice === null || min < bestPrice) {
      bestPrice = min
      bestId = product.product_id
    }
  }
  return bestId
})

function removeProduct(id) {
  compareStore.remove(id)
  products.value = products.value.filter((p) => p.product_id !== id)
}

function clearAndGoHome() {
  compareStore.clear()
  router.push('/')
}

// ── Summary table ──
const summaryColumns = computed(() => {
  const cols = [
    { name: 'store_city', label: 'Supermercato / Città', field: 'store_city', align: 'left' },
  ]
  for (const p of products.value) {
    cols.push({
      name: `p_${p.product_id}`,
      label: p.name.length > 25 ? p.name.substring(0, 25) + '…' : p.name,
      field: `p_${p.product_id}`,
      align: 'center',
    })
  }
  return cols
})

const summaryRows = computed(() => {
  const map = new Map()
  for (const product of products.value) {
    for (const price of filteredSortedPrices(product)) {
      const key = `${price.store} — ${price.city}`
      if (!map.has(key)) map.set(key, { store_city: key })
      map.get(key)[`p_${product.product_id}`] = price.price
    }
  }
  return Array.from(map.values()).sort((a, b) => a.store_city.localeCompare(b.store_city))
})

const minPricePerProduct = computed(() => {
  const mins = {}
  for (const product of products.value) {
    const prices = filteredSortedPrices(product).map((p) => p.price)
    mins[`p_${product.product_id}`] = prices.length ? Math.min(...prices) : null
  }
  return mins
})

function isMinForProduct(field, value) {
  return minPricePerProduct.value[field] === value
}

// ── Shopping plan ──
const selectedStores = ref([])

// All unique store+city pairs from filtered prices
const storeCityList = computed(() => {
  const set = new Set()
  for (const product of products.value) {
    for (const price of filteredSortedPrices(product)) {
      set.add(`${price.store}|${price.city}`)
    }
  }
  return Array.from(set).sort().map((key) => {
    const [store, city] = key.split('|')
    return { key, label: `${store} (${city})`, store, city }
  })
})

function toggleStore(key) {
  const idx = selectedStores.value.indexOf(key)
  if (idx >= 0) {
    selectedStores.value.splice(idx, 1)
  } else {
    selectedStores.value.push(key)
  }
}

// Details for each selected store: which products, prices, total
const selectedStoreDetails = computed(() => {
  return selectedStores.value.map((key) => {
    const [store, city] = key.split('|')
    const items = []
    let total = 0
    let available = 0

    for (const product of products.value) {
      const match = (product.prices || []).find(
        (p) => p.store === store && p.city === city
      )
      if (match) {
        items.push({ name: product.name, price: match.price })
        total += match.price
        available++
      } else {
        items.push({ name: product.name, price: null })
      }
    }

    return {
      key,
      label: `${store} (${city})`,
      store,
      city,
      items,
      total,
      available,
    }
  }).sort((a, b) => a.total - b.total)
})

// Which selected store has lowest total?
const cheapestStoreKey = computed(() => {
  if (selectedStoreDetails.value.length === 0) return null
  // Only consider stores that have all products
  const full = selectedStoreDetails.value.filter((s) => s.available === products.value.length)
  if (full.length > 0) return full[0].key // already sorted by total
  return selectedStoreDetails.value[0].key
})

// ── Best Mix ──
const bestMixColumns = [
  { name: 'name', label: 'Prodotto', field: 'name', align: 'left' },
  { name: 'store', label: 'Supermercato', field: 'storeLabel', align: 'center' },
  { name: 'price', label: 'Prezzo', field: 'price', align: 'right', sortable: true },
]

const bestMixRows = computed(() => {
  if (selectedStores.value.length < 2) return []

  return products.value.map((product) => {
    let bestPrice = null
    let bestStore = ''
    let bestCity = ''
    const allAtBest = []

    // Find the best price across selected stores
    for (const key of selectedStores.value) {
      const [store, city] = key.split('|')
      const match = (product.prices || []).find(
        (p) => p.store === store && p.city === city
      )
      if (match && (bestPrice === null || match.price < bestPrice)) {
        bestPrice = match.price
        bestStore = store
        bestCity = city
      }
    }

    // Collect all stores with the same best price
    if (bestPrice !== null) {
      for (const key of selectedStores.value) {
        const [store, city] = key.split('|')
        const match = (product.prices || []).find(
          (p) => p.store === store && p.city === city
        )
        if (match && match.price === bestPrice) {
          allAtBest.push(`${store} (${city})`)
        }
      }
    }

    const primaryLabel = bestStore ? `${bestStore} (${bestCity})` : '—'
    // altStores = all others at same price, excluding the primary
    const altStores = allAtBest.filter((s) => s !== primaryLabel)

    return {
      name: product.name,
      storeLabel: primaryLabel,
      altStores,
      price: bestPrice ?? 0,
    }
  })
})

const bestMixTotal = computed(() => {
  return bestMixRows.value.reduce((sum, r) => sum + r.price, 0)
})

const bestSingleTotal = computed(() => {
  if (selectedStoreDetails.value.length === 0) return null
  const full = selectedStoreDetails.value.filter((s) => s.available === products.value.length)
  if (full.length === 0) return null
  return full[0].total // already sorted by total ascending
})

const storeColors = ['primary', 'secondary', 'accent', 'teal', 'deep-purple', 'blue-grey', 'brown', 'indigo']

function storeColor(label) {
  const idx = storeCityList.value.findIndex((sc) => `${sc.store} (${sc.city})` === label)
  return storeColors[idx % storeColors.length]
}

// ── Init ──
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
