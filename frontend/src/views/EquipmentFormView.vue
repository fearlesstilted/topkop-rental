<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">{{ isEdit ? 'Edycja sprzętu' : 'Nowy sprzęt' }}</div>
    <q-form @submit.prevent="save" class="q-gutter-md" style="max-width:600px">
      <q-select v-model="form.category_id" :options="categories" option-value="id" option-label="name_pl" emit-value map-options label="Kategoria" />
      <q-input v-model="form.code" label="Kod (unikalny)" :disable="isEdit" required />
      <q-input v-model="form.name" label="Nazwa" required />
      <div class="row q-col-gutter-sm">
        <q-input class="col" v-model="form.manufacturer" label="Producent" />
        <q-input class="col" v-model="form.model" label="Model" />
        <q-input class="col-3" v-model.number="form.year" type="number" label="Rok" />
      </div>
      <q-input v-model="form.registration_number" label="Nr rejestracyjny" hint="np. WB 12345 — do szybkiego wyszukiwania" />
      <q-select v-model="form.tracking_type" :options="trackingOpts" emit-value map-options label="Tryb pomiaru" />
      <div class="row q-col-gutter-sm">
        <q-input class="col" v-model.number="form.rate_tier_1_7" type="number" step="0.01" label="Stawka 1-7 dni (zł)" required />
        <q-input class="col" v-model.number="form.rate_above_7" type="number" step="0.01" label="Stawka >7 dni (zł)" required />
      </div>
      <div class="row q-col-gutter-sm">
        <q-input class="col" v-model.number="form.daily_limit" type="number" label="Dzienny limit (mth/rbh)" />
        <q-input class="col" v-model.number="form.overage_rate" type="number" step="0.01" label="Stawka nadgodzin (zł)" />
      </div>
      <q-input v-model="form.notes" type="textarea" label="Uwagi" />
      <q-btn type="submit" color="primary" :label="isEdit ? 'Zapisz' : 'Dodaj'" :loading="busy" />
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api, errMsg } from '@/lib/api'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()

const isEdit = computed(() => !!route.params.id)
const busy = ref(false)
const categories = ref<any[]>([])
const trackingOpts = [
  { value: 'mth', label: 'MTH (motogodziny)' },
  { value: 'rbh', label: 'RBH (roboczogodziny)' },
  { value: 'daily', label: 'Tylko dni' }
]

const form = ref<any>({
  category_id: null, code: '', name: '',
  manufacturer: '', model: '', year: null,
  registration_number: '',
  tracking_type: 'daily',
  rate_tier_1_7: 0, rate_above_7: 0,
  daily_limit: null, overage_rate: null, notes: ''
})

onMounted(async () => {
  const { data } = await api.get('/equipment/categories')
  categories.value = data
  if (isEdit.value) {
    const r = await api.get(`/equipment/${route.params.id}`)
    form.value = { ...r.data }
  } else if (categories.value.length) {
    form.value.category_id = categories.value[0].id
    form.value.tracking_type = categories.value[0].default_tracking
  }
})

async function save() {
  busy.value = true
  try {
    if (isEdit.value) {
      await api.patch(`/equipment/${route.params.id}`, form.value)
    } else {
      await api.post('/equipment', form.value)
    }
    $q.notify({ type: 'positive', message: 'Zapisano' })
    router.push('/equipment')
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    busy.value = false
  }
}
</script>
