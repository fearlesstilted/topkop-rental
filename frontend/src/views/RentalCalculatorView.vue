<template>
  <q-page padding class="pricing-page">
    <div class="pricing-hero q-mb-lg">
      <div>
        <div class="text-overline text-grey-7">TopKop wycena</div>
        <h1>Nowa umowa</h1>
        <p>Dobowo bez operatora albo godzinowo z operatorem. Transport jako osobna pozycja.</p>
      </div>
      <q-btn flat color="primary" icon="arrow_back" label="Umowy" to="/rentals" />
    </div>

    <div class="row q-col-gutter-xl">
      <q-form class="col-12 col-lg-8 q-gutter-lg" @submit.prevent="submit">
        <section class="pricing-card">
          <div class="section-head">
            <div>
              <div class="section-kicker">01</div>
              <h2>Model rozliczenia</h2>
            </div>
            <q-badge color="dark" outline>{{ modeLabel }}</q-badge>
          </div>

          <div class="mode-grid">
            <button
              type="button"
              class="mode-card"
              :class="{ active: form.billing_mode === 'daily' }"
              @click="setMode('daily')"
            >
              <q-icon name="calendar_month" size="28px" />
              <strong>Bez operatora</strong>
              <span>Rozliczenie za doby / dni robocze.</span>
            </button>
            <button
              type="button"
              class="mode-card"
              :class="{ active: form.billing_mode === 'hourly' }"
              @click="setMode('hourly')"
            >
              <q-icon name="engineering" size="28px" />
              <strong>Z operatorem</strong>
              <span>Rozliczenie godzinowe: godziny × stawka.</span>
            </button>
          </div>

          <q-select
            v-model="form.equipment_id"
            :options="equipment"
            option-value="id"
            option-label="label"
            emit-value
            map-options
            label="Sprzęt"
            @update:model-value="applyEquipment"
          />

          <div class="row q-col-gutter-md">
            <q-input class="col-12 col-sm-6" v-model="form.start_date" type="date" label="Data od" required />
            <q-input class="col-12 col-sm-6" v-model="form.end_date" type="date" label="Data do" required />
          </div>
          <div class="term-box q-mt-md">
            <q-toggle
              v-model="form.is_term_estimated"
              label="Termin orientacyjny"
              color="primary"
            />
            <div class="text-caption text-grey-7">
              Dla małego sprzętu: klient mówi „około 2 tygodnie”, ale może oddać później.
              W umowie zostaje data przewidywana, a nie twarde zobowiązanie systemowe.
            </div>
            <q-input
              v-if="form.is_term_estimated"
              v-model="form.term_note"
              class="q-mt-sm"
              label="Ustalenie terminu"
              placeholder="np. przewidywany zwrot po ok. 2 tygodniach, możliwe przedłużenie po kontakcie"
              maxlength="300"
              counter
            />
          </div>

          <div v-if="form.billing_mode === 'daily'" class="q-gutter-md">
            <div class="row q-gutter-sm">
              <q-toggle v-model="form.weekdays_only" label="Tylko dni robocze" />
              <q-toggle v-model="form.align_to_monday" label="Start od poniedziałku" />
              <q-toggle v-model="form.flat_rate" label="Jedna stawka" />
              <q-toggle v-model="form.operator_included" label="Operator w cenie" />
            </div>
            <div class="row q-col-gutter-md">
              <q-input class="col-12 col-sm-6" v-model.number="form.rate_tier_1_7" type="number" step="0.01" label="Stawka 1-7 dni" suffix="zł" />
              <q-input class="col-12 col-sm-6" v-model.number="form.rate_above_7" type="number" step="0.01" label="Stawka >7 dni" suffix="zł" :disable="form.flat_rate" />
            </div>
          </div>

          <div v-else class="operator-panel">
            <q-toggle v-model="form.operator_included" label="Operator jest w usłudze" />
            <div class="row q-col-gutter-md">
              <q-input class="col-12 col-sm-6" v-model.number="form.operator_hours" type="number" step="0.25" label="Liczba godzin" suffix="h" />
              <q-input class="col-12 col-sm-6" v-model.number="form.hourly_rate" type="number" step="0.01" label="Stawka godzinowa" suffix="zł/h" />
            </div>
          </div>

          <div class="row q-col-gutter-md">
            <q-input class="col-12 col-sm-6" v-model.number="form.discount_pct" type="number" step="0.1" label="Rabat" suffix="%" />
            <q-input class="col-12 col-sm-6" v-model.number="form.surcharge_pct" type="number" step="0.1" label="Dopłata" suffix="%" />
          </div>

          <div class="manual-total-box q-mt-md" :class="{ active: form.manual_total_enabled }">
            <div class="row items-center q-col-gutter-md">
              <div class="col-12 col-md">
                <q-toggle
                  v-model="form.manual_total_enabled"
                  color="warning"
                  checked-icon="priority_high"
                  unchecked-icon="calculate"
                  label="Cena końcowa ręcznie"
                  @update:model-value="syncManualTotal"
                />
                <div class="text-caption text-grey-7 q-mt-xs">
                  Użyj, gdy cena jest dogadana telefonicznie i systemowy wzór ma nie nadpisywać kwoty.
                </div>
              </div>
              <div class="col-12 col-md-4">
                <q-input
                  v-model.number="form.manual_total_netto"
                  type="number"
                  step="0.01"
                  min="0"
                  label="Końcowa cena netto"
                  suffix="zł"
                  :disable="!form.manual_total_enabled"
                  :rules="manualTotalRules"
                >
                  <template #prepend>
                    <q-icon name="priority_high" color="warning" />
                  </template>
                </q-input>
              </div>
            </div>
          </div>
        </section>

        <section class="pricing-card">
          <div class="section-head">
            <div>
              <div class="section-kicker">02</div>
              <h2>Transport</h2>
            </div>
            <q-icon name="local_shipping" color="primary" size="28px" />
          </div>
          <div class="transport-strip">
            <q-input v-model.number="form.transport_cost" type="number" step="0.01" label="Koszt transportu netto" suffix="zł" />
            <q-input v-model="form.transport_description" label="Opis transportu" placeholder="np. Gołdap → klient, 8 zł/km" />
          </div>
          <div class="quick-transport">
            <q-btn flat dense label="0 zł" @click="form.transport_cost = 0" />
            <q-btn flat dense label="7 zł/km" @click="appendTransportRate('7 zł/km')" />
            <q-btn flat dense label="8 zł/km" @click="appendTransportRate('8 zł/km')" />
          </div>
        </section>

        <section class="pricing-card">
          <div class="section-head">
            <div>
              <div class="section-kicker">03</div>
              <h2>Najemca</h2>
            </div>
          </div>

          <div class="row q-col-gutter-md items-end">
            <q-input
              class="col-12 col-md"
              v-model="form.client_nip"
              label="NIP / PESEL"
              hint="Firma: wpisz NIP i kliknij Szukaj"
              @keyup.enter="lookupNip"
            />
            <div class="col-12 col-md-auto">
              <q-btn outline color="primary" label="Szukaj" icon="search" :loading="nipLoading" @click="lookupNip" />
            </div>
          </div>

          <q-select
            v-model="clientSearch"
            use-input
            hide-selected
            fill-input
            input-debounce="300"
            :options="clientOptions"
            option-label="name"
            label="Historia klientów"
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
          </q-select>

          <q-input v-model="form.client_name" label="Nazwa / imię i nazwisko" required />
          <div class="row q-col-gutter-md">
            <q-input class="col-12 col-sm-5" v-model="form.client_phone" label="Telefon" />
            <q-input class="col-12 col-sm-7" v-model="form.client_address" label="Adres" />
          </div>
        </section>

        <section class="pricing-card">
          <div class="section-head">
            <div>
              <div class="section-kicker">04</div>
              <h2>Umowa</h2>
            </div>
          </div>
          <div class="field-label q-mb-xs">Wystaw umowę na</div>
          <q-option-group v-model="form.billing_entity" :options="billingEntityOptions" color="primary" inline />
          <q-input class="q-mt-md" v-model="form.notes" type="textarea" rows="3" label="Uwagi do umowy" />
        </section>

        <div class="mobile-submit">
          <q-btn type="submit" color="primary" size="lg" label="Zapisz umowę" :loading="busy" class="full-width" />
        </div>
      </q-form>

      <aside class="col-12 col-lg-4">
        <q-card flat class="summary-card">
          <q-card-section>
            <div class="text-overline text-grey-7">Podsumowanie netto</div>
            <div class="summary-total">{{ displayTotal }} zł</div>
            <div class="text-body2 text-grey-7">{{ modeLabel }}</div>
            <q-badge
              v-if="form.manual_total_enabled"
              color="warning"
              text-color="black"
              icon="priority_high"
              label="Cena ręczna"
              class="q-mt-sm"
            />
          </q-card-section>

          <q-separator />

          <q-card-section class="q-gutter-sm">
            <div class="summary-row">
              <span>Okres</span>
              <strong>{{ calc?.days ?? '-' }} dni</strong>
            </div>
            <div class="summary-row">
              <span>Ilość rozliczeniowa</span>
              <strong>{{ calc?.billable_quantity ?? '-' }} {{ form.billing_mode === 'hourly' ? 'h' : 'dni' }}</strong>
            </div>
            <div v-if="form.billing_mode === 'daily' && calc && !form.flat_rate" class="mini-breakdown">
              <div>1-7 dni: {{ calc.tier1_days }} × {{ form.rate_tier_1_7 }} = {{ calc.tier1_amount }} zł</div>
              <div>>7 dni: {{ calc.tier2_days }} × {{ form.rate_above_7 }} = {{ calc.tier2_amount }} zł</div>
            </div>
            <div v-if="form.billing_mode === 'hourly'" class="mini-breakdown">
              <div>{{ form.operator_hours || 0 }} h × {{ form.hourly_rate || 0 }} zł/h</div>
            </div>
            <div class="summary-row">
              <span>Usługa</span>
              <strong>{{ calc?.rental_amount ?? '-' }} zł</strong>
            </div>
            <div class="summary-row">
              <span>Transport</span>
              <strong>{{ calc?.transport_cost ?? '0.00' }} zł</strong>
            </div>
            <div v-if="form.manual_total_enabled && calc" class="mini-breakdown warning">
              Wyliczenie systemu: {{ calc.total_netto }} zł. Do umowy trafi kwota ręczna.
            </div>
          </q-card-section>

          <q-card-actions class="q-pa-md">
            <q-btn type="submit" color="primary" size="lg" label="Zapisz umowę" :loading="busy" class="full-width" @click="submit" />
          </q-card-actions>
        </q-card>
      </aside>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api, errMsg } from '@/lib/api'

