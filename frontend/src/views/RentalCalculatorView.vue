<template>
  <q-page padding>
    <div class="text-h6 q-mb-lg" style="font-weight:700">Nowa umowa</div>
    <div class="row q-col-gutter-lg">
      <q-form class="col-12 col-md-7 q-gutter-sm" @submit.prevent="submit">

        <!-- Sprzęt -->
        <q-select v-model="form.equipment_id" :options="equipment" option-value="id" option-label="name"
          emit-value map-options label="Sprzęt" @update:model-value="applyEquipment" />

        <!-- Daty -->
        <div class="row q-col-gutter-sm">
          <q-input class="col" v-model="form.start_date" type="date" label="Data od" required />
          <q-input class="col" v-model="form.end_date" type="date" label="Data do" required />
        </div>
        <div class="row q-gutter-sm">
          <q-toggle v-model="form.weekdays_only" label="Tylko dni robocze (pn-pt)" />
          <q-toggle v-model="form.align_to_monday" label="Przesuń start na poniedziałek" />
          <q-toggle v-model="form.flat_rate" label="Stawka stała (bez tier)" />
        </div>
        <div class="row q-col-gutter-sm">
          <q-input class="col" v-model.number="form.rate_tier_1_7" type="number" step="0.01" label="Stawka 1-7 dni (zł)" />
          <q-input class="col" v-model.number="form.rate_above_7" type="number" step="0.01" label="Stawka >7 dni (zł)" :disable="form.flat_rate" />
        </div>
        <div class="row q-col-gutter-sm">
          <q-input class="col" v-model.number="form.discount_pct" type="number" step="0.1" label="Rabat %" />
          <q-input class="col" v-model.number="form.surcharge_pct" type="number" step="0.1" label="Dopłata %" />
        </div>
        <div class="row q-col-gutter-sm">
          <q-input class="col" v-model.number="form.daily_limit" type="number" label="Dzienny limit" />
          <q-input class="col" v-model.number="form.overage_rate" type="number" step="0.01" label="Stawka nadgodzin" />
        </div>

        <q-separator class="q-my-md" />

        <!-- Wystawca -->
        <div class="field-label q-mb-xs">Wystaw umowę na</div>
        <q-option-group v-model="form.billing_entity" :options="billingEntityOptions" color="primary" inline />

        <q-separator class="q-my-md" />

        <!-- Najemca -->
        <div class="field-label q-mb-sm">Najemca</div>

        <!-- NIP z lookup -->
        <div class="row q-col-gutter-sm items-end">
          <div class="col">
            <q-input v-model="form.client_nip" label="NIP / PESEL (opcjonalnie)"
              hint="Firma: wpisz NIP i kliknij Szukaj · Osoba fizyczna: PESEL lub zostaw puste"
              @keyup.enter="lookupNip" />
          </div>
          <div class="col-auto">
            <q-btn outline color="primary" label="Szukaj" icon="search" :loading="nipLoading"
              @click="lookupNip" style="margin-bottom:20px" />
          </div>
        </div>

        <!-- Autocomplete z historii -->
        <q-select
          v-model="clientSearch"
          use-input
          hide-selected
          fill-input
          input-debounce="300"
          :options="clientOptions"
          option-label="name"
          label="Lub szukaj po nazwie klienta (historia)"
          hint="Poprzedni klienci — kliknij aby uzupełnić"
          @filter="filterClients"
          @update:model-value="applyClient"
          clearable
        >
          <template #option="{ opt, itemProps }">
            <q-item v-bind="itemProps">
              <q-item-section>
                <q-item-label>{{ opt.name }}</q-item-label>
                <q-item-label caption>{{ opt.nip ? 'NIP: ' + opt.nip : '' }} {{ opt.phone }}</q-item-label>
              </q-item-section>
            </q-item>
          </template>
          <template #no-option>
            <q-item><q-item-section class="text-grey">Brak wyników</q-item-section></q-item>
          </template>
        </q-select>

        <q-input v-model="form.client_name" label="Nazwa / imię i nazwisko" required />
        <div class="row q-col-gutter-sm">
          <q-input class="col" v-model="form.client_phone" label="Telefon" />
        </div>
        <q-input v-model="form.client_address" label="Adres" />
        <q-input v-model="form.notes" type="textarea" label="Uwagi" />

        <q-btn type="submit" color="primary" label="Zapisz umowę" :loading="busy" />
      </q-form>

      <!-- Podgląd kalkulatora -->
      <div class="col-12 col-md-5">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1" style="font-weight:700">Podgląd</div>
            <div class="q-mt-sm">Dni naliczone: <b>{{ calc?.days ?? '-' }}</b></div>
            <div v-if="calc && !form.flat_rate">Tier 1-7: {{ calc.tier1_days }} × {{ form.rate_tier_1_7 }} = {{ calc.tier1_amount }} zł</div>
            <div v-if="calc && !form.flat_rate">Tier >7: {{ calc.tier2_days }} × {{ form.rate_above_7 }} = {{ calc.tier2_amount }} zł</div>
            <div v-if="calc">Suma: {{ calc.subtotal }} zł</div>
            <div v-if="calc && calc.adjustment_pct !== '0'">Korekta: {{ calc.adjustment_pct }}% = {{ calc.adjustment_amount }} zł</div>
            <div class="text-h6 q-mt-sm">Razem netto: <b>{{ calc?.total_netto ?? '-' }} zł</b></div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api, errMsg } from '@/lib/api'

