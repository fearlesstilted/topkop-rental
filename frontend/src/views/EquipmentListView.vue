<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h6" style="font-weight:700">Park maszyn</div>
      <q-space />
      <q-input v-model="search" dense outlined placeholder="Szukaj kodu, nazwy, rejestracji…"
        style="width:240px" clearable class="q-mr-sm">
        <template #prepend><q-icon name="search" /></template>
      </q-input>
      <q-btn color="primary" icon="add" label="Nowy" to="/equipment/new" />
    </div>

    <q-table :rows="filtered" :columns="cols" row-key="id" :loading="loading" flat bordered dense>
      <template #body-cell-status="{ row }">
        <q-td>
          <q-badge :color="statusColor(row.status)" :label="statusLabel(row.status)" />
        </q-td>
      </template>
      <template #body-cell-actions="{ row }">
        <q-td auto-width>
          <q-btn flat dense round icon="edit" color="grey" @click.stop="$router.push(`/equipment/${row.id}`)" />
          <q-btn flat dense round icon="delete" color="negative" @click.stop="confirmDelete(row)" />
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="dialog">
      <q-card>
        <q-card-section>
          <div class="text-h6">Usunąć sprzęt?</div>
          <div class="text-body2 q-mt-sm">{{ target?.code }} — {{ target?.name }}</div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Anuluj" v-close-popup />
          <q-btn color="negative" label="Usuń" :loading="deleting" @click="doDelete" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, errMsg } from '@/lib/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const rows = ref<any[]>([])
const loading = ref(false)
const dialog = ref(false)
const deleting = ref(false)
const target = ref<any>(null)
const search = ref('')

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return rows.value
  return rows.value.filter(r =>
    r.code.toLowerCase().includes(q) ||
    r.name.toLowerCase().includes(q) ||
    (r.registration_number || '').toLowerCase().includes(q) ||
    (r.manufacturer || '').toLowerCase().includes(q)
  )
})

const cols = [
  { name: 'code',   label: 'Kod',      field: 'code',                align: 'left' as const },
  { name: 'reg',    label: 'Rej.',      field: 'registration_number', align: 'left' as const },
  { name: 'name',   label: 'Nazwa',     field: 'name',                align: 'left' as const },
  { name: 'rate1',  label: '1-7 dni',   field: 'rate_tier_1_7',       align: 'right' as const },
  { name: 'rate2',  label: '>7 dni',    field: 'rate_above_7',        align: 'right' as const },
  { name: 'status', label: 'Status',    field: 'status',              align: 'left' as const },
  { name: 'actions',label: '',          field: 'actions',             align: 'center' as const },
]

function statusColor(s: string) {
  return { available: 'positive', rented: 'primary', service: 'warning', broken: 'negative' }[s] ?? 'grey'
}
function statusLabel(s: string) {
  return { available: 'Wolny', rented: 'Wynajęty', service: 'Serwis', broken: 'Uszkodzony' }[s] ?? s
}

async function load() {
  loading.value = true
  try { rows.value = (await api.get('/equipment')).data }
  finally { loading.value = false }
}

function confirmDelete(row: any) { target.value = row; dialog.value = true }

async function doDelete() {
  deleting.value = true
  try {
    await api.delete(`/equipment/${target.value.id}`)
    rows.value = rows.value.filter(r => r.id !== target.value.id)
    dialog.value = false
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally { deleting.value = false }
}

onMounted(load)
</script>
