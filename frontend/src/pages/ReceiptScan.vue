<template>
  <q-page class="page-container">
    <h1 class="text-h5 q-mb-md">📸 Scansiona Scontrino</h1>
    <p class="text-body2 text-grey-7 q-mb-lg">
      Carica una foto del tuo scontrino. L'OCR estrarrà i prodotti e i prezzi.
      Potrai verificare e correggere i dati prima di salvarli nel database.
    </p>

    <!-- ═══════ STEP 1: Upload & Analyze ═══════ -->
    <div v-if="step === 'upload'" class="row q-col-gutter-lg">
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Carica immagine</div>
            <q-file
              v-model="imageFile"
              filled
              label="Seleziona o scatta foto"
              accept="image/*"
              capture="environment"
              @update:model-value="onFileSelected"
            >
              <template #prepend><q-icon name="attach_file" /></template>
            </q-file>

            <div v-if="previewUrl" class="q-mt-md">
              <q-img :src="previewUrl" style="max-height: 300px" fit="contain" />
            </div>
          </q-card-section>

          <q-card-actions class="q-pa-md">
            <q-btn
              v-if="imageBase64"
              color="primary"
              label="Analizza scontrino"
              icon="document_scanner"
              class="full-width"
              size="lg"
              :loading="analyzing"
              @click="analyze"
              no-caps
            />
          </q-card-actions>
        </q-card>
      </div>

      <div class="col-12 col-md-6">
        <q-card v-if="error">
          <q-card-section class="bg-negative text-white">
            <q-icon name="error" class="q-mr-sm" />Errore
          </q-card-section>
          <q-card-section>
            <p>{{ error }}</p>
            <q-expansion-item v-if="ocrText" label="Testo OCR estratto" dense header-class="text-caption">
              <pre class="text-caption q-pa-sm bg-grey-2" style="white-space: pre-wrap; max-height: 200px; overflow: auto">{{ ocrText }}</pre>
            </q-expansion-item>
          </q-card-section>
        </q-card>

        <div v-else class="text-center q-pa-xl text-grey-5">
          <q-icon name="receipt_long" size="64px" />
          <p class="q-mt-md">Carica un'immagine e clicca "Analizza"</p>
        </div>
      </div>
    </div>

    <!-- ═══════ STEP 2: Review & Confirm ═══════ -->
    <div v-if="step === 'review'">
      <q-banner class="bg-info text-white q-mb-md" rounded>
        <template #avatar><q-icon name="rate_review" /></template>
        Verifica i dati estratti. Puoi modificare supermercato, città, nomi e prezzi prima di salvare.
      </q-banner>

      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-12 col-sm-4">
          <q-input
            v-model="reviewData.store_name"
            filled
            dense
            label="Supermercato"
          >
            <template #prepend><q-icon name="store" /></template>
          </q-input>
        </div>
        <div class="col-12 col-sm-4">
          <q-input
            v-model="reviewData.city"
            filled
            dense
            label="Città"
          >
            <template #prepend><q-icon name="location_on" /></template>
          </q-input>
        </div>
        <div class="col-12 col-sm-4">
          <q-input
            v-model="reviewData.date"
            filled
            dense
            label="Data (dd/mm/yyyy)"
          >
            <template #prepend><q-icon name="calendar_today" /></template>
          </q-input>
        </div>
      </div>

      <!-- Editable items table -->
      <q-table
        :rows="reviewData.items"
        :columns="reviewColumns"
        row-key="__idx"
        flat
        bordered
        dense
        :pagination="{ rowsPerPage: 0 }"
        hide-pagination
        class="q-mb-md"
      >
        <template #body="props">
          <q-tr :props="props">
            <q-td key="name" :props="props">
              <q-input
                v-model="props.row.name"
                dense
                borderless
                input-class="text-body2"
              />
            </q-td>
            <q-td key="price" :props="props">
              <q-input
                v-model.number="props.row.price"
                dense
                borderless
                type="number"
                step="0.01"
                input-class="text-body2 text-right text-weight-bold"
                prefix="€"
              />
            </q-td>
            <q-td key="actions" :props="props">
              <q-btn
                flat
                round
                dense
                icon="delete"
                color="negative"
                size="sm"
                @click="removeItem(props.rowIndex)"
              />
            </q-td>
          </q-tr>
        </template>
      </q-table>

      <div class="row q-gutter-sm q-mb-md">
        <q-btn
          outline
          color="grey-7"
          label="← Torna all'upload"
          icon="arrow_back"
          no-caps
          @click="backToUpload"
        />
        <q-space />
        <q-btn
          unelevated
          color="primary"
          label="Salva nel database"
          icon="save"
          no-caps
          size="lg"
          :loading="saving"
          :disable="reviewData.items.length === 0"
          @click="confirmSave"
        />
      </div>

      <!-- OCR debug -->
      <q-expansion-item v-if="ocrText" label="Testo OCR estratto" icon="text_fields" dense header-class="text-caption">
        <pre class="text-caption q-pa-sm bg-grey-2" style="white-space: pre-wrap; max-height: 200px; overflow: auto">{{ ocrText }}</pre>
      </q-expansion-item>
    </div>

    <!-- ═══════ STEP 3: Done ═══════ -->
    <div v-if="step === 'done'">
      <q-card>
        <q-card-section class="bg-positive text-white">
          <div class="row items-center">
            <q-icon name="check_circle" size="28px" class="q-mr-sm" />
            <div class="text-h6">{{ saveResult.message }}</div>
          </div>
        </q-card-section>

        <q-card-section v-if="saveResult.feedback?.length">
          <div class="text-subtitle2 q-mb-sm">Dettagli:</div>
          <q-list dense>
            <q-item v-for="(msg, idx) in saveResult.feedback" :key="idx" class="q-px-none">
              <q-item-section avatar style="min-width: 28px">
                <q-icon
                  :name="msg.includes('Nuovo') || msg.includes('aggiornato') ? 'check_circle' : 'info'"
                  :color="msg.includes('Nuovo') || msg.includes('aggiornato') ? 'positive' : 'info'"
                  size="xs"
                />
              </q-item-section>
              <q-item-section class="text-body2">{{ msg }}</q-item-section>
            </q-item>
          </q-list>
        </q-card-section>

        <q-card-actions class="q-pa-md">
          <q-btn
            outline
            color="primary"
            label="Scansiona un altro scontrino"
            icon="add_a_photo"
            no-caps
            @click="reset"
          />
          <q-btn
            flat
            color="primary"
            label="Vai ai prodotti"
            icon="shopping_bag"
            no-caps
            to="/"
          />
        </q-card-actions>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { scanReceipt, confirmReceipt } from '../services/api'

