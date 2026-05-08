<template>
  <q-page padding style="max-width:680px; margin:0 auto">
    <div class="text-h6 q-mb-lg" style="font-weight:700">Kategorie sprzętu</div>

    <q-list bordered separator class="q-mb-xl">
      <q-item v-for="c in list" :key="c.id">
        <q-item-section v-if="editId !== c.id">
          <q-item-label style="font-weight:600">{{ c.name_pl }}</q-item-label>
          <q-item-label caption>{{ c.slug }} · {{ trackingLabel(c.default_tracking) }}</q-item-label>
        </q-item-section>

        <q-item-section v-else>
          <div class="row q-col-gutter-sm items-center">
            <div class="col-12 col-sm-5">
              <q-input v-model="editForm.name_pl" label="Nazwa" dense />
            </div>
            <div class="col-12 col-sm-4">
              <q-select v-model="editForm.default_tracking" :options="opts" emit-value map-options label="Pomiar" dense />
            </div>
            <div class="col-auto">
              <q-input v-model.number="editForm.sort_order" label="Sort" type="number" dense style="width:70px" />
            </div>
          </div>
        </q-item-section>

        <q-item-section side>
          <div class="row q-gutter-xs">
            <template v-if="editId === c.id">
              <q-btn flat dense round icon="check" color="positive" size="sm" :loading="saving" @click="saveEdit(c.id)" />
              <q-btn flat dense round icon="close" color="grey" size="sm" @click="cancelEdit" />
            </template>
            <template v-else>
              <q-btn flat dense round icon="edit" color="grey-6" size="sm" @click="startEdit(c)" />
            </template>
          </div>
        </q-item-section>
      </q-item>
    </q-list>

    <div class="text-subtitle2 q-mb-sm" style="font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#aaa; font-size:10px">Dodaj kategorię</div>
    <q-form @submit.prevent="add" class="q-gutter-sm">
      <div class="row q-col-gutter-sm">
        <div class="col-12 col-sm-3">
          <q-input v-model="form.slug" label="Slug" dense required />
        </div>
        <div class="col-12 col-sm-4">
          <q-input v-model="form.name_pl" label="Nazwa" dense required />
        </div>
        <div class="col-12 col-sm-3">
          <q-select v-model="form.default_tracking" :options="opts" emit-value map-options label="Pomiar" dense />
        </div>
        <div class="col-auto">
          <q-btn type="submit" color="primary" label="Dodaj" dense :loading="busy" style="margin-top:4px" />
        </div>
      </div>
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api, errMsg } from '@/lib/api'

const list = ref<any[]>([])
const busy = ref(false)
const saving = ref(false)
const $q = useQuasar()
const form = ref({ slug: '', name_pl: '', default_tracking: 'daily' })
const editId = ref<number | null>(null)
const editForm = ref({ name_pl: '', default_tracking: 'daily', sort_order: 0 })

const opts = [
  { value: 'mth', label: 'MTH' }, { value: 'rbh', label: 'RBH' }, { value: 'daily', label: 'Dni' }
]

function trackingLabel(t: string) {
  return { mth: 'MTH', rbh: 'RBH', daily: 'Dni' }[t] ?? t
}

function startEdit(c: any) {
  editId.value = c.id
  editForm.value = { name_pl: c.name_pl, default_tracking: c.default_tracking, sort_order: c.sort_order }
}

function cancelEdit() { editId.value = null }

async function saveEdit(id: number) {
  saving.value = true
  try {
    const { data } = await api.patch(`/equipment/categories/${id}`, editForm.value)
    const idx = list.value.findIndex(c => c.id === id)
    if (idx !== -1) list.value[idx] = data
    editId.value = null
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    saving.value = false
  }
}

async function load() {
  const { data } = await api.get('/equipment/categories')
  list.value = data
}

async function add() {
  busy.value = true
  try {
    await api.post('/equipment/categories', form.value)
    form.value = { slug: '', name_pl: '', default_tracking: 'daily' }
    await load()
  } catch (e: any) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
