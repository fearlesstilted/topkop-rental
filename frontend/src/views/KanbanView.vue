<template>
  <q-page padding class="board-page">
    <div class="board-hero q-mb-md">
      <div>
        <div class="text-overline text-grey-7">TopKop operations</div>
        <div class="text-h5 text-weight-bold">Tablica operacyjna</div>
        <div class="text-body2 text-grey-7">
          Jedna kolejka dla wypożyczeń, zwrotów i przygotowania sprzętu.
        </div>
      </div>
      <div class="row items-center q-gutter-sm">
        <q-badge :color="connected ? 'positive' : 'grey'" class="status-badge">
          {{ connected ? 'online' : 'offline' }}
        </q-badge>
        <q-btn color="primary" icon="add" label="Nowa karta" @click="openCreate" />
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col-12 col-md-5">
        <q-input v-model="search" dense outlined clearable debounce="150" placeholder="Szukaj: sprzęt, klient, opis">
          <template #prepend><q-icon name="search" /></template>
        </q-input>
      </div>
      <div class="col-6 col-md-3">
        <q-select v-model="priorityFilter" dense outlined emit-value map-options
          :options="priorityFilterOptions" label="Priorytet" />
      </div>
      <div class="col-6 col-md-2">
        <q-toggle v-model="onlyOverdue" dense label="Po terminie" />
      </div>
      <div class="col-12 col-md-2 text-right">
        <q-btn flat icon="refresh" label="Odśwież" @click="reload" />
      </div>
    </div>

    <div class="row q-col-gutter-md">
      <div v-for="col in columns" :key="col.key" class="col-12 col-sm-6 col-lg-3">
        <div :class="`board-col board-col-${col.key}`">
          <div class="board-col-header">
            <div>
              <div class="board-col-title">{{ col.label }}</div>
              <div class="board-col-hint">{{ col.hint }}</div>
            </div>
            <span class="board-col-count">{{ byColumn(col.key).length }}</span>
          </div>

          <div class="q-mt-sm">
            <q-card v-for="card in byColumn(col.key)" :key="card.id" flat class="board-card q-mb-sm">
              <q-card-section class="q-pa-md">
                <div class="row items-start no-wrap q-mb-sm">
                  <div class="col">
                    <div class="row items-center q-gutter-xs q-mb-xs">
                      <q-badge :color="priorityColor(card.priority)" class="priority-badge">
                        {{ priorityLabel(card.priority) }}
                      </q-badge>
                      <q-badge v-if="card.source !== 'manual'" color="blue-grey" outline>
                        {{ sourceLabel(card.source) }}
                      </q-badge>
                      <q-badge v-if="isOverdue(card)" color="negative">po terminie</q-badge>
                    </div>
                    <div class="text-body1 text-weight-bold card-title">{{ card.title }}</div>
                  </div>
                  <q-btn v-if="canDelete" flat dense round icon="close" color="negative" size="sm"
                    @click.stop="confirmDelete(card)" />
                </div>

                <div class="context-box q-mb-sm">
                  <div class="row items-center no-wrap">
                    <q-icon name="construction" size="16px" class="q-mr-xs" />
                    <span class="text-weight-medium">{{ card.equipment_code || `#${card.equipment_id}` }}</span>
                    <span class="text-grey-7 q-ml-xs">{{ card.equipment_name }}</span>
                  </div>
                  <div v-if="card.rental_id" class="row items-center no-wrap q-mt-xs">
                    <q-icon name="description" size="16px" class="q-mr-xs" />
                    <span>#{{ card.rental_id }}</span>
                    <span v-if="card.rental_client_name" class="q-ml-xs">{{ card.rental_client_name }}</span>
                  </div>
                  <div v-if="card.due_date" class="row items-center no-wrap q-mt-xs">
                    <q-icon name="event" size="16px" class="q-mr-xs" />
                    <span :class="isOverdue(card) ? 'text-negative text-weight-bold' : ''">
                      {{ card.due_date }}
                    </span>
                  </div>
                </div>

                <div v-if="card.notes" class="notes q-mb-sm">{{ card.notes }}</div>

                <div v-if="card.checklist.length" class="q-mb-sm">
                  <div v-for="it in card.checklist" :key="it.id" class="row items-center no-wrap">
                    <q-checkbox
                      :model-value="it.done"
                      dense
                      size="sm"
                      @update:model-value="(v) => toggle(card, it, Boolean(v))"
                    />
                    <span class="q-ml-xs" :class="it.done ? 'text-strike text-grey-5' : 'text-body2'">
                      {{ it.label }}
                    </span>
                  </div>
                  <q-linear-progress
                    :value="doneRatio(card)"
                    :color="doneRatio(card) === 1 ? 'positive' : 'primary'"
                    rounded
                    size="5px"
                    class="q-mt-sm"
                  />
                </div>

                <q-input
                  dense
                  outlined
                  :model-value="ownerDraft[card.id] ?? card.assigned_worker ?? ''"
                  label="Kto ogarnia"
                  placeholder="— wolne —"
                  @update:model-value="(v) => setOwnerDraft(card.id, v)"
                  @blur="saveOwner(card)"
                  @keyup.enter="saveOwner(card)"
                />

                <div class="row q-gutter-xs q-mt-sm">
                  <q-btn v-if="previousColumn(card.column)" dense flat icon="chevron_left"
                    :label="columnLabel(previousColumn(card.column))" @click="move(card, previousColumn(card.column))" />
                  <q-space />
                  <q-btn v-if="nextColumn(card.column)" dense unelevated color="primary" icon-right="chevron_right"
                    :label="columnLabel(nextColumn(card.column))" @click="move(card, nextColumn(card.column))" />
                </div>
              </q-card-section>
            </q-card>

            <div v-if="!byColumn(col.key).length" class="empty-col">
              Brak kart
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
      <q-card style="min-width:360px; max-width:520px">
        <q-card-section>
          <div class="text-h6">Nowa karta operacyjna</div>
          <div class="text-body2 text-grey-7">Dla zwrotu, przygotowania sprzętu albo ręcznej sprawy.</div>
        </q-card-section>
        <q-card-section class="q-pt-none q-gutter-sm">
          <q-select v-model="newCard.equipment_id" :options="equipment" option-value="id" option-label="label"
            emit-value map-options label="Sprzęt" />
          <q-input v-model="newCard.title" label="Tytuł / opis problemu" />
          <div class="row q-col-gutter-sm">
            <div class="col-6">
              <q-select v-model="newCard.priority" :options="priorityOptions" emit-value map-options label="Priorytet" />
            </div>
            <div class="col-6">
              <q-input v-model="newCard.due_date" type="date" label="Termin" />
            </div>
          </div>
          <q-input v-model="newCard.assigned_worker" label="Kto ogarnia" />
          <q-input v-model="newCard.notes" type="textarea" rows="2" label="Notatki" />
          <q-input v-model="checklistText" type="textarea" rows="4" label="Lista zadań (po linii)" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Anuluj" v-close-popup />
          <q-btn color="primary" label="Dodaj" :loading="creating" @click="create" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useQuasar } from 'quasar'
