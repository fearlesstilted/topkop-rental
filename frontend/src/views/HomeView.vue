<template>
  <q-page class="home-page">
    <section class="home-hero">
      <div>
        <div class="eyebrow">{{ greeting }}</div>
        <h1>{{ auth.user?.name }}</h1>
        <p>{{ roleDesc }}</p>
      </div>
      <q-btn
        v-if="canOperate"
        color="amber-8"
        text-color="black"
        icon="add_circle"
        label="Nowa umowa"
        to="/rentals/new"
        unelevated
      />
    </section>

    <q-banner
      v-if="kpi?.ending_today.length"
      rounded
      class="alert-banner q-mb-lg"
    >
      <template #avatar><q-icon name="warning" /></template>
      Dziś kończy się {{ kpi.ending_today.length }} {{ kpi.ending_today.length === 1 ? 'umowa' : 'umów' }}:
      {{ kpi.ending_today.map((r) => r.client_name).join(', ') }}
    </q-banner>

    <section v-if="kpi" class="kpi-grid q-mb-lg">
      <article v-for="item in primaryKpis" :key="item.label" class="metric-card">
        <div class="metric-label">{{ item.label }}</div>
        <div class="metric-value">{{ item.value }}</div>
        <div class="metric-note">{{ item.note }}</div>
      </article>
    </section>

    <section class="content-grid">
      <article class="action-panel">
        <div class="section-heading">
          <span>{{ canOperate ? 'Co robimy teraz' : 'Najważniejsze widoki' }}</span>
          <small>{{ canOperate ? 'operacje' : 'read-only' }}</small>
        </div>
        <div class="tile-grid">
          <button v-for="tile in tiles" :key="tile.to" class="action-tile" type="button" @click="router.push(tile.to)">
            <span class="tile-icon"><q-icon :name="tile.icon" size="22px" /></span>
            <span>
              <strong>{{ tile.label }}</strong>
              <small>{{ tile.desc }}</small>
            </span>
          </button>
        </div>
      </article>

      <article v-if="isDirector && kpi" class="director-panel">
        <div class="section-heading">
          <span>Obraz miesiąca</span>
          <small>dyrektor</small>
        </div>
        <div class="director-list">
          <div class="director-row">
            <span>Średnia umowa</span>
            <strong>{{ money(kpi.average_rental_netto ?? 0) }}</strong>
          </div>
          <div class="director-row">
            <span>Transport</span>
            <strong>{{ money(kpi.transport_revenue_month ?? 0) }}</strong>
          </div>
          <div class="director-row">
            <span>Operatorzy</span>
            <strong>{{ number(kpi.operator_hours_month ?? 0) }} h</strong>
          </div>
          <div class="director-row">
            <span>Tryb godzinowy / dzienny</span>
            <strong>{{ kpi.hourly_rentals_month ?? 0 }} / {{ kpi.daily_rentals_month ?? 0 }}</strong>
          </div>
          <div class="director-row">
            <span>Serwis / uszkodzone</span>
            <strong>{{ kpi.service_equipment ?? 0 }} / {{ kpi.broken_equipment ?? 0 }}</strong>
          </div>
        </div>
      </article>

      <article v-if="isDirector && kpi?.top_clients?.length" class="director-panel">
        <div class="section-heading">
          <span>Top klienci</span>
          <small>ten miesiąc</small>
        </div>
        <div class="client-list">
          <div v-for="client in kpi.top_clients" :key="client.client_name" class="client-row">
            <div>
              <strong>{{ client.client_name }}</strong>
              <small>{{ client.rentals_count }} um.</small>
            </div>
            <span>{{ money(client.total_netto) }}</span>
          </div>
        </div>
      </article>

      <article v-if="isDirector && kpi?.upcoming_returns?.length" class="director-panel">
        <div class="section-heading">
          <span>Najbliższe zwroty</span>
          <small>7 dni</small>
        </div>
        <div class="client-list">
          <div v-for="item in kpi.upcoming_returns" :key="item.id" class="client-row">
            <div>
              <strong>#{{ item.id }} · {{ item.client_name }}</strong>
              <small>koniec umowy</small>
            </div>
            <span>{{ item.end_date }}</span>
          </div>
        </div>
      </article>
    </section>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/lib/api'