const router = useRouter()
const $q = useQuasar()
const equipment = ref<any[]>([])
const calc = ref<any>(null)
const busy = ref(false)
const nipLoading = ref(false)
const clientSearch = ref<any>(null)
const clientOptions = ref<any[]>([])

const form = ref<any>({
  equipment_id: null,
  client_name: '', client_nip: '', client_address: '', client_phone: '',
  start_date: new Date().toISOString().slice(0, 10),
  end_date: new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 10),
  weekdays_only: true, align_to_monday: true,
  rate_tier_1_7: 0, rate_above_7: 0,
  flat_rate: false, daily_limit: null, overage_rate: null,
  discount_pct: 0, surcharge_pct: 0,
  billing_entity: 'topkop_jdg', notes: ''
})

const billingEntityOptions = [
  { label: 'TOP KOP Krzysztof Świtaj', value: 'topkop_jdg' },
  { label: 'TK Sp. z o.o.', value: 'tk_spzoo' }
]

onMounted(async () => {
  const { data } = await api.get('/equipment')
  equipment.value = data
  if (data[0]) { form.value.equipment_id = data[0].id; applyEquipment(data[0].id) }
  await recalc()  // pierwsze przeliczenie po załadowaniu stawek
})

function applyEquipment(id: number | null) {
  const eq = equipment.value.find((e) => e.id === id)
  if (!eq) return
  form.value.rate_tier_1_7 = Number(eq.rate_tier_1_7)
  form.value.rate_above_7 = Number(eq.rate_above_7)
  form.value.daily_limit = eq.daily_limit
  form.value.overage_rate = eq.overage_rate ? Number(eq.overage_rate) : null
}

async function lookupNip() {
  const nip = form.value.client_nip?.replace(/[^0-9]/g, '')
  if (!nip || nip.length !== 10) {
    $q.notify({ type: 'warning', message: 'NIP musi mieć dokładnie 10 cyfr' })
    return
  }
  nipLoading.value = true
  try {
    const { data } = await api.get(`/utils/nip/${nip}`)
    form.value.client_name = data.name
    form.value.client_address = data.address || form.value.client_address
    if (data.phone) form.value.client_phone = data.phone
    form.value.client_nip = nip
    const src = data.source === 'local' ? 'z historii' : 'MF Biała Lista'
    $q.notify({ type: 'positive', message: `Uzupełniono dane (${src})` })
  } catch (e: any) {
    $q.notify({ type: 'negative', message: e.response?.data?.detail || 'Nie znaleziono' })
  } finally {
    nipLoading.value = false
  }
}

async function filterClients(val: string, update: (fn: () => void) => void) {
  update(async () => {
    if (!val || val.length < 2) { clientOptions.value = []; return }
    try {
      const { data } = await api.get('/utils/clients', { params: { q: val } })
      clientOptions.value = data
    } catch { clientOptions.value = [] }
  })
}

function applyClient(c: any) {
  if (!c) return
  form.value.client_name = c.name
  form.value.client_nip = c.nip || form.value.client_nip
  form.value.client_address = c.address || form.value.client_address
  form.value.client_phone = c.phone || form.value.client_phone
}

let t: number | null = null
watch(form, () => {
  if (t) clearTimeout(t)
  t = window.setTimeout(recalc, 200)
}, { deep: true })

async function recalc() {
  try {
    const { data } = await api.post('/rentals/calculate', {
      start_date: form.value.start_date, end_date: form.value.end_date,
      weekdays_only: form.value.weekdays_only, align_to_monday: form.value.align_to_monday,
      rate_tier_1_7: form.value.rate_tier_1_7, rate_above_7: form.value.rate_above_7,
      flat_rate: form.value.flat_rate, discount_pct: form.value.discount_pct, surcharge_pct: form.value.surcharge_pct
    })
    calc.value = data
  } catch { calc.value = null }
}

async function submit() {
  busy.value = true
  try {
    const { data } = await api.post('/rentals', form.value)
    $q.notify({ type: 'positive', message: `Umowa nr ${data.id} utworzona` })
    router.push(`/rentals/${data.id}`)
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.field-label { font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #aaa; }
</style>