type BillingMode = 'daily' | 'hourly'

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
  client_name: '',
  client_nip: '',
  client_address: '',
  client_phone: '',
  start_date: new Date().toISOString().slice(0, 10),
  end_date: new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 10),
  is_term_estimated: false,
  term_note: '',
  weekdays_only: true,
  align_to_monday: true,
  rate_tier_1_7: 0,
  rate_above_7: 0,
  flat_rate: false,
  billing_mode: 'daily' as BillingMode,
  operator_included: false,
  operator_hours: null,
  hourly_rate: null,
  daily_limit: null,
  overage_rate: null,
  transport_cost: 0,
  transport_description: '',
  discount_pct: 0,
  surcharge_pct: 0,
  manual_total_enabled: false,
  manual_total_netto: null,
  billing_entity: 'topkop_jdg',
  notes: ''
})

const billingEntityOptions = [
  { label: 'TOP KOP Krzysztof Świtaj', value: 'topkop_jdg' },
  { label: 'TK Sp. z o.o.', value: 'tk_spzoo' }
]

const modeLabel = computed(() => (
  form.value.billing_mode === 'hourly'
    ? 'Z operatorem · godzinowo'
    : form.value.operator_included
      ? 'Dobowo · operator w cenie'
      : 'Bez operatora · dobowo'
))