interface EndingRental {
  id: number
  client_name: string
  end_date: string
  equipment_id?: number
}

interface TopClient {
  client_name: string
  total_netto: number
  rentals_count: number
}

interface DashboardData {
  active_rentals: number
  equipment_out: number
  ending_today: EndingRental[]
  ending_week: number
  month_revenue: number
  total_equipment?: number
  available_equipment?: number
  service_equipment?: number
  broken_equipment?: number
  draft_rentals?: number
  returned_month?: number
  cancelled_month?: number
  hourly_rentals_month?: number
  daily_rentals_month?: number
  operator_hours_month?: number
  transport_revenue_month?: number
  average_rental_netto?: number
  upcoming_returns?: EndingRental[]
  top_clients?: TopClient[]
}

interface Tile {
  to: string
  label: string
  desc: string
  icon: string
}

const router = useRouter()
const auth = useAuthStore()
const role = computed(() => auth.user?.role)
const canOperate = computed(() => role.value === 'biuro')
const isDirector = computed(() => role.value === 'manager')
const kpi = ref<DashboardData | null>(null)

onMounted(async () => {
  kpi.value = (await api.get<DashboardData>('/utils/dashboard')).data
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Dzień dobry'
  if (h < 18) return 'Cześć'
  return 'Dobry wieczór'
})

const roleDesc = computed(() => (
  canOperate.value
    ? 'Pełne operacje: umowy, protokoły, sprzęt i tablica.'
    : 'Szeroki przegląd firmy: przychód, flota, zwroty i klienci.'
))

const primaryKpis = computed(() => {
  if (!kpi.value) return []

  const items = [
    { label: 'Aktywne umowy', value: String(kpi.value.active_rentals), note: 'teraz w pracy' },
    { label: 'Maszyny w terenie', value: String(kpi.value.equipment_out), note: 'status wynajęty' },
    { label: 'Kończy w 7 dni', value: String(kpi.value.ending_week), note: 'pilnować zwrotów' },
    { label: 'Przychód miesiąca', value: money(kpi.value.month_revenue), note: 'netto' },
  ]

  if (!isDirector.value) return items

  return [
    ...items,
    { label: 'Wolne maszyny', value: String(kpi.value.available_equipment ?? 0), note: `z ${kpi.value.total_equipment ?? 0} w parku` },
    { label: 'Szkice umów', value: String(kpi.value.draft_rentals ?? 0), note: 'do domknięcia' },
    { label: 'Zwrócone w mies.', value: String(kpi.value.returned_month ?? 0), note: 'zamknięte operacje' },
    { label: 'Anulowane w mies.', value: String(kpi.value.cancelled_month ?? 0), note: 'kontrola strat' },
  ]
})

const tiles = computed<Tile[]>(() => {
  if (canOperate.value) {
    return [
      { to: '/rentals/new', label: 'Nowa umowa', desc: 'wycena, PDF, transport', icon: 'add_circle' },
      { to: '/inspections/new', label: 'Nowy protokół', desc: 'wydanie albo zwrot', icon: 'photo_camera' },
      { to: '/kanban', label: 'Tablica', desc: 'co trzeba ogarnąć', icon: 'view_kanban' },
      { to: '/equipment', label: 'Park maszyn', desc: 'ceny i statusy', icon: 'construction' },
      { to: '/rentals', label: 'Umowy', desc: 'lista i PDF', icon: 'description' },
      { to: '/inspections', label: 'Protokoły', desc: 'historia kontroli', icon: 'assignment' },
    ]
  }

  return [
    { to: '/rentals', label: 'Umowy', desc: 'statusy i przychód', icon: 'description' },
    { to: '/equipment', label: 'Park maszyn', desc: 'dostępność floty', icon: 'construction' },
    { to: '/kanban', label: 'Tablica', desc: 'stan operacji', icon: 'view_kanban' },
    { to: '/inspections', label: 'Protokoły', desc: 'wydania i zwroty', icon: 'assignment' },
  ]
})

