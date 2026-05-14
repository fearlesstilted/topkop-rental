import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import axios from 'axios'

export type Role = 'biuro' | 'manager'

interface LoginResponse {
  access_token: string
  token_type: string
  user_id: number
  name: string
  role: Role
}

const TOKEN_KEY = 'topkop_token'
const USER_KEY = 'topkop_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const rawUser = localStorage.getItem(USER_KEY)
  const user = ref<{ id: number; name: string; role: Role } | null>(
    rawUser ? JSON.parse(rawUser) : null
  )

  const isAuthed = computed(() => !!token.value && !!user.value)

  async function login(pin: string) {
    const { data } = await axios.post<LoginResponse>('/api/auth/login', { pin })
    token.value = data.access_token
    user.value = { id: data.user_id, name: data.name, role: data.role }
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(user.value))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return { token, user, isAuthed, login, logout }
})
