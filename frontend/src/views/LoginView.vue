<template>
  <q-page style="background:#0a0a0a; min-height:100vh" class="flex flex-center">
    <div style="width:100%; max-width:340px; padding:24px">
      <!-- Logo -->
      <div class="text-center q-mb-xl">
        <img src="/topkop_logo.webp" alt="TOP KOP" style="height:32px; filter:invert(1); opacity:0.9; margin-bottom:16px" />
        <div style="font-size:11px; letter-spacing:3px; text-transform:uppercase; color:rgba(255,255,255,0.3); font-weight:600">
          System zarządzania
        </div>
      </div>

      <!-- Card -->
      <div style="background:#161616; border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:28px">
        <div style="font-size:18px; font-weight:700; color:#fff; margin-bottom:4px">Zaloguj się</div>
        <div style="font-size:12px; color:rgba(255,255,255,0.35); margin-bottom:24px; font-weight:500">
          Wpisz swój PIN
        </div>

        <!-- PIN dots visualization -->
        <div class="flex flex-center q-mb-md" style="gap:10px">
          <div
            v-for="i in 4"
            :key="i"
            :style="`
              width:12px; height:12px; border-radius:50%;
              transition:background 0.15s;
              background:${pin.length >= i ? '#f59e0b' : 'rgba(255,255,255,0.12)'}
            `"
          />
        </div>

        <q-input
          v-model="pin"
          type="password"
          inputmode="numeric"
          pattern="[0-9]*"
          autofocus
          maxlength="6"
          standout="bg-grey-10 text-white"
          :error="!!err"
          :error-message="err"
          placeholder="••••"
          style="--q-field-input-text-color:#fff"
          input-style="text-align:center; font-size:1.4rem; letter-spacing:8px; color:#fff"
          @keyup.enter="submit"
        />

        <q-btn
          unelevated
          :loading="busy"
          class="full-width q-mt-md"
          style="background:#f59e0b; color:#000; font-weight:700; font-size:14px; height:44px; border-radius:10px; letter-spacing:0.3px"
          label="Wejdź"
          @click="submit"
        />
      </div>

      <div style="text-align:center; margin-top:20px; font-size:11px; color:rgba(255,255,255,0.18); font-weight:500">
        TOP KOP Gołdap · {{ new Date().getFullYear() }}
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const pin = ref('')
const err = ref('')
const busy = ref(false)
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

async function submit() {
  if (!pin.value.trim()) return
  err.value = ''
  busy.value = true
  try {
    await auth.login(pin.value.trim())
    router.push((route.query.next as string) || '/')
  } catch (error: unknown) {
    err.value = axios.isAxiosError(error) && error.code === 'ECONNABORTED'
      ? 'Serwer startuje po uśpieniu. Spróbuj ponownie za chwilę.'
      : 'Nieprawidłowy PIN'
    pin.value = ''
  } finally {
    busy.value = false
  }
}
</script>