function money(value: number): string {
  return new Intl.NumberFormat('pl-PL', {
    currency: 'PLN',
    maximumFractionDigits: 0,
    style: 'currency',
  }).format(value || 0)
}

function number(value: number): string {
  return new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 1 }).format(value || 0)
}
</script>

<style scoped>
.home-page {
  background:
    radial-gradient(circle at 20% 0%, rgba(245, 158, 11, 0.18), transparent 32%),
    radial-gradient(circle at 100% 18%, rgba(15, 118, 110, 0.12), transparent 26%),
    linear-gradient(180deg, #f8fafc 0%, #ffffff 52%);
  min-height: 100dvh;
  padding: 28px;
}

.home-hero {
  align-items: center;
  background: #111827;
  border-radius: 28px;
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.18);
  color: white;
  display: flex;
  justify-content: space-between;
  margin: 0 auto 24px;
  max-width: 1180px;
  padding: 28px;
}

.home-hero h1 {
  font-size: clamp(2rem, 5vw, 4.4rem);
  font-weight: 900;
  letter-spacing: -0.06em;
  line-height: 0.95;
  margin: 0;
}

.home-hero p {
  color: rgba(255, 255, 255, 0.66);
  font-size: 15px;
  margin: 10px 0 0;
}

.eyebrow,
.section-heading small,
.metric-label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.eyebrow {
  color: #f59e0b;
  margin-bottom: 8px;
}

.alert-banner,
.kpi-grid,
.content-grid {
  margin-inline: auto;
  max-width: 1180px;
}

.alert-banner {
  background: #fee2e2;
  color: #991b1b;
  font-weight: 700;
}

.kpi-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metric-card,
.action-panel,
.director-panel {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 22px;
  box-shadow: 0 16px 38px rgba(15, 23, 42, 0.07);
}

.metric-card {
  padding: 18px;
}

.metric-label,
.metric-note {
  color: #64748b;
}

.metric-value {
  color: #0f172a;
  font-size: clamp(1.7rem, 3vw, 2.7rem);
  font-weight: 900;
  letter-spacing: -0.05em;
  line-height: 1;
  margin: 10px 0 6px;
}

.metric-note {
  font-size: 12px;
  font-weight: 650;
}

.content-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.8fr);
}

.action-panel,
.director-panel {
  padding: 20px;
}

.section-heading {
  align-items: center;
  color: #0f172a;
  display: flex;
  font-size: 18px;
  font-weight: 850;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-heading small {
  color: #94a3b8;
}

.tile-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.action-tile {
  align-items: center;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  color: #0f172a;
  cursor: pointer;
  display: flex;
  gap: 12px;
  min-height: 86px;
  padding: 14px;
  text-align: left;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}

.action-tile:hover {
  border-color: rgba(245, 158, 11, 0.7);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.10);
  transform: translateY(-2px);
}

.tile-icon {
  align-items: center;
  background: #111827;
  border-radius: 16px;
  color: #f59e0b;
  display: inline-flex;
  height: 46px;
  justify-content: center;
  min-width: 46px;
}

.action-tile strong,
.action-tile small {
  display: block;
}

.action-tile strong {
  font-size: 15px;
  font-weight: 850;
}

.action-tile small {
  color: #64748b;
  font-size: 12px;
  font-weight: 650;
  margin-top: 3px;
}

.director-list,
.client-list {
  display: grid;
  gap: 10px;
}

.director-row,
.client-row {
  align-items: center;
  border-bottom: 1px solid rgba(15, 23, 42, 0.07);
  display: flex;
  justify-content: space-between;
  padding-bottom: 10px;
}

.director-row span,
.client-row small {
  color: #64748b;
  font-size: 12px;
  font-weight: 650;
}

.director-row strong,
.client-row span {
  color: #0f172a;
  font-size: 14px;
  font-weight: 850;
}

.client-row strong,
.client-row small {
  display: block;
}

@media (max-width: 980px) {
  .kpi-grid,
  .content-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .home-page {
    padding: 16px;
  }

  .home-hero {
    align-items: flex-start;
    flex-direction: column;
    border-radius: 22px;
  }

  .kpi-grid,
  .content-grid,
  .tile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
