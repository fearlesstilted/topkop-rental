import Dexie, { type Table } from 'dexie'

export interface OfflineInspection {
  id?: number
  client_local_id: string
  payload: Record<string, unknown>
  photos: { slot: string; blob: Blob }[]
  signature_data_url?: string
  created_at: number
}

class OfflineDB extends Dexie {
  inspections!: Table<OfflineInspection, number>
  constructor() {
    super('topkop_offline')
    this.version(1).stores({
      inspections: '++id,client_local_id,created_at'
    })
  }
}

export const offlineDb = new OfflineDB()

export async function enqueueInspection(item: OfflineInspection): Promise<number> {
  return (await offlineDb.inspections.add(item)) as number
}

export async function listQueued(): Promise<OfflineInspection[]> {
  return await offlineDb.inspections.toArray()
}

export async function removeQueued(id: number): Promise<void> {
  await offlineDb.inspections.delete(id)
}

export async function flushQueue(
  send: (item: OfflineInspection) => Promise<boolean>
): Promise<number> {
  const items = await listQueued()
  let synced = 0
  for (const it of items) {
    try {
      const ok = await send(it)
      if (ok && it.id !== undefined) {
        await removeQueued(it.id)
        synced++
      }
    } catch {
      // остаёмся офлайн
      break
    }
  }
  return synced
}
