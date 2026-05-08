<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Protokół {{ form.type === 'pickup' ? 'wydania' : 'zwrotu' }}</div>

    <q-form @submit.prevent="submit" class="q-gutter-md" style="max-width:640px">
      <q-select v-model="form.equipment_id" :options="equipment" option-value="id" option-label="name" emit-value map-options label="Sprzęt" />
      <q-btn-toggle v-model="form.type" :options="[{label:'Wydanie', value:'pickup'}, {label:'Zwrot', value:'return'}]" toggle-color="primary" />
      <q-input v-model.number="form.meter_reading" type="number" step="0.1" label="Stan licznika (mth/rbh)" />

      <div class="row q-gutter-sm items-center">
        <q-btn outline icon="my_location" :label="gpsLabel" :loading="gpsBusy" @click="captureGps" />
        <span v-if="form.lat" class="text-caption">{{ form.lat.toFixed(6) }}, {{ form.lon.toFixed(6) }}</span>
      </div>

      <div class="row q-col-gutter-sm">
        <div class="col-6 col-sm-4"><PhotoSlot label="Przód" @change="(f:any) => setPhoto('front', f)" /></div>
        <div class="col-6 col-sm-4"><PhotoSlot label="Tył" @change="(f:any) => setPhoto('back', f)" /></div>
        <div class="col-6 col-sm-4"><PhotoSlot label="Lewa" @change="(f:any) => setPhoto('left', f)" /></div>
        <div class="col-6 col-sm-4"><PhotoSlot label="Prawa" @change="(f:any) => setPhoto('right', f)" /></div>
        <div class="col-6 col-sm-4"><PhotoSlot label="Licznik" @change="(f:any) => setPhoto('meter', f)" /></div>
      </div>

      <q-input v-model="form.client_signer_name" label="Podpisujący (imię i nazwisko)" />
      <div>
        <div class="text-caption">Podpis klienta:</div>
        <SignaturePad :width="320" :height="140" @change="(url) => form.signature_data_url = url" />
      </div>

      <q-input v-model="form.notes" type="textarea" label="Uwagi" />

      <div v-if="validationError" class="text-negative text-caption q-mb-sm">{{ validationError }}</div>
      <q-btn type="submit" color="primary" :label="online ? 'Wyślij' : 'Zapisz offline'"
        :loading="busy" :disable="!!validationError" />
      <q-btn v-if="queued > 0" flat color="warning" :label="`W kolejce: ${queued}`" @click="flush" />
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'
import { api, errMsg } from '@/lib/api'
import SignaturePad from '@/components/SignaturePad.vue'
import PhotoSlot from '@/components/PhotoSlot.vue'
import { enqueueInspection, flushQueue, listQueued } from '@/composables/useOfflineQueue'

const $q = useQuasar()
const router = useRouter()
const online = ref(navigator.onLine)
const queued = ref(0)
const equipment = ref<any[]>([])
const busy = ref(false)
const gpsBusy = ref(false)

const REQUIRED_SLOTS = ['front', 'back', 'left', 'right', 'meter']

const photos = ref<Record<string, File | null>>({})
const form = ref<any>({
  equipment_id: null, type: 'pickup',
  meter_reading: null, lat: null, lon: null, gps_accuracy_m: null,
  client_signer_name: '', notes: '', signature_data_url: null
})

const gpsLabel = computed(() => form.value.lat ? 'GPS OK' : 'Pobierz GPS')

const validationError = computed(() => {
  const missing = REQUIRED_SLOTS.filter(s => !photos.value[s])
  if (missing.length > 0) return `Brakuje zdjęć: ${missing.join(', ')}`
  if (!form.value.signature_data_url) return 'Wymagany podpis klienta'
  return null
})

onMounted(async () => {
  const { data } = await api.get('/equipment')
  equipment.value = data
  if (data[0]) form.value.equipment_id = data[0].id
  queued.value = (await listQueued()).length
  window.addEventListener('online', () => { online.value = true; flush() })
  window.addEventListener('offline', () => { online.value = false })
})

function setPhoto(slot: string, file: File | null) {
  photos.value[slot] = file
}

function captureGps() {
  if (!navigator.geolocation) {
    $q.notify({ type: 'warning', message: 'GPS niedostępny' })
    return
  }
  gpsBusy.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      form.value.lat = pos.coords.latitude
      form.value.lon = pos.coords.longitude
      form.value.gps_accuracy_m = pos.coords.accuracy
      gpsBusy.value = false
    },
    (err) => {
      $q.notify({ type: 'negative', message: `GPS: ${err.message}` })
      gpsBusy.value = false
    },
    { enableHighAccuracy: true, timeout: 10000 }
  )
}

function uuid() {
  return crypto.randomUUID()
}

async function sendToServer(payload: any, photoEntries: [string, File][]) {
  const fd = new FormData()
  fd.append('payload', JSON.stringify(payload))
  fd.append('photo_slots', JSON.stringify(photoEntries.map(([slot]) => slot)))
  for (const [, file] of photoEntries) fd.append('photos', file)
  await api.post('/inspections', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
}

async function submit() {
  busy.value = true
  try {
    const payload = { ...form.value, client_local_id: uuid() }
    const photoEntries = Object.entries(photos.value).filter(([, v]) => v) as [string, File][]
    if (online.value) {
      await sendToServer(payload, photoEntries)
      $q.notify({ type: 'positive', message: 'Wysłane' })
      router.push('/inspections')
    } else {
      await enqueueInspection({
        client_local_id: payload.client_local_id,
        payload,
        photos: photoEntries.map(([slot, file]) => ({ slot, blob: file })),
        signature_data_url: form.value.signature_data_url ?? undefined,
        created_at: Date.now()
      })
      queued.value += 1
      $q.notify({ type: 'info', message: 'Zapisane offline' })
      router.push('/inspections')
    }
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    busy.value = false
  }
}

async function flush() {
  const synced = await flushQueue(async (it) => {
    const photoEntries = it.photos.map((p) => [p.slot, new File([p.blob], `${p.slot}.jpg`)] as [string, File])
    await sendToServer(it.payload, photoEntries)
    return true
  })
  if (synced > 0) $q.notify({ type: 'positive', message: `Zsynchronizowano: ${synced}` })
  queued.value = (await listQueued()).length
}
</script>