const manualTotalRules = [
  (value: number | null) => !form.value.manual_total_enabled || value !== null || 'Podaj cenę',
  (value: number | null) => !form.value.manual_total_enabled || Number(value) >= 0 || 'Cena musi być >= 0'
]

const displayTotal = computed(() => {
  if (form.value.manual_total_enabled && form.value.manual_total_netto !== null) {
    return Number(form.value.manual_total_netto).toFixed(2)
  }
  return calc.value?.total_netto ?? '—'
})

onMounted(async () => {
  const { data } = await api.get('/equipment')
  equipment.value = data.map((item: any) => ({
    ...item,
    label: `${item.code} · ${item.name}`
  }))
  if (data[0]) {
    form.value.equipment_id = data[0].id
    applyEquipment(data[0].id)
  }
  await recalc()
})

function setMode(mode: BillingMode): void {
  form.value.billing_mode = mode
  if (mode === 'hourly') {
    form.value.operator_included = true
    form.value.weekdays_only = false
    form.value.align_to_monday = false
    if (!form.value.operator_hours) form.value.operator_hours = 8
    if (!form.value.hourly_rate) form.value.hourly_rate = form.value.overage_rate || form.value.rate_tier_1_7 || 0
    return
  }
  form.value.operator_included = false
}

function applyEquipment(id: number | null): void {
  const selected = equipment.value.find((item) => item.id === id)
  if (!selected) return
  form.value.rate_tier_1_7 = Number(selected.rate_tier_1_7)
  form.value.rate_above_7 = Number(selected.rate_above_7)
  form.value.daily_limit = selected.daily_limit
  form.value.overage_rate = selected.overage_rate ? Number(selected.overage_rate) : null
  if (form.value.billing_mode === 'hourly' && !form.value.hourly_rate) {
    form.value.hourly_rate = form.value.overage_rate || form.value.rate_tier_1_7
  }
}

