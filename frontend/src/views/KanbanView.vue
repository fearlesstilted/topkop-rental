<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h6" style="font-weight:700">Warsztat</div>
      <q-badge :color="connected ? 'positive' : 'grey'" class="q-ml-sm" style="font-size:10px">
        {{ connected ? 'online' : 'offline' }}
      </q-badge>
      <q-space />
      <q-btn color="primary" icon="add" label="Nowa karta" @click="openCreate" />
    </div>

    <div class="row q-col-gutter-md">
      <div v-for="col in columns" :key="col.key" class="col-12 col-sm-6 col-md-3">
        <div :class="`kanban-col kanban-col-${col.key}`">
          <div class="kanban-col-header">
            {{ col.label }}
            <span class="kanban-col-count">{{ byColumn(col.key).length }}</span>
          </div>

          <div class="q-mt-sm">
            <div v-for="card in byColumn(col.key)" :key="card.id" class="q-mb-sm">
              <q-card flat class="kanban-card">
                <q-card-section class="q-pa-md">
                  <div class="row items-start no-wrap q-mb-sm">
                    <div class="col text-body2" style="font-weight:600; line-height:1.3">{{ card.title }}</div>
                    <q-btn v-if="canDelete" flat dense round icon="close" color="negative" size="xs"
                      @click.stop="confirmDelete(card)" />
                  </div>

                  <div v-if="card.checklist.length" class="q-mb-sm">
                    <div v-for="it in card.checklist" :key="it.id" class="row items-center no-wrap">
                      <q-checkbox
                        :model-value="it.done"
                        dense size="sm"
                        @update:model-value="(v) => toggle(card, it, Boolean(v))"
                      />
                      <span class="q-ml-xs" :class="it.done ? 'text-strike text-grey-5' : 'text-body2'">
                        {{ it.label }}
                      </span>
                    </div>
                    <q-linear-progress
                      :value="doneRatio(card)"
                      :color="doneRatio(card) === 1 ? 'positive' : 'primary'"
                      rounded size="4px"
                      class="q-mt-sm"
                    />
                  </div>

                  <q-input
                    dense
                    :model-value="workerDraft[card.id] ?? card.assigned_worker ?? ''"
                    label="Kto robi"
                    placeholder="— nieprzydzielone —"
                    class="q-mt-xs"
                    @update:model-value="(v) => setWorkerDraft(card.id, v)"
                    @blur="saveWorker(card)"
                    @keyup.enter="saveWorker(card)"
                  />

                  <div v-if="col.key === 'gotowe'" class="q-mt-sm">
                    <q-btn
                      unelevated dense size="sm" color="teal" icon="check_circle" label="Oznacz jako wydaną"
                      class="full-width"
                      @click="moveToWydana(card)"
                    />
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </div>
      </div>
    </div>

    <q-dialog v-model="deleteDialog">
      <q-card style="min-width:280px">
        <q-card-section>
          <div class="text-h6">Usunąć kartę?</div>
          <div class="text-body2 q-mt-sm text-grey-6">{{ deleteTarget?.title }}</div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Anuluj" v-close-popup />
          <q-btn color="negative" label="Usuń" :loading="deleting" @click="doDelete" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="showCreate">
      <q-card style="min-width:340px">
        <q-card-section><div class="text-h6">Nowa karta serwisowa</div></q-card-section>
        <q-card-section class="q-pt-none q-gutter-sm">
          <q-select v-model="newCard.equipment_id" :options="equipment" option-value="id" option-label="name"
            emit-value map-options label="Sprzęt" />
          <q-input v-model="newCard.title" label="Tytuł / opis problemu" />
          <q-input v-model="checklistText" type="textarea" rows="4" label="Lista zadań (po linii)" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Anuluj" v-close-popup />
          <q-btn color="primary" label="Dodaj" @click="create" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { api, errMsg } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { useKanbanSocket } from '@/composables/useKanbanSocket'

const $q = useQuasar()
const auth = useAuthStore()

type WorkshopColumn = 'na_serwis' | 'w_trakcie' | 'gotowe' | 'wydana'

type ChecklistItem = {
  id: number
  label: string
  done: boolean
}

type WorkshopCard = {
  id: number
  equipment_id: number
  title: string
  column: WorkshopColumn
  assigned_worker: string | null
  checklist: ChecklistItem[]
}

type EquipmentOption = {
  id: number
  name: string
}

type NewCardForm = {
  equipment_id: number | null
  title: string
}

const cards = ref<WorkshopCard[]>([])
const equipment = ref<EquipmentOption[]>([])
const showCreate = ref(false)
const checklistText = ref('Nasmarować\nZatankować\nSprawdzić łyżki')
const newCard = ref<NewCardForm>({ equipment_id: null, title: '' })