import { api, errMsg } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { useKanbanSocket } from '@/composables/useKanbanSocket'

const $q = useQuasar()
const auth = useAuthStore()

type WorkshopColumn = 'na_serwis' | 'w_trakcie' | 'gotowe' | 'wydana'
type Priority = 'low' | 'normal' | 'high' | 'urgent'
type PriorityFilter = Priority | 'all'

type ChecklistItem = {
  id: number
  label: string
  done: boolean
}

type WorkshopCard = {
  id: number
  equipment_id: number
  rental_id: number | null
  title: string
  column: WorkshopColumn
  assigned_worker: string | null
  priority: Priority
  due_date: string | null
  source: string
  notes: string | null
  equipment_code: string | null
  equipment_name: string | null
  rental_client_name: string | null
  rental_status: string | null
  checklist: ChecklistItem[]
}

type EquipmentOption = {
  id: number
  code: string
  name: string
  label: string
}

type NewCardForm = {
  equipment_id: number | null
  title: string
  priority: Priority
  due_date: string | null
  assigned_worker: string
  notes: string
}

const cards = ref<WorkshopCard[]>([])
const equipment = ref<EquipmentOption[]>([])
const showCreate = ref(false)
const creating = ref(false)
const checklistText = ref('Sprawdzić stan techniczny\nNasmarować\nUzupełnić płyny')
const newCard = ref<NewCardForm>({
  equipment_id: null,
  title: '',
  priority: 'normal',
  due_date: null,
  assigned_worker: '',
  notes: '',
})

const search = ref('')
const priorityFilter = ref<PriorityFilter>('all')
const onlyOverdue = ref(false)

