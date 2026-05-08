<template>
  <div class="q-gutter-xs">
    <div class="text-caption">{{ label }}</div>
    <div v-if="preview">
      <img :src="preview" style="max-width:120px; max-height:90px; border:1px solid #ccc" />
      <q-btn size="sm" flat icon="close" @click="clear" />
    </div>
    <q-btn v-else outline icon="photo_camera" :label="label" @click="pick" />
    <input ref="inp" type="file" accept="image/*" capture="environment" style="display:none" @change="onChange" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ label: string }>()
const emit = defineEmits<{ (e: 'change', file: File | null): void }>()

const inp = ref<HTMLInputElement | null>(null)
const preview = ref<string | null>(null)
let current: File | null = null

function pick() { inp.value?.click() }

function onChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0] ?? null
  current = file
  if (file) {
    preview.value = URL.createObjectURL(file)
    emit('change', file)
  } else {
    clear()
  }
}

function clear() {
  current = null
  if (preview.value) URL.revokeObjectURL(preview.value)
  preview.value = null
  if (inp.value) inp.value.value = ''
  emit('change', null)
}
</script>
