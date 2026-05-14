<template>
  <q-layout view="hHh lpR fFf">
    <q-header v-if="auth.isAuthed" style="background:#0f0f0f; border-bottom:1px solid rgba(255,255,255,0.07)">
      <q-toolbar style="min-height:52px">
        <q-btn flat dense round icon="menu" color="white" @click="drawer = !drawer" />
        <q-toolbar-title style="font-size:15px; font-weight:700; letter-spacing:-0.3px; color:#fff">
          TOP KOP <span style="color:#f59e0b">Rental</span>
        </q-toolbar-title>
        <q-chip
          dense
          :color="roleChip.color"
          text-color="white"
          style="font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; border-radius:6px"
        >
          {{ auth.user?.name }}
        </q-chip>
        <q-btn flat dense round icon="logout" color="grey-4" class="q-ml-sm" @click="logout" title="Wyloguj" />
      </q-toolbar>
    </q-header>

    <q-drawer
      v-if="auth.isAuthed"
      v-model="drawer"
      show-if-above
      :width="220"
      style="background:#0a0a0a"
    >
      <div class="column" style="height:100%">
        <!-- Brand -->
        <div class="nav-brand">
          <img src="/topkop_logo.webp" alt="TOP KOP" />
          <div class="nav-brand-sub">{{ isDirector ? 'Panel dyrektora' : 'Operacje biura' }}</div>
        </div>

        <!-- Nav -->
        <q-list style="flex:1; padding:0">
          <q-item exact clickable v-ripple to="/" class="nav-item" style="color:#ccc">
            <q-item-section avatar><q-icon name="home" size="18px" /></q-item-section>
            <q-item-section>Start</q-item-section>
          </q-item>

          <template v-if="canOperate">
            <div style="padding:12px 16px 4px; font-size:10px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:rgba(255,255,255,0.2)">
              Szybkie działania
            </div>
            <q-item clickable v-ripple to="/rentals/new" class="nav-item" style="color:#ccc">
              <q-item-section avatar><q-icon name="add_circle" size="18px" /></q-item-section>
              <q-item-section>Nowa umowa</q-item-section>
            </q-item>
            <q-item clickable v-ripple to="/rentals" class="nav-item" style="color:#ccc">
              <q-item-section avatar><q-icon name="description" size="18px" /></q-item-section>
              <q-item-section>Umowy</q-item-section>
            </q-item>
          </template>

          <div style="padding:12px 16px 4px; font-size:10px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:rgba(255,255,255,0.2)">
            {{ isDirector ? 'Przegląd' : 'Teren' }}
          </div>
          <q-item v-if="canOperate" clickable v-ripple to="/inspections/new" class="nav-item" style="color:#ccc">
            <q-item-section avatar><q-icon name="photo_camera" size="18px" /></q-item-section>
            <q-item-section>Nowy protokół</q-item-section>
          </q-item>
          <q-item clickable v-ripple to="/inspections" class="nav-item" style="color:#ccc">
            <q-item-section avatar><q-icon name="assignment" size="18px" /></q-item-section>
            <q-item-section>Protokoły</q-item-section>
          </q-item>
          <q-item clickable v-ripple to="/kanban" class="nav-item" style="color:#ccc">
            <q-item-section avatar><q-icon name="view_kanban" size="18px" /></q-item-section>
            <q-item-section>Tablica</q-item-section>
          </q-item>
          <q-item v-if="isDirector" clickable v-ripple to="/rentals" class="nav-item" style="color:#ccc">
            <q-item-section avatar><q-icon name="description" size="18px" /></q-item-section>
            <q-item-section>Umowy</q-item-section>
          </q-item>

          <template v-if="canOperate || isDirector">
            <div style="padding:12px 16px 4px; font-size:10px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:rgba(255,255,255,0.2)">
              Sprzęt
            </div>
            <q-item clickable v-ripple to="/equipment" class="nav-item" style="color:#ccc">
              <q-item-section avatar><q-icon name="construction" size="18px" /></q-item-section>
              <q-item-section>Park maszyn</q-item-section>
            </q-item>
            <q-item v-if="canOperate" clickable v-ripple to="/categories" class="nav-item" style="color:#ccc">
              <q-item-section avatar><q-icon name="category" size="18px" /></q-item-section>
              <q-item-section>Kategorie</q-item-section>
            </q-item>
          </template>
        </q-list>

        <!-- Footer -->
        <div class="nav-role-footer">
          <div class="nav-role-badge">
            <q-icon :name="roleChip.icon" size="12px" />
            {{ roleLabel }}
          </div>
        </div>
      </div>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const drawer = ref(false)
const auth = useAuthStore()
const router = useRouter()

const role = computed(() => auth.user?.role)
const isDirector = computed(() => role.value === 'manager')
const canOperate = computed(() => role.value === 'biuro')

const roleLabel = computed(() => ({
  biuro: 'Biuro', manager: 'Dyrektor'
}[role.value ?? 'biuro'] ?? role.value))

const roleChip = computed(() => ({
  biuro:    { color: 'indigo-8', icon: 'badge' },
  manager:  { color: 'teal-8',   icon: 'supervisor_account' },
}[role.value ?? 'biuro'] ?? { color: 'grey-7', icon: 'person' }))

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
