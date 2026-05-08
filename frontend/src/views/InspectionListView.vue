<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h5">Protokoły</div>
      <q-space />
      <q-btn color="primary" icon="add" label="Nowy" to="/inspections/new" />
    </div>

    <!-- Filtry -->
    <div class="row q-col-gutter-sm q-mb-md">
      <div class="col-12 col-sm-5">
        <q-input v-model="search" dense outlined clearable placeholder="Szukaj klienta / sprzętu…" debounce="200">
          <template #prepend><q-icon name="search" /></template>
        </q-input>
      </div>
      <div class="col-auto">
        <q-btn-toggle
          v-model="period"
          dense no-caps
          :options="[
            { label: '7 dni', value: 7 },
            { label: '30 dni', value: 30 },
            { label: 'Wszystkie', value: 0 }
          ]"
          toggle-color="primary"
        />
      </div>
    </div>

    <q-list bordered separator>
      <q-item v-for="i in filtered" :key="i.id" class="q-py-sm">
        <q-item-section>
          <q-item-label>
            <q-badge :color="i.type === 'pickup' ? 'positive' : 'blue-grey'" class="q-mr-xs">
              {{ i.type === 'pickup' ? 'Wydanie' : 'Zwrot' }}
            </q-badge>
            #{{ i.id }} · {{ i.equipment_code || ('sprzęt ' + i.equipment_id) }}
          </q-item-label>
          <q-item-label caption>
            {{ i.client_signer_name || '—' }} · {{ new Date(i.created_at).toLocaleString('pl-PL') }}
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn flat round dense icon="picture_as_pdf" color="grey-7" title="Pobierz PDF" @click="openPdf(i)" />
        </q-item-section>
      </q-item>
      <q-item v-if="filtered.length === 0 && !loading">
        <q-item-section><q-item-label caption>Brak wyników</q-item-label></q-item-section>
      </q-item>
    </q-list>

    <div v-if="loading" class="flex flex-center q-mt-lg"><q-spinner size="2rem" /></div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '@/lib/api'

const $q = useQuasar()
const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const period = ref(30)

const filtered = computed(() => {
  let list = items.value
  if (period.value > 0) {
    const cutoff = Date.now() - period.value * 86_400_000
    list = list.filter(i => new Date(i.created_at).getTime() >= cutoff)
  }
  const q = search.value.trim().toLowerCase()
  if (q) {
    list = list.filter(i =>
      (i.client_signer_name || '').toLowerCase().includes(q) ||
      (i.equipment_code || '').toLowerCase().includes(q) ||
      String(i.equipment_id).includes(q)
    )
  }
  return list
})

onMounted(async () => {
  loading.value = true
  try { items.value = (await api.get('/inspections')).data }
  finally { loading.value = false }
})

async function openPdf(item: any) {
  try {
    const res = await api.get(`/inspections/${item.id}/pdf`, { responseType: 'blob' })
    const mime = res.headers['content-type'] || 'application/pdf'
    const url = URL.createObjectURL(new Blob([res.data], { type: mime }))
    if (mime.includes('pdf')) {
      window.open(url, '_blank')
    } else {
      const a = document.createElement('a')
      a.href = url; a.download = `protokol_${item.id}.html`; a.click()
    }
    setTimeout(() => URL.revokeObjectURL(url), 10_000)
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd pobierania PDF' })
  }
}
</script>
