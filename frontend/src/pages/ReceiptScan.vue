<template>
  <q-page class="page-container">
    <h1 class="text-h5 q-mb-md">📸 Scansiona Scontrino</h1>
    <p class="text-body2 text-grey-7 q-mb-lg">
      Scatta una foto al tuo scontrino o carica un'immagine. L'OCR estrarrà i prodotti e i prezzi automaticamente.
    </p>

    <div class="row q-col-gutter-lg">
      <!-- Upload area -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Carica immagine</div>

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

            <!-- Preview -->
            <div v-if="previewUrl" class="q-mt-md">
              <q-img :src="previewUrl" style="max-height: 300px" fit="contain" />
            </div>

            <q-btn
              v-if="imageBase64"
              color="primary"
              label="Analizza scontrino"
              icon="document_scanner"
              class="full-width q-mt-md"
              :loading="processing"
              @click="processReceipt"
            />
          </q-card-section>
        </q-card>
      </div>

      <!-- Results -->
      <div class="col-12 col-md-6">
        <q-card v-if="result">
          <q-card-section class="bg-positive text-white">
            <div class="text-subtitle1">Risultato analisi</div>
          </q-card-section>

          <q-card-section>
            <div class="q-mb-sm">
              <strong>Supermercato:</strong> {{ result.receipt?.store_name || '-' }}
            </div>
            <div class="q-mb-md">
              <strong>Data:</strong> {{ result.receipt?.date || '-' }}
            </div>

            <div class="text-subtitle2 q-mb-sm">Prodotti trovati:</div>
            <q-list bordered separator dense>
              <q-item v-for="(item, idx) in result.receipt?.items || []" :key="idx">
                <q-item-section>{{ item.name }}</q-item-section>
                <q-item-section side>€{{ Number(item.price).toFixed(2) }}</q-item-section>
              </q-item>
            </q-list>

            <div v-if="result.feedback?.length" class="q-mt-md">
              <div class="text-subtitle2 q-mb-sm">Dettagli aggiornamento DB:</div>
              <q-list dense>
                <q-item v-for="(msg, idx) in result.feedback" :key="idx" class="text-caption">
                  <q-item-section avatar>
                    <q-icon name="info" color="info" size="xs" />
                  </q-item-section>
                  <q-item-section>{{ msg }}</q-item-section>
                </q-item>
              </q-list>
            </div>
          </q-card-section>
        </q-card>

        <q-card v-if="error">
          <q-card-section class="bg-negative text-white">
            <div class="text-subtitle1">Errore</div>
          </q-card-section>
          <q-card-section>{{ error }}</q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { scanReceipt } from '../services/api'

const imageFile = ref(null)
const imageBase64 = ref(null)
const previewUrl = ref(null)
const processing = ref(false)
const result = ref(null)
const error = ref(null)

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

async function processReceipt() {
  if (!imageBase64.value) return
  processing.value = true
  result.value = null
  error.value = null

  try {
    const { data } = await scanReceipt(imageBase64.value)
    result.value = data
  } catch (err) {
    error.value = err.response?.data?.error || 'Errore durante l\'elaborazione dello scontrino'
  } finally {
    processing.value = false
  }
}
</script>
