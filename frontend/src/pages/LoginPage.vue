<template>
  <q-page class="flex flex-center">
    <q-card style="width: 400px; max-width: 90vw">
      <q-card-section class="bg-primary text-white">
        <div class="text-h6">Accedi</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit.prevent="onSubmit" class="q-gutter-sm">
          <q-input
            v-model="form.login"
            filled
            label="Username o Email"
            :rules="[val => !!val || 'Campo obbligatorio']"
          >
            <template #prepend><q-icon name="person" /></template>
          </q-input>

          <q-input
            v-model="form.password"
            filled
            :type="showPassword ? 'text' : 'password'"
            label="Password"
            :rules="[val => !!val || 'Campo obbligatorio']"
          >
            <template #prepend><q-icon name="lock" /></template>
            <template #append>
              <q-icon
                :name="showPassword ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="showPassword = !showPassword"
              />
            </template>
          </q-input>

          <q-btn
            type="submit"
            color="primary"
            label="Accedi"
            class="full-width q-mt-md"
            :loading="submitting"
          />
        </q-form>
      </q-card-section>

      <q-separator />

      <q-card-section class="text-center">
        <span class="text-grey-6">Non hai un account?</span>
        <q-btn flat dense no-caps color="primary" label="Registrati" to="/register" />
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ login: '', password: '' })
const showPassword = ref(false)
const submitting = ref(false)

async function onSubmit() {
  submitting.value = true
  const ok = await auth.login(form.login, form.password)
  submitting.value = false

  if (ok) {
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  }
}
</script>