const canDelete = computed(() => auth.user?.role === 'biuro' || auth.user?.role === 'manager')
const deleteDialog = ref(false)
const deleteTarget = ref<WorkshopCard | null>(null)
const deleting = ref(false)

const ownerDraft = reactive<Record<number, string>>({})

const columns: { key: WorkshopColumn; label: string; hint: string }[] = [
  { key: 'na_serwis', label: 'Do ogarnięcia', hint: 'Nowe zwroty i ręczne sprawy' },
  { key: 'w_trakcie', label: 'W robocie', hint: 'Ktoś już nad tym pracuje' },
  { key: 'gotowe', label: 'Gotowe', hint: 'Można wypożyczać / zamykać' },
  { key: 'wydana', label: 'Zamknięte', hint: 'Oddane klientowi albo zakończone' },
]

const priorityOptions: { label: string; value: Priority }[] = [
  { label: 'Niski', value: 'low' },
  { label: 'Normalny', value: 'normal' },
  { label: 'Wysoki', value: 'high' },
  { label: 'Pilny', value: 'urgent' },
]

const priorityFilterOptions: { label: string; value: PriorityFilter }[] = [
  { label: 'Wszystkie', value: 'all' },
  ...priorityOptions,
]

const filteredCards = computed(() => {
  const query = search.value.trim().toLowerCase()
  return cards.value.filter((card) => {
    if (priorityFilter.value !== 'all' && card.priority !== priorityFilter.value) return false
    if (onlyOverdue.value && !isOverdue(card)) return false
    if (!query) return true

    const haystack = [
      card.title,
      card.notes,
      card.assigned_worker,
      card.equipment_code,
      card.equipment_name,
      card.rental_client_name,
    ].filter(Boolean).join(' ').toLowerCase()
    return haystack.includes(query)
  })
})

const { connected } = useKanbanSocket(() => reload())

onMounted(async () => {
  await Promise.all([reload(), loadEquipment()])
})

function byColumn(key: WorkshopColumn): WorkshopCard[] {
  return filteredCards.value.filter((card) => card.column === key)
}

function doneRatio(card: WorkshopCard): number {
  if (!card.checklist.length) return 0
  return card.checklist.filter((item) => item.done).length / card.checklist.length
}

function setOwnerDraft(cardId: number, value: string | number | null): void {
  ownerDraft[cardId] = String(value ?? '')
}

function isOverdue(card: WorkshopCard): boolean {
  if (!card.due_date || card.column === 'wydana') return false
  return card.due_date < new Date().toISOString().slice(0, 10)
}

function priorityColor(priority: string): string {
  return { low: 'grey', normal: 'primary', high: 'orange', urgent: 'negative' }[priority] ?? 'grey'
}

function priorityLabel(priority: string): string {
  return { low: 'niski', normal: 'normalny', high: 'wysoki', urgent: 'pilny' }[priority] ?? priority
}

function sourceLabel(source: string): string {
  return { rental_return: 'zwrot', manual: 'ręcznie' }[source] ?? source
}

function columnLabel(column?: WorkshopColumn | null): string {
  return columns.find((item) => item.key === column)?.label ?? ''
}

function previousColumn(column: WorkshopColumn): WorkshopColumn | null {
  const index = columns.findIndex((item) => item.key === column)
  return index > 0 ? columns[index - 1].key : null
}

function nextColumn(column: WorkshopColumn): WorkshopColumn | null {
  const index = columns.findIndex((item) => item.key === column)
  return index >= 0 && index < columns.length - 1 ? columns[index + 1].key : null
}

async function loadEquipment(): Promise<void> {
  const { data } = await api.get<Array<{ id: number; code: string; name: string }>>('/equipment')
  equipment.value = data.map((item) => ({
    ...item,
    label: `${item.code} · ${item.name}`,
  }))
  if (data[0]) newCard.value.equipment_id = data[0].id
}

async function reload(): Promise<void> {
  const { data } = await api.get<WorkshopCard[]>('/kanban')
  cards.value = data
}

async function toggle(card: WorkshopCard, item: ChecklistItem, value: boolean): Promise<void> {
  const { data } = await api.post<WorkshopCard>(
    `/kanban/${card.id}/checklist/${item.id}/toggle`,
    null,
    { params: { done: value } }
  )
  replaceCard(data)
}

