<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h5">Umowy</div>
      <q-space />
      <q-btn v-if="canOperate" color="primary" icon="add" label="Nowa" to="/rentals/new" />
    </div>

    <q-table
      :rows="rows"
      :columns="cols"
      row-key="id"
      :loading="loading"
      flat
      bordered
      dense
      @row-click="openRental"
    >
      <template #body-cell-to="{ row }">
        <q-td>
          <div>{{ row.end_date }}</div>
          <q-badge
            v-if="row.is_term_estimated"
            color="amber-8"
            text-color="black"
            label="orientacyjny"
            class="q-mt-xs"
          />
        </q-td>
      </template>

      <template #body-cell-status="{ row }">
        <q-td>
          <q-badge :color="statusColor(row.status)" :label="statusLabel(row.status)" />
        </q-td>
      </template>

      <template #body-cell-actions="{ row }">
        <q-td auto-width class="q-gutter-xs">
          <q-btn
            flat
            dense
            round
            :icon="canOperate && row.status !== 'returned' && row.status !== 'cancelled' ? 'edit' : 'visibility'"
            color="grey-8"
            :title="canOperate && row.status !== 'returned' && row.status !== 'cancelled' ? 'Edytuj' : 'Podgląd'"
            @click.stop="openRental(null, row)"
          />
          <q-btn flat dense round icon="picture_as_pdf" color="grey-7" title="Pobierz PDF"
            @click.stop="openPdf(row)" />
          <q-btn v-if="canOperate && row.status === 'draft'" flat dense round icon="play_arrow" color="positive"
            title="Aktywuj" @click.stop="changeStatus(row, 'active')" />
          <q-btn v-if="canOperate && row.status === 'active'" flat dense round icon="check_circle" color="primary"
            title="Zwróć (zakończ)" @click.stop="changeStatus(row, 'returned')" />
          <q-btn v-if="canOperate && (row.status === 'draft' || row.status === 'active')" flat dense round icon="cancel"
            color="warning" title="Anuluj" @click.stop="changeStatus(row, 'cancelled')" />
          <q-btn v-if="canOperate && row.status === 'active'" flat dense round icon="event_repeat" color="indigo"
            title="Przedłuż" @click.stop="openExtend(row)" />
          <q-btn v-if="canOperate && row.status !== 'active'" flat dense round icon="delete" color="negative"
            title="Usuń" @click.stop="confirmDelete(row)" />
        </q-td>
      </template>
    </q-table>

    <!-- Confirm delete -->
    <q-dialog v-model="dialog">
      <q-card style="min-width: 320px">
        <q-card-section>
          <div class="text-h6">Usunąć umowę?</div>
          <div class="text-body2 q-mt-sm">#{{ target?.id }} — {{ target?.client_name }}</div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Anuluj" v-close-popup />
          <q-btn color="negative" label="Usuń" :loading="deleting" @click="doDelete" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Przedłuż dialog -->
    <q-dialog v-model="extendDialog">
      <q-card style="min-width:320px">
        <q-card-section>
          <div class="text-h6">Przedłuż najem</div>
          <div class="text-body2 text-grey-6 q-mt-xs">#{{ extendTarget?.id }} — {{ extendTarget?.client_name }}</div>
          <div class="text-caption q-mt-xs">Aktualna data końca: <b>{{ extendTarget?.end_date }}</b></div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="extendDate" type="date" label="Nowa data końca" dense />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Anuluj" v-close-popup />
          <q-btn color="indigo" label="Przedłuż" :loading="extending" @click="doExtend" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Confirm status change -->
    <q-dialog v-model="statusDialog">
      <q-card style="min-width: 320px">
        <q-card-section>
          <div class="text-h6">{{ statusAction?.label }}</div>
          <div class="text-body2 q-mt-sm">#{{ statusAction?.row?.id }} — {{ statusAction?.row?.client_name }}</div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Anuluj" v-close-popup />
          <q-btn :color="statusAction?.color || 'primary'" label="Potwierdź"
            :loading="statusChanging" @click="doStatusChange" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Dialog: wyślij na serwis po zwrocie -->
    <q-dialog v-model="serviceDialog" persistent>
      <q-card style="min-width:320px">
        <q-card-section>
          <div class="text-h6">Wysłać sprzęt na serwis?</div>
          <div class="text-body2 text-grey-6 q-mt-xs">{{ serviceTarget?.client_name }}</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="serviceTitle" label="Opis (opcjonalnie)"
            :placeholder="`Przegląd po zwrocie — ${serviceTarget?.end_date}`" dense />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Nie, dziękuję" v-close-popup />
          <q-btn color="orange" icon="build" label="Tak, na serwis" :loading="serviceSending" @click="createServiceCard" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api, errMsg } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

const $q = useQuasar()
const router = useRouter()
const auth = useAuthStore()
const rows = ref<any[]>([])
const loading = ref(false)
const dialog = ref(false)
const deleting = ref(false)
const target = ref<any>(null)
const statusDialog = ref(false)
const statusChanging = ref(false)
const statusAction = ref<{ row: any; newStatus: string; label: string; color: string } | null>(null)
const extendDialog = ref(false)
const extendTarget = ref<any>(null)
const extendDate = ref('')
const extending = ref(false)
const serviceDialog = ref(false)
const serviceTarget = ref<any>(null)
const serviceTitle = ref('')
const serviceSending = ref(false)
const canOperate = computed(() => auth.user?.role === 'biuro')

