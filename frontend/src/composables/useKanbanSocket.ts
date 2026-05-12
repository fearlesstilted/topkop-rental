import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from '@/stores/auth'

export type KanbanSocketEvent = {
  event: string
  payload: Record<string, unknown>
}

const HEARTBEAT_MS = 30_000
const RECONNECT_MS = 3_000
const POLICY_VIOLATION_CLOSE_CODE = 1008

function resolveSocketUrl(token: string): string {
  const configured = import.meta.env.VITE_WS_BASE_URL
  if (configured) return `${configured.replace(/\/$/, '')}/ws/kanban?token=${encodeURIComponent(token)}`

  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${location.host}/ws/kanban?token=${encodeURIComponent(token)}`
}

function parseSocketEvent(data: string): KanbanSocketEvent | null {
  try {
    const parsed = JSON.parse(data) as Partial<KanbanSocketEvent>
    if (typeof parsed.event !== 'string' || typeof parsed.payload !== 'object' || parsed.payload === null) {
      return null
    }
    return { event: parsed.event, payload: parsed.payload as Record<string, unknown> }
  } catch {
    return null
  }
}

export function useKanbanSocket(onMessage: (evt: KanbanSocketEvent) => void) {
  const connected = ref(false)
  const $q = useQuasar()
  const auth = useAuthStore()
  let ws: WebSocket | null = null
  let reconnectTimer: number | null = null
  let pingTimer: number | null = null

  function connect() {
    const token = auth.token
    if (!token) return
    ws = new WebSocket(resolveSocketUrl(token))

    ws.onopen = () => {
      connected.value = true
      pingTimer = window.setInterval(() => ws?.readyState === WebSocket.OPEN && ws.send('ping'), HEARTBEAT_MS)
    }

    ws.onclose = (e) => {
      connected.value = false
      if (pingTimer) clearInterval(pingTimer)
      if (e.code === POLICY_VIOLATION_CLOSE_CODE) {
        $q.notify({ type: 'warning', message: 'Kanban: sesja wygasła, zaloguj się ponownie' })
        return
      }
      reconnectTimer = window.setTimeout(connect, RECONNECT_MS)
    }

    ws.onerror = () => {
      connected.value = false
    }

    ws.onmessage = (e: MessageEvent<string>) => {
      const event = parseSocketEvent(e.data)
      if (event) onMessage(event)
    }
  }

  onMounted(connect)
  onBeforeUnmount(() => {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (pingTimer) clearInterval(pingTimer)
    ws?.close()
  })

  return { connected }
}