const step = ref('upload') // upload → review → done

// Upload state
const imageFile = ref(null)
const imageBase64 = ref(null)
const previewUrl = ref(null)
const analyzing = ref(false)
const error = ref(null)
const ocrText = ref(null)

// Review state
const reviewData = ref({ store_name: '', city: '', date: '', items: [] })
const reviewColumns = [
  { name: 'name', label: 'Prodotto', field: 'name', align: 'left', style: 'width: 70%' },
  { name: 'price', label: 'Prezzo', field: 'price', align: 'right', style: 'width: 20%' },
  { name: 'actions', label: '', field: '', align: 'center', style: 'width: 10%' },
]

// Save state
const saving = ref(false)
const saveResult = ref(null)

function onFileSelected(file) {
  if (!file) {
    imageBase64.value = null
    previewUrl.value = null
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    imageBase64.value = e.target.result
    previewUrl.value = e.target.result
  }
  reader.readAsDataURL(file)
}

async function analyze() {
  if (!imageBase64.value) return
  analyzing.value = true
  error.value = null
  ocrText.value = null

  try {
    const { data } = await scanReceipt(imageBase64.value)
    ocrText.value = data.ocr_text || null

    const receipt = data.receipt || {}
    reviewData.value = {
      store_name: (receipt.store_name || '').trim(),
      city: (receipt.city || '').trim(),
      date: (receipt.date || '').trim(),
      items: (receipt.items || [])
        .filter((i) => i.name && i.price)
        .map((i, idx) => ({ ...i, __idx: idx })),
    }

    step.value = 'review'
  } catch (err) {
    error.value = err.response?.data?.error || "Errore durante l'analisi"
    ocrText.value = err.response?.data?.ocr_text || null
  } finally {
    analyzing.value = false
  }
}

function removeItem(index) {
  reviewData.value.items.splice(index, 1)
}

function backToUpload() {
  step.value = 'upload'
}

async function confirmSave() {
  saving.value = true
  try {
    const { data } = await confirmReceipt({
      store_name: reviewData.value.store_name,
      city: reviewData.value.city,
      date: reviewData.value.date,
      items: reviewData.value.items.map((i) => ({ name: i.name, price: i.price })),
    })
    saveResult.value = data
    step.value = 'done'
  } catch (err) {
    error.value = err.response?.data?.error || 'Errore durante il salvataggio'
    step.value = 'upload'
  } finally {
    saving.value = false
  }
}

function reset() {
  step.value = 'upload'
  imageFile.value = null
  imageBase64.value = null
  previewUrl.value = null
  error.value = null
  ocrText.value = null
  reviewData.value = { store_name: '', city: '', date: '', items: [] }
  saveResult.value = null
}
</script>