const cols = [
  { name: 'id',      label: '#',      field: 'id',          align: 'left' as const },
  { name: 'client',  label: 'Klient', field: 'client_name', align: 'left' as const },
  { name: 'from',    label: 'Od',     field: 'start_date',  align: 'left' as const },
  { name: 'to',      label: 'Do',     field: 'end_date',    align: 'left' as const },
  { name: 'days',    label: 'Dni',    field: 'rental_days', align: 'right' as const },
  { name: 'total',   label: 'Netto',  field: 'total_netto', align: 'right' as const },
  { name: 'status',  label: 'Status', field: 'status',      align: 'left' as const },
  { name: 'actions', label: '',       field: 'actions',     align: 'center' as const },
]

function statusColor(s: string) {
  return { draft: 'grey', active: 'positive', returned: 'blue-grey', cancelled: 'negative' }[s] ?? 'grey'
}
function statusLabel(s: string) {
  return { draft: 'Szkic', active: 'Aktywna', returned: 'Zwrócona', cancelled: 'Anulowana' }[s] ?? s
}

function openRental(_evt: Event | null, row: any) {
  router.push(`/rentals/${row.id}`)
}

async function openPdf(row: any) {
  try {
    const resp = await api.get(`/rentals/${row.id}/pdf`, { responseType: 'blob' })
    const mime = resp.headers['content-type'] || 'application/pdf'
    const url = URL.createObjectURL(new Blob([resp.data], { type: mime }))
    const a = document.createElement('a')
    a.href = url
    a.target = '_blank'
    // если сервер вернул PDF — открыть в новой вкладке; HTML fallback — скачать
    if (mime.includes('pdf')) {
      window.open(url, '_blank')
    } else {
      a.download = `umowa_${row.id}.html`
      a.click()
    }
    setTimeout(() => URL.revokeObjectURL(url), 10_000)
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  }
}

function changeStatus(row: any, newStatus: string) {
  const labels: Record<string, { label: string; color: string }> = {
    active:    { label: 'Aktywować umowę?',   color: 'positive' },
    returned:  { label: 'Oznaczyć jako zwróconą?', color: 'primary' },
    cancelled: { label: 'Anulować umowę?',    color: 'warning' },
  }
  statusAction.value = { row, newStatus, ...labels[newStatus] }
  statusDialog.value = true
}

async function doStatusChange() {
  if (!statusAction.value) return
  statusChanging.value = true
  try {
    const { data } = await api.patch(`/rentals/${statusAction.value.row.id}/status`, {
      new_status: statusAction.value.newStatus
    })
    const idx = rows.value.findIndex(r => r.id === data.id)
    if (idx !== -1) rows.value[idx] = data
    statusDialog.value = false
    $q.notify({ type: 'positive', message: `Status zmieniony: ${statusLabel(data.status)}` })
    // po zwrocie — zaproponuj serwis
    if (data.status === 'returned') {
      serviceTarget.value = data
      serviceTitle.value = ''
      serviceDialog.value = true
    }
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    statusChanging.value = false
  }
}

function openExtend(row: any) {
  extendTarget.value = row
  extendDate.value = row.end_date
  extendDialog.value = true
}

async function doExtend() {
  if (!extendTarget.value || !extendDate.value) return
  extending.value = true
  try {
    const { data } = await api.patch(`/rentals/${extendTarget.value.id}`, { end_date: extendDate.value })
    const idx = rows.value.findIndex(r => r.id === data.id)
    if (idx !== -1) rows.value[idx] = data
    extendDialog.value = false
    $q.notify({ type: 'positive', message: `Przedłużono do ${data.end_date} (${data.rental_days} dni)` })
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    extending.value = false
  }
}

async function createServiceCard() {
  if (!serviceTarget.value) return
  serviceSending.value = true
  try {
    const title = serviceTitle.value.trim() ||
      `Przegląd po zwrocie — ${serviceTarget.value.end_date}`
    await api.post('/kanban', {
      equipment_id: serviceTarget.value.equipment_id,
      rental_id: serviceTarget.value.id,
      title,
      priority: 'high',
      due_date: serviceTarget.value.end_date,
      source: 'rental_return',
      checklist: [
        { label: 'Sprawdzić stan techniczny', sort_order: 0 },
        { label: 'Nasmarować', sort_order: 1 },
        { label: 'Uzupełnić płyny', sort_order: 2 },
      ],
    })
    serviceDialog.value = false
    $q.notify({ type: 'positive', message: 'Karta serwisowa dodana do Warsztatu' })
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    serviceSending.value = false
  }
}

function confirmDelete(row: any) { target.value = row; dialog.value = true }

async function doDelete() {
  deleting.value = true
  try {
    await api.delete(`/rentals/${target.value.id}`)
    rows.value = rows.value.filter(r => r.id !== target.value.id)
    dialog.value = false
    $q.notify({ type: 'positive', message: 'Umowa usunięta' })
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    deleting.value = false }
}

async function load() {
  loading.value = true
  try { rows.value = (await api.get('/rentals')).data }
  finally { loading.value = false }
}

onMounted(load)
</script>