async function saveOwner(card: WorkshopCard): Promise<void> {
  const raw = ownerDraft[card.id]
  if (raw === undefined) return

  const value = raw.trim() || null
  if (value === (card.assigned_worker || null)) {
    delete ownerDraft[card.id]
    return
  }

  const { data } = await api.patch<WorkshopCard>(`/kanban/${card.id}`, { assigned_worker: value })
  replaceCard(data)
  delete ownerDraft[card.id]
}

async function move(card: WorkshopCard, column: WorkshopColumn | null): Promise<void> {
  if (!column) return
  const { data } = await api.patch<WorkshopCard>(`/kanban/${card.id}`, { column })
  replaceCard(data)
}

function replaceCard(card: WorkshopCard): void {
  const index = cards.value.findIndex((item) => item.id === card.id)
  if (index !== -1) cards.value[index] = card
}

function openCreate(): void {
  showCreate.value = true
}

function confirmDelete(card: WorkshopCard): void {
  deleteTarget.value = card
  deleteDialog.value = true
}

async function doDelete(): Promise<void> {
  if (!deleteTarget.value) return
  const targetId = deleteTarget.value.id
  deleting.value = true
  try {
    await api.delete(`/kanban/${targetId}`)
    cards.value = cards.value.filter((card) => card.id !== targetId)
    deleteDialog.value = false
    $q.notify({ type: 'positive', message: 'Karta usunięta' })
  } catch (error: unknown) {
    $q.notify({ type: 'negative', message: errMsg(error) })
  } finally {
    deleting.value = false
  }
}

async function create(): Promise<void> {
  if (!newCard.value.equipment_id || !newCard.value.title.trim()) {
    $q.notify({ type: 'warning', message: 'Wybierz sprzęt i wpisz tytuł' })
    return
  }

  const checklist = checklistText.value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((label, index) => ({ label, sort_order: index }))

  creating.value = true
  try {
    const { data } = await api.post<WorkshopCard>('/kanban', {
      equipment_id: newCard.value.equipment_id,
      title: newCard.value.title.trim(),
      priority: newCard.value.priority,
      due_date: newCard.value.due_date || null,
      assigned_worker: newCard.value.assigned_worker.trim() || null,
      notes: newCard.value.notes.trim() || null,
      checklist,
    })
    cards.value.push(data)
    showCreate.value = false
    checklistText.value = 'Sprawdzić stan techniczny\nNasmarować\nUzupełnić płyny'
    newCard.value = {
      equipment_id: equipment.value[0]?.id ?? null,
      title: '',
      priority: 'normal',
      due_date: null,
      assigned_worker: '',
      notes: '',
    }
  } catch (error: unknown) {
    $q.notify({ type: 'negative', message: errMsg(error) })
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.board-page {
  background:
    radial-gradient(circle at top left, rgba(217, 119, 6, 0.10), transparent 30%),
    linear-gradient(180deg, #f8fafc 0%, #fff 45%);
}

.board-hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.07);
}

.status-badge,
.priority-badge {
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.board-col {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 12px;
  min-height: 280px;
}

.board-col-header {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;
  padding-bottom: 10px;
  border-bottom: 2px solid currentColor;
}

.board-col-title {
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 1.4px;
  text-transform: uppercase;
}

.board-col-hint {
  color: #64748b;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
}

.board-col-count {
  background: rgba(15, 23, 42, 0.08);
  border-radius: 999px;
  color: #0f172a;
  font-size: 12px;
  font-weight: 800;
  min-width: 28px;
  padding: 2px 8px;
  text-align: center;
}

.board-col-na_serwis { color: #dc2626; }
.board-col-w_trakcie { color: #d97706; }
.board-col-gotowe { color: #16a34a; }
.board-col-wydana { color: #475569; }

.board-card {
  border: 1px solid rgba(15, 23, 42, 0.09);
  border-radius: 14px !important;
  color: #0f172a;
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.board-card:hover {
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.10);
  transform: translateY(-1px);
}

.card-title {
  line-height: 1.25;
}

.context-box {
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 10px;
  color: #334155;
  font-size: 12px;
  padding: 8px;
}

.notes {
  border-left: 3px solid #cbd5e1;
  color: #475569;
  font-size: 12px;
  padding-left: 8px;
  white-space: pre-wrap;
}

.empty-col {
  border: 1px dashed rgba(100, 116, 139, 0.35);
  border-radius: 12px;
  color: #94a3b8;
  font-size: 12px;
  padding: 18px;
  text-align: center;
}

.text-strike {
  text-decoration: line-through;
}

@media (max-width: 700px) {
  .board-hero {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