function appendTransportRate(text: string): void {
  form.value.transport_description = form.value.transport_description
    ? `${form.value.transport_description}; ${text}`
    : text
}

function syncManualTotal(enabled: boolean): void {
  if (!enabled) {
    form.value.manual_total_netto = null
    return
  }
  if (form.value.manual_total_netto === null && calc.value?.total_netto) {
    form.value.manual_total_netto = Number(calc.value.total_netto)
  }
}

async function lookupNip(): Promise<void> {
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
    const source = data.source === 'local' ? 'z historii' : 'MF Biała Lista'
    $q.notify({ type: 'positive', message: `Uzupełniono dane (${source})` })
  } catch (error: any) {
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Nie znaleziono' })
  } finally {
    nipLoading.value = false
  }
}

async function filterClients(value: string, update: (fn: () => void) => void): Promise<void> {
  update(async () => {
    if (!value || value.length < 2) {
      clientOptions.value = []
      return
    }
    try {
      const { data } = await api.get('/utils/clients', { params: { q: value } })
      clientOptions.value = data
    } catch {
      clientOptions.value = []
    }
  })
}

function applyClient(client: any): void {
  if (!client) return
  form.value.client_name = client.name
  form.value.client_nip = client.nip || form.value.client_nip
  form.value.client_address = client.address || form.value.client_address
  form.value.client_phone = client.phone || form.value.client_phone
}

let recalcTimer: number | null = null
watch(form, () => {
  if (recalcTimer) clearTimeout(recalcTimer)
  recalcTimer = window.setTimeout(recalc, 180)
}, { deep: true })

async function recalc(): Promise<void> {
  try {
    const { data } = await api.post('/rentals/calculate', {
      start_date: form.value.start_date,
      end_date: form.value.end_date,
      weekdays_only: form.value.weekdays_only,
      align_to_monday: form.value.align_to_monday,
      rate_tier_1_7: form.value.rate_tier_1_7,
      rate_above_7: form.value.rate_above_7,
      flat_rate: form.value.flat_rate,
      billing_mode: form.value.billing_mode,
      operator_included: form.value.operator_included,
      operator_hours: form.value.operator_hours,
      hourly_rate: form.value.hourly_rate,
      transport_cost: form.value.transport_cost || 0,
      discount_pct: form.value.discount_pct,
      surcharge_pct: form.value.surcharge_pct
    })
    calc.value = data
  } catch {
    calc.value = null
  }
}

