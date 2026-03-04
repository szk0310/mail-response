<script setup lang="ts">
import type { InquiryStatus } from '../types/inquiry'
import { INQUIRY_STATUS_LABELS } from '../types/inquiry'

const props = defineProps<{ status: InquiryStatus }>()

const colorMap: Record<InquiryStatus, string> = {
  draft: 'bg-yellow-100 text-yellow-800',
  sent: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
}
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
    :class="colorMap[props.status]"
  >
    {{ INQUIRY_STATUS_LABELS[props.status] }}
  </span>
</template>
