<template>
  <q-page padding style="max-width:860px; margin:0 auto">
    <div class="row items-center q-mb-lg">
      <q-btn flat dense icon="arrow_back" to="/rentals" color="grey-6" />
      <div class="q-ml-sm text-h6" style="font-weight:700">Umowa nr {{ rental?.id }}</div>
      <q-space />
      <q-badge :color="statusColor(rental?.status)" style="font-size:11px; padding:4px 10px; border-radius:6px">
        {{ statusLabel(rental?.status) }}
      </q-badge>
    </div>

    <div v-if="rental" class="q-gutter-y-md">
      <!-- Billing entity -->
      <q-card flat bordered>
        <q-card-section>
          <div class="field-label q-mb-sm">Wynajmujący</div>
          <q-option-group
            v-model="form.billing_entity"
            :options="billingOptions"
            color="primary"
            inline
            :disable="!editable"
          />
        </q-card-section>
      </q-card>

      <!-- Client -->
      <q-card flat bordered>
        <q-card-section>
          <div class="field-label q-mb-md">Najemca</div>
          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-6">
              <q-input v-model="form.client_name" label="Nazwa / Imię i nazwisko" dense :readonly="!editable" />
            </div>
            <div class="col-12 col-sm-6">
              <q-input v-model="form.client_nip" label="NIP / PESEL" dense :readonly="!editable" />
            </div>
            <div class="col-12 col-sm-8">
              <q-input v-model="form.client_address" label="Adres" dense :readonly="!editable" />
            </div>
            <div class="col-12 col-sm-4">
              <q-input v-model="form.client_phone" label="Telefon" dense :readonly="!editable" />
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Dates -->
      <q-card flat bordered>
        <q-card-section>
          <div class="field-label q-mb-md">Okres najmu</div>
          <div class="row q-col-gutter-md items-center">
            <div class="col-6 col-sm-3">
              <q-input v-model="form.start_date" label="Od" type="date" dense :readonly="!editable" />
            </div>
            <div class="col-6 col-sm-3">
              <q-input v-model="form.end_date" label="Do" type="date" dense :readonly="!editable" />
            </div>
            <div class="col-6 col-sm-3">
              <q-checkbox v-model="form.weekdays_only" label="Tylko robocze" dense :disable="!editable" />
            </div>
            <div class="col-6 col-sm-3">
              <q-checkbox v-model="form.align_to_monday" label="Wyrównaj do pon." dense :disable="!editable" />
            </div>
            <div class="col-12">
              <q-checkbox
                v-model="form.is_term_estimated"
                label="Termin orientacyjny"
                dense
                :disable="!editable"
              />
              <q-input
                v-if="form.is_term_estimated"
                v-model="form.term_note"
                label="Ustalenie terminu"
                placeholder="np. przewidywany zwrot po ok. 2 tygodniach, możliwe przedłużenie po kontakcie"
                maxlength="300"
                counter
                dense
                :readonly="!editable"
                class="q-mt-sm"
              />
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Rates -->
      <q-card flat bordered>
        <q-card-section>
          <div class="field-label q-mb-md">Wycena</div>
          <q-option-group
            v-model="form.billing_mode"
            :options="billingModeOptions"
            color="primary"
            inline
            :disable="!editable"
            class="q-mb-md"
          />
          <div v-if="form.billing_mode === 'daily'" class="row q-col-gutter-md">
            <div class="col-6 col-sm-4">
              <q-input v-model.number="form.rate_tier_1_7" label="Stawka 1–7 dni (zł)" type="number" dense :readonly="!editable" />
            </div>
            <div class="col-6 col-sm-4">
              <q-input v-model.number="form.rate_above_7" label="Stawka >7 dni (zł)" type="number" dense :readonly="!editable" />
            </div>
            <div class="col-12 col-sm-4">
              <q-checkbox v-model="form.flat_rate" label="Jedna stawka" dense :disable="!editable" />
            </div>
          </div>
          <div v-else class="row q-col-gutter-md">
            <div class="col-12 col-sm-4">
              <q-checkbox v-model="form.operator_included" label="Operator w usłudze" dense :disable="!editable" />
            </div>
            <div class="col-6 col-sm-4">
              <q-input v-model.number="form.operator_hours" label="Godziny" type="number" step="0.25" dense :readonly="!editable" />
            </div>
            <div class="col-6 col-sm-4">
              <q-input v-model.number="form.hourly_rate" label="Stawka godzinowa" type="number" step="0.01" dense :readonly="!editable" />
            </div>
          </div>
          <div class="row q-col-gutter-md q-mt-sm">
            <div class="col-6 col-sm-2">
              <q-input v-model.number="form.discount_pct" label="Rabat %" type="number" dense :readonly="!editable" />
            </div>
            <div class="col-6 col-sm-2">
              <q-input v-model.number="form.surcharge_pct" label="Dopłata %" type="number" dense :readonly="!editable" />
            </div>
            <div class="col-12 col-sm-4">
              <q-input v-model.number="form.transport_cost" label="Transport netto" type="number" step="0.01" dense :readonly="!editable" />
            </div>
            <div class="col-12 col-sm-4">
              <q-input v-model="form.transport_description" label="Opis transportu" dense :readonly="!editable" />
            </div>
          </div>
          <div class="manual-total-row q-mt-md" :class="{ active: form.manual_total_enabled }">
            <div class="row q-col-gutter-md items-center">
              <div class="col-12 col-sm">
                <q-checkbox
                  v-model="form.manual_total_enabled"
                  label="! Cena końcowa ręcznie"
                  dense
                  :disable="!editable"
                  @update:model-value="syncManualTotal"
                />
                <div class="text-caption text-grey-6 q-mt-xs">
                  Kwota końcowa netto nadpisuje wyliczenie systemowe.
                </div>
              </div>
              <div class="col-12 col-sm-4">
                <q-input
                  v-model.number="form.manual_total_netto"
                  label="Końcowa cena netto"
                  type="number"
                  step="0.01"
                  min="0"
                  suffix="zł"
                  dense
                  :readonly="!editable"
                  :disable="!form.manual_total_enabled"
                >
                  <template #prepend>
                    <q-icon name="priority_high" color="warning" />
                  </template>
                </q-input>
              </div>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Notes -->
      <q-card flat bordered>
        <q-card-section>
          <q-input v-model="form.notes" label="Uwagi" type="textarea" rows="2" dense :readonly="!editable" />
        </q-card-section>
      </q-card>

      <!-- Summary -->
      <q-card flat style="background:#f9f9f9; border:1px solid #eee">
        <q-card-section>
          <div class="row items-center justify-between">
            <div>
              <div class="text-caption text-grey-6">Dni najmu</div>
              <div class="text-h6">{{ rental.rental_days }} dni</div>
              <q-badge
                v-if="rental.is_term_estimated"
                color="amber-8"
                text-color="black"
                label="termin orientacyjny"
              />
            </div>
            <div>
              <div class="text-caption text-grey-6">Model</div>
              <div class="text-h6">{{ rental.billing_mode === 'hourly' ? 'Godzinowo' : 'Dobowo' }}</div>
            </div>
            <div class="text-right">
              <div class="text-caption text-grey-6">Wartość netto</div>
              <div class="text-h5" style="font-weight:800; color:#111">{{ rental.total_netto }} zł</div>
              <q-badge
                v-if="rental.manual_total_enabled"
                color="warning"
                text-color="black"
                icon="priority_high"
                label="cena ręczna"
              />
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Actions -->
      <div class="row q-gutter-sm">
        <template v-if="editable">
          <q-btn color="primary" label="Zapisz zmiany" :loading="saving" @click="save" />
          <q-btn flat label="Anuluj" @click="resetForm" />
        </template>
        <template v-else>
          <q-btn v-if="canOperate && rental.status !== 'returned' && rental.status !== 'cancelled'"
            outline color="primary" icon="edit" label="Edytuj" @click="editable = true" />
        </template>
        <q-btn outline color="deep-orange" icon="picture_as_pdf" label="PDF" @click="openPdf" />
      </div>
    </div>

    <div v-else class="text-center q-pa-xl text-grey-5">
      <q-spinner size="32px" />
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { api, errMsg } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const $q = useQuasar()
const auth = useAuthStore()
const rental = ref<any>(null)
const editable = ref(false)
const saving = ref(false)
const form = ref<any>({})
const canOperate = computed(() => auth.user?.role === 'biuro')