const canDelete = computed(() => auth.user?.role === 'biuro' || auth.user?.role === 'manager')
const deleteDialog = ref(false)
const deleteTarget = ref<WorkshopCard | null>(null)
const deleting = ref(false)

const workerDraft = reactive<Record<number, string>>({})

const columns: { key: WorkshopColumn; label: string }[] = [
  { key: 'na_serwis', label: 'Na serwis' },
  { key: 'w_trakcie', label: 'W trakcie' },
  { key: 'gotowe', label: 'Gotowe' },
  { key: 'wydana', label: 'Wydana' },
]

function byColumn(key: WorkshopColumn): WorkshopCard[] {
  return cards.value.filter((c) => c.column === key)
}

function doneRatio(card: WorkshopCard): number {
  if (!card.checklist.length) return 0
  return card.checklist.filter((i) => i.done).length / card.checklist.length
}

function setWorkerDraft(cardId: number, value: string | number | null): void {
  workerDraft[cardId] = String(value ?? '')
}

const { connected } = useKanbanSocket(() => reload())

onMounted(async () => {
  await reload()
  const { data } = await api.get<EquipmentOption[]>('/equipment')
  equipment.value = data
  if (data[0]) newCard.value.equipment_id = data[0].id
})

async function reload() {
  const { data } = await api.get<WorkshopCard[]>('/kanban')
  cards.value = data
}

async function toggle(card: WorkshopCard, item: ChecklistItem, v: boolean) {
  const { data } = await api.post<WorkshopCard>(
    `/kanban/${card.id}/checklist/${item.id}/toggle`,
    null,
    { params: { done: v } }
  )
  const idx = cards.value.findIndex(c => c.id === card.id)
  if (idx !== -1) cards.value[idx] = data
}

async function saveWorker(card: WorkshopCard) {
  const raw = workerDraft[card.id]
  if (raw === undefined) return
  const val = raw.trim() || null
  if (val === (card.assigned_worker || null)) { delete workerDraft[card.id]; return }
  const { data } = await api.patch<WorkshopCard>(`/kanban/${card.id}`, { assigned_worker: val })
  const idx = cards.value.findIndex(c => c.id === card.id)
  if (idx !== -1) cards.value[idx] = data
  delete workerDraft[card.id]
}

async function moveToWydana(card: WorkshopCard) {
  const { data } = await api.patch<WorkshopCard>(`/kanban/${card.id}`, { column: 'wydana' })
  const idx = cards.value.findIndex(c => c.id === card.id)
  if (idx !== -1) cards.value[idx] = data
}

function openCreate() { showCreate.value = true }
function confirmDelete(card: WorkshopCard) { deleteTarget.value = card; deleteDialog.value = true }

async function doDelete() {
  if (!deleteTarget.value) return
  const targetId = deleteTarget.value.id
  deleting.value = true
  try {
    await api.delete(`/kanban/${targetId}`)
    cards.value = cards.value.filter(c => c.id !== targetId)
    deleteDialog.value = false
    $q.notify({ type: 'positive', message: 'Karta usunięta' })
  } catch (e: unknown) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  } finally {
    deleting.value = false
  }
}

async function create() {
  const checklist = checklistText.value.split('\n').map(s => s.trim()).filter(Boolean)
    .map((label, i) => ({ label, sort_order: i }))
  try {
    await api.post('/kanban', { ...newCard.value, checklist })
    showCreate.value = false
    checklistText.value = 'Nasmarować\nZatankować\nSprawdzić łyżki'
    newCard.value = { equipment_id: equipment.value[0]?.id, title: '' }
  } catch (e: unknown) {
    $q.notify({ type: 'negative', message: errMsg(e) })
  }
}
</script>

<style scoped>
.kanban-col {
  background: rgba(0,0,0,0.02);
  border-radius: 12px;
  padding: 12px;
  min-height: 200px;
}
.kanban-col-header {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 2px;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 2px solid currentColor;
}
.kanban-col-count {
  font-weight: 400;
  opacity: 0.45;
}
.kanban-col-na_serwis  { color: #dc2626; }
.kanban-col-na_serwis .kanban-col-header  { border-color: #dc2626; }
.kanban-col-w_trakcie  { color: #d97706; }
.kanban-col-w_trakcie .kanban-col-header  { border-color: #d97706; }
.kanban-col-gotowe     { color: #16a34a; }
.kanban-col-gotowe .kanban-col-header     { border-color: #16a34a; }
.kanban-col-wydana     { color: #6366f1; }
.kanban-col-wydana .kanban-col-header     { border-color: #6366f1; }
.kanban-card { border: 1px solid rgba(0,0,0,0.07); border-radius: 10px !important; }
.text-strike { text-decoration: line-through; }
</style>
