<template>
  <q-page class="flex flex-center">
    <q-card style="width: 400px; max-width: 90vw">
      <q-card-section class="bg-primary text-white">
        <div class="text-h6">Registrati</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit.prevent="onSubmit" class="q-gutter-sm">
          <q-input
            v-model="form.username"
            filled
            label="Username"
            :rules="[
              val => !!val || 'Campo obbligatorio',
              val => val.length >= 3 || 'Minimo 3 caratteri',
            ]"
          >
            <template #prepend><q-icon name="person" /></template>
          </q-input>

          <q-input
            v-model="form.email"
            filled
            label="Email"
            type="email"
            :rules="[
              val => !!val || 'Campo obbligatorio',
              val => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val) || 'Email non valida',
            ]"
          >
            <template #prepend><q-icon name="email" /></template>
          </q-input>

          <q-input
            v-model="form.password"
            filled
            :type="showPassword ? 'text' : 'password'"
            label="Password"
            :rules="[
              val => !!val || 'Campo obbligatorio',
              val => val.length >= 6 || 'Minimo 6 caratteri',
            ]"
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

          <q-input
            v-model="form.confirmPassword"
            filled
            :type="showPassword ? 'text' : 'password'"
            label="Conferma Password"
            :rules="[
              val => !!val || 'Campo obbligatorio',
              val => val === form.password || 'Le password non coincidono',
            ]"
          >
            <template #prepend><q-icon name="lock" /></template>
          </q-input>

          <q-btn
            type="submit"
            color="primary"
            label="Registrati"
            class="full-width q-mt-md"
            :loading="submitting"
          />
        </q-form>
      </q-card-section>

      <q-separator />

      <q-card-section class="text-center">
        <span class="text-grey-6">Hai già un account?</span>
        <q-btn flat dense no-caps color="primary" label="Accedi" to="/login" />
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const showPassword = ref(false)
const submitting = ref(false)

async function onSubmit() {
  submitting.value = true
  const ok = await auth.register(form.username, form.email, form.password)
  submitting.value = false

  if (ok) {
    router.push('/')
  }
}
</script>