const billingOptions = [
  { value: 'topkop_jdg', label: '„TOP KOP Krzysztof Świtaj"' },
  { value: 'tk_spzoo',   label: 'TK Sp. z o.o.' },
]

const billingModeOptions = [
  { value: 'daily', label: 'Dobowo' },
  { value: 'hourly', label: 'Godzinowo z operatorem' },
]

function statusColor(s?: string) {
  return { draft: 'grey-5', active: 'positive', returned: 'blue-grey-5', cancelled: 'negative' }[s ?? ''] ?? 'grey'
}
function statusLabel(s?: string) {
  return { draft: 'Projekt', active: 'Aktywna', returned: 'Zwrócona', cancelled: 'Anulowana' }[s ?? ''] ?? s
}

function populateForm(r: any) {
  form.value = {
    billing_entity: r.billing_entity,
    client_name: r.client_name,
    client_nip: r.client_nip ?? '',
    client_address: r.client_address ?? '',
    client_phone: r.client_phone ?? '',
    start_date: r.start_date,
    end_date: r.end_date,
    is_term_estimated: r.is_term_estimated,
    term_note: r.term_note ?? '',
    weekdays_only: r.weekdays_only,
    align_to_monday: r.align_to_monday,
    rate_tier_1_7: r.rate_tier_1_7,
    rate_above_7: r.rate_above_7,
    flat_rate: r.flat_rate,
    billing_mode: r.billing_mode,
    operator_included: r.operator_included,
    operator_hours: r.operator_hours,
    hourly_rate: r.hourly_rate,
    transport_cost: r.transport_cost,
    transport_description: r.transport_description ?? '',
    discount_pct: r.discount_pct,
    surcharge_pct: r.surcharge_pct,
    manual_total_enabled: r.manual_total_enabled,
    manual_total_netto: r.manual_total_netto,
    notes: r.notes ?? '',
  }
}

