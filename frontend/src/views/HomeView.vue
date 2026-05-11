<template>
  <q-page padding style="max-width:900px; margin:0 auto">
    <!-- Greeting -->
    <div class="q-mb-xl q-pt-sm">
      <div style="font-size:11px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase; color:#999; margin-bottom:6px">
        {{ greeting }}
      </div>
      <div style="font-size:2rem; font-weight:700; letter-spacing:-0.5px; line-height:1.1; color:#111">
        {{ auth.user?.name }}
      </div>
      <div style="font-size:13px; color:#aaa; margin-top:4px; font-weight:500">
        {{ roleDesc }}
      </div>
    </div>

    <!-- Dashboard KPIs (biuro + manager) -->
    <div v-if="role !== 'mechanik' && kpi" class="q-mb-xl">
      <q-banner v-if="kpi.ending_today.length > 0" dense rounded
        class="text-white q-mb-md"
        style="background:#dc2626; font-size:13px; font-weight:600">
        <template #avatar><q-icon name="warning" color="white" /></template>
        Dziś kończy się {{ kpi.ending_today.length }} {{ kpi.ending_today.length === 1 ? 'umowa' : 'umów' }}:
        {{ kpi.ending_today.map((r: any) => r.client_name).join(', ') }}
      </q-banner>

      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-6 col-sm-3">
          <div class="q-card q-pa-md text-center" style="border-radius:12px">
            <div style="font-size:2rem; font-weight:800; color:#0369a1; line-height:1">{{ kpi.active_rentals }}</div>
            <div style="font-size:11px; color:#888; font-weight:600; margin-top:4px; text-transform:uppercase; letter-spacing:1px">Aktywnych umów</div>
          </div>
        </div>
        <div class="col-6 col-sm-3">
          <div class="q-card q-pa-md text-center" style="border-radius:12px">
            <div style="font-size:2rem; font-weight:800; color:#16a34a; line-height:1">{{ kpi.equipment_out }}</div>
            <div style="font-size:11px; color:#888; font-weight:600; margin-top:4px; text-transform:uppercase; letter-spacing:1px">Maszyn w terenie</div>
          </div>
        </div>
        <div class="col-6 col-sm-3">
          <div class="q-card q-pa-md text-center" style="border-radius:12px">
            <div style="font-size:2rem; font-weight:800; color:#d97706; line-height:1">{{ kpi.ending_week }}</div>
            <div style="font-size:11px; color:#888; font-weight:600; margin-top:4px; text-transform:uppercase; letter-spacing:1px">Kończy w 7 dni</div>
          </div>
        </div>
        <div class="col-6 col-sm-3">
          <div class="q-card q-pa-md text-center" style="border-radius:12px">
            <div style="font-size:1.4rem; font-weight:800; color:#111; line-height:1">{{ revenueFormatted }}</div>
            <div style="font-size:11px; color:#888; font-weight:600; margin-top:4px; text-transform:uppercase; letter-spacing:1px">Przychód (mies.)</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tiles -->
    <div class="row q-col-gutter-md">
      <div v-for="tile in tiles" :key="tile.to" :class="tile.wide ? 'col-12 col-sm-8' : 'col-6 col-sm-4 col-md-3'">
        <div class="card-action q-card" style="height:100%" @click="router.push(tile.to)">
          <div class="q-pa-lg column" style="height:100%; min-height:110px; gap:12px">
            <div :style="`background:${tile.bg}; border-radius:10px; width:40px; height:40px; display:flex; align-items:center; justify-content:center`">
              <q-icon :name="tile.icon" size="20px" :style="`color:${tile.iconColor}`" />
            </div>
            <div>
              <div style="font-weight:700; font-size:14px; color:#111; line-height:1.2">{{ tile.label }}</div>
              <div style="font-size:12px; color:#aaa; margin-top:3px; font-weight:500">{{ tile.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/lib/api'

const router = useRouter()
const auth = useAuthStore()
const role = computed(() => auth.user?.role)

const kpi = ref<any>(null)
onMounted(async () => {
  if (role.value !== 'mechanik') {
    try { kpi.value = (await api.get('/utils/dashboard')).data } catch { /* ignore */ }
  }
})

const revenueFormatted = computed(() => {
  if (!kpi.value) return '—'
  return new Intl.NumberFormat('pl-PL', { style: 'currency', currency: 'PLN', maximumFractionDigits: 0 })
    .format(kpi.value.month_revenue)
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Dzień dobry'
  if (h < 18) return 'Cześć'
  return 'Dobry wieczór'
})

const roleDesc = computed(() => ({
  biuro:    'Zarządzanie umowami i protokołami',
  mechanik: 'Nadzór serwisu · Hala',
  manager:  'Pełny dostęp · Dyrektor',
}[role.value ?? 'biuro']))

interface Tile {
  to: string; label: string; desc: string; icon: string
  bg: string; iconColor: string; wide?: boolean
}

const tiles = computed<Tile[]>(() => {
  if (role.value === 'mechanik') {
    return [
      { to: '/kanban',    label: 'Tablica',     desc: 'Zwroty · serwis · gotowość', icon: 'view_kanban',  bg: 'rgba(217,119,6,0.1)', iconColor: '#d97706', wide: true },
      { to: '/equipment', label: 'Park maszyn', desc: 'Status sprzętu',                   icon: 'construction', bg: 'rgba(22,163,74,0.1)', iconColor: '#16a34a' },
    ]
  }
  if (role.value === 'manager') {
    return [
      { to: '/rentals/new',     label: 'Nowa umowa',       desc: 'Kalkulator + PDF',  icon: 'add_circle',    bg: 'rgba(17,17,17,0.08)',  iconColor: '#111' },
      { to: '/rentals',         label: 'Umowy',            desc: 'Wszystkie umowy',   icon: 'description',   bg: 'rgba(3,105,161,0.1)',  iconColor: '#0369a1' },
      { to: '/inspections/new', label: 'Nowa inspekcja',   desc: 'Wydanie / zwrot',   icon: 'photo_camera',  bg: 'rgba(217,119,6,0.1)',  iconColor: '#d97706' },
      { to: '/inspections',     label: 'Protokoły',        desc: 'Historia inspekcji', icon: 'assignment',   bg: 'rgba(99,102,241,0.1)', iconColor: '#6366f1' },
      { to: '/kanban',          label: 'Tablica',          desc: 'Operacje sprzętu',  icon: 'view_kanban',   bg: 'rgba(202,138,4,0.1)',  iconColor: '#ca8a04' },
      { to: '/equipment',       label: 'Park maszyn',      desc: 'Sprzęt i statusy',  icon: 'construction',  bg: 'rgba(22,163,74,0.1)',  iconColor: '#16a34a' },
    ]
  }
  // biuro
  return [
    { to: '/rentals/new',     label: 'Nowa umowa',       desc: 'Kalkulator + PDF',  icon: 'add_circle',    bg: 'rgba(17,17,17,0.08)',  iconColor: '#111', wide: true },
    { to: '/rentals',         label: 'Umowy',            desc: 'Wszystkie umowy',   icon: 'description',   bg: 'rgba(3,105,161,0.1)',  iconColor: '#0369a1' },
    { to: '/inspections/new', label: 'Nowa inspekcja',   desc: 'Wydanie / zwrot',   icon: 'photo_camera',  bg: 'rgba(217,119,6,0.1)',  iconColor: '#d97706' },
    { to: '/inspections',     label: 'Protokoły',        desc: 'Historia inspekcji', icon: 'assignment',   bg: 'rgba(99,102,241,0.1)', iconColor: '#6366f1' },
    { to: '/kanban',          label: 'Tablica',          desc: 'Operacje sprzętu',  icon: 'view_kanban',   bg: 'rgba(202,138,4,0.1)',  iconColor: '#ca8a04' },
    { to: '/equipment',       label: 'Park maszyn',      desc: 'Sprzęt i statusy',  icon: 'construction',  bg: 'rgba(22,163,74,0.1)',  iconColor: '#16a34a' },
  ]
})
</script>