function normalizedPayload(): any {
  return {
    ...form.value,
    client_nip: form.value.client_nip || null,
    client_address: form.value.client_address || null,
    client_phone: form.value.client_phone || null,
    operator_hours: form.value.billing_mode === 'hourly' ? form.value.operator_hours : null,
    hourly_rate: form.value.billing_mode === 'hourly' ? form.value.hourly_rate : null,
    transport_cost: form.value.transport_cost || 0,
    transport_description: form.value.transport_description || null,
    manual_total_enabled: form.value.manual_total_enabled,
    manual_total_netto: form.value.manual_total_enabled ? form.value.manual_total_netto : null,
    term_note: form.value.is_term_estimated ? (form.value.term_note || null) : null,
    notes: form.value.notes || null
  }
}

async function submit(): Promise<void> {
  busy.value = true
  try {
    const { data } = await api.post('/rentals', normalizedPayload())
    $q.notify({ type: 'positive', message: `Umowa nr ${data.id} utworzona` })
    router.push(`/rentals/${data.id}`)
  } catch (error: any) {
    $q.notify({ type: 'negative', message: errMsg(error) })
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.pricing-page {
  background:
    radial-gradient(circle at top left, rgba(14, 116, 144, 0.12), transparent 28%),
    radial-gradient(circle at top right, rgba(202, 138, 4, 0.10), transparent 26%),
    linear-gradient(180deg, #f8fafc 0%, #ffffff 42%);
  min-height: 100%;
}

.pricing-hero,
.pricing-card,
.summary-card {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 24px;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
}

.pricing-hero {
  align-items: center;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 22px;
}

.pricing-hero h1,
.section-head h2 {
  color: #0f172a;
  font-family: Georgia, "Times New Roman", serif;
  font-weight: 700;
  line-height: 1.05;
  margin: 0;
}

.pricing-hero h1 {
  font-size: clamp(2rem, 5vw, 3.5rem);
}

.pricing-hero p {
  color: #64748b;
  margin: 8px 0 0;
  max-width: 680px;
}

.pricing-card {
  padding: 22px;
}

.section-head {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 18px;
}

.section-kicker {
  color: #0891b2;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.mode-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-bottom: 18px;
}

.mode-card {
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.10);
  border-radius: 18px;
  color: #0f172a;
  cursor: pointer;
  display: grid;
  gap: 6px;
  min-height: 132px;
  padding: 18px;
  text-align: left;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}

.mode-card span {
  color: #64748b;
  font-size: 13px;
  line-height: 1.45;
}

.mode-card.active,
.mode-card:hover {
  border-color: #0891b2;
  box-shadow: 0 16px 30px rgba(8, 145, 178, 0.16);
  transform: translateY(-1px);
}

.operator-panel,
.term-box,
.manual-total-box,
.transport-strip {
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.07);
  border-radius: 18px;
  padding: 16px;
}

.manual-total-box {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.13), rgba(248, 250, 252, 0.94));
  border-color: rgba(180, 83, 9, 0.18);
}

.manual-total-box.active {
  border-color: rgba(180, 83, 9, 0.52);
  box-shadow: 0 16px 34px rgba(180, 83, 9, 0.13);
}

.transport-strip {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(160px, 0.4fr) 1fr;
}

.quick-transport {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.summary-card {
  position: sticky;
  top: 20px;
}

.summary-total {
  color: #0f172a;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2.3rem, 5vw, 3.6rem);
  font-weight: 800;
  letter-spacing: -0.04em;
}

.summary-row {
  align-items: center;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.summary-row span,
.mini-breakdown {
  color: #64748b;
  font-size: 13px;
}

.summary-row strong {
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.mini-breakdown {
  background: #f8fafc;
  border-radius: 12px;
  padding: 10px;
}

.mini-breakdown.warning {
  background: rgba(251, 191, 36, 0.14);
  color: #92400e;
}

.field-label {
  color: #64748b;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1.4px;
  text-transform: uppercase;
}

.mobile-submit {
  display: none;
}

@media (max-width: 1023px) {
  .summary-card {
    position: static;
  }
}

@media (max-width: 700px) {
  .pricing-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .mode-grid,
  .transport-strip {
    grid-template-columns: 1fr;
  }

  .mobile-submit {
    display: block;
  }
}
</style>