function syncManualTotal(enabled: boolean) {
  if (!enabled) {
    form.value.manual_total_netto = null
    return
  }
  if (form.value.manual_total_netto === null && rental.value?.total_netto) {
    form.value.manual_total_netto = Number(rental.value.total_netto)
  }
}

function resetForm() {
  populateForm(rental.value)
  editable.value = false
}

async function save() {
  saving.value = true
  try {
    const payload: any = { ...form.value }
    // send nulls for empty strings
    if (!payload.client_nip) payload.client_nip = null
    if (!payload.client_address) payload.client_address = null
    if (!payload.client_phone) payload.client_phone = null
    if (payload.billing_mode !== 'hourly') {
      payload.operator_hours = null
      payload.hourly_rate = null
    }
    if (!payload.transport_description) payload.transport_description = null
    if (!payload.manual_total_enabled) payload.manual_total_netto = null
    if (!payload.is_term_estimated || !payload.term_note) payload.term_note = null
    if (!payload.notes) payload.notes = null
    const { data } = await api.patch(`/rentals/${route.params.id}`, payload)
    rental.value = data
    populateForm(data)
    editable.value = false
    $q.notify({ type: 'positive', message: 'Zapisano' })
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    saving.value = false
  }
}

async function openPdf() {
  const res = await api.get(`/rentals/${route.params.id}/pdf`, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  window.open(url, '_blank')
}

onMounted(async () => {
  const { data } = await api.get(`/rentals/${route.params.id}`)
  rental.value = data
  populateForm(data)
})
</script>

<style scoped>
.field-label { font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #aaa; }
.manual-total-row {
  background: rgba(251, 191, 36, 0.10);
  border: 1px solid rgba(180, 83, 9, 0.18);
  border-radius: 12px;
  padding: 12px;
}
.manual-total-row.active {
  border-color: rgba(180, 83, 9, 0.48);
}
</style>
