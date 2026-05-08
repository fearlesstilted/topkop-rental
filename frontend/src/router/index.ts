import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// roles: которым РАЗРЕШЁН доступ; undefined = все авторизованные
const routes: RouteRecordRaw[] = [
  { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  { path: '/', component: () => import('@/views/HomeView.vue') },
  { path: '/equipment',     component: () => import('@/views/EquipmentListView.vue'), meta: { roles: ['biuro', 'manager', 'mechanik'] } },
  { path: '/equipment/new', component: () => import('@/views/EquipmentFormView.vue'), meta: { roles: ['biuro', 'manager'] } },
  { path: '/equipment/:id', component: () => import('@/views/EquipmentFormView.vue'), meta: { roles: ['biuro', 'manager'] } },
  { path: '/categories',    component: () => import('@/views/CategoriesView.vue'),    meta: { roles: ['biuro', 'manager'] } },
  { path: '/rentals',       component: () => import('@/views/RentalListView.vue'),    meta: { roles: ['biuro', 'manager'] } },
  { path: '/rentals/new',   component: () => import('@/views/RentalCalculatorView.vue'), meta: { roles: ['biuro', 'manager'] } },
  { path: '/rentals/:id',   component: () => import('@/views/RentalDetailView.vue'),  meta: { roles: ['biuro', 'manager'] } },
  { path: '/inspections/new', component: () => import('@/views/InspectionFormView.vue') },
  { path: '/inspections',   component: () => import('@/views/InspectionListView.vue') },
  { path: '/kanban',        component: () => import('@/views/KanbanView.vue') },
]

export const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.path === '/login' && auth.isAuthed) return { path: '/' }
  if (!to.meta.public && !auth.isAuthed) return { path: '/login', query: { next: to.fullPath } }

  const roles = to.meta.roles as string[] | undefined
  if (roles && auth.user && !roles.includes(auth.user.role)) return { path: '/' }

  return true
})
