<template>
  <div>
    <canvas ref="cv" :width="width" :height="height" style="border:1px solid #999; background:#fff; touch-action:none"></canvas>
    <div class="q-mt-xs">
      <q-btn size="sm" flat icon="clear" label="Wyczyść" @click="clear" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import SignaturePad from 'signature_pad'

defineProps<{ width?: number; height?: number }>()
const emit = defineEmits<{ (e: 'change', dataUrl: string | null): void }>()

const cv = ref<HTMLCanvasElement | null>(null)
let pad: SignaturePad | null = null

onMounted(() => {
  if (!cv.value) return
  pad = new SignaturePad(cv.value, { penColor: '#111' })
  pad.addEventListener('endStroke', () => emit('change', pad?.isEmpty() ? null : pad!.toDataURL('image/png')))
})

onBeforeUnmount(() => { pad?.off() })

function clear() {
  pad?.clear()
  emit('change', null)
}
</script>
