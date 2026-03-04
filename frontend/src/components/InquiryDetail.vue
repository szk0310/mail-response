<script setup lang="ts">
import { ref } from 'vue'
import { useInquiriesStore } from '../stores/inquiries'
import { INQUIRY_TYPE_LABELS, INQUIRY_STATUS_LABELS } from '../types/inquiry'
import StatusBadge from './StatusBadge.vue'

const store = useInquiriesStore()
const copySuccess = ref(false)

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function copyReply() {
  if (!store.selected) return
  await navigator.clipboard.writeText(store.selected.reply_draft)
  copySuccess.value = true
  setTimeout(() => (copySuccess.value = false), 2000)
}

async function handleSetStatus(status: 'sent' | 'rejected') {
  if (!store.selected) return
  try {
    await store.setStatus(store.selected.id, status)
  } catch {
    alert(store.error ?? 'ステータスの更新に失敗しました')
  }
}

async function handleDelete() {
  if (!store.selected) return
  if (!confirm('この問い合わせを削除しますか？')) return
  try {
    await store.remove(store.selected.id)
  } catch {
    alert(store.error ?? '削除に失敗しました')
  }
}
</script>

<template>
  <!-- Backdrop -->
  <div
    v-if="store.selected"
    class="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
    @click="store.clearSelected"
  />

  <!-- Modal -->
  <div
    v-if="store.selected"
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
  >
    <div class="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl bg-white shadow-2xl">
      <!-- Header -->
      <div class="sticky top-0 flex items-start justify-between border-b border-gray-200 bg-white px-6 py-4">
        <div>
          <h2 class="text-lg font-bold text-gray-900">{{ store.selected.email_subject }}</h2>
          <p class="mt-0.5 text-sm text-gray-500">
            {{ store.selected.email_sender }} &middot; {{ formatDate(store.selected.email_date) }}
          </p>
        </div>
        <button
          class="ml-4 rounded-full p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          @click="store.clearSelected"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="px-6 py-4 space-y-5">
        <!-- Meta -->
        <div class="flex flex-wrap gap-2 items-center">
          <span class="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
            {{ INQUIRY_TYPE_LABELS[store.selected.inquiry_type] }}
          </span>
          <StatusBadge :status="store.selected.status" />
        </div>

        <!-- Original email body -->
        <div>
          <h3 class="mb-2 text-sm font-semibold text-gray-700">元のメール本文</h3>
          <div class="max-h-48 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
            {{ store.selected.email_body }}
          </div>
        </div>

        <!-- Reply draft -->
        <div>
          <div class="mb-2 flex items-center justify-between">
            <h3 class="text-sm font-semibold text-gray-700">Claude 生成の返信文</h3>
            <button
              class="flex items-center gap-1 rounded border border-gray-300 px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50"
              @click="copyReply"
            >
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              {{ copySuccess ? 'コピーしました！' : 'コピー' }}
            </button>
          </div>
          <div class="max-h-64 overflow-y-auto rounded-lg border border-indigo-100 bg-indigo-50 p-3 text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
            {{ store.selected.reply_draft }}
          </div>
        </div>

        <!-- Gmail Draft ID -->
        <p class="text-xs text-gray-400">Gmail 下書き ID: {{ store.selected.gmail_draft_id }}</p>

        <!-- Status actions -->
        <div v-if="store.selected.status === 'draft'" class="flex gap-3 pt-2">
          <button
            class="flex-1 rounded-lg bg-green-600 py-2 text-sm font-medium text-white hover:bg-green-700"
            @click="handleSetStatus('sent')"
          >
            送信済みにする
          </button>
          <button
            class="flex-1 rounded-lg bg-red-600 py-2 text-sm font-medium text-white hover:bg-red-700"
            @click="handleSetStatus('rejected')"
          >
            却下する
          </button>
        </div>
        <div v-else class="rounded-lg bg-gray-50 px-4 py-3 text-center text-sm text-gray-500">
          ステータス: {{ INQUIRY_STATUS_LABELS[store.selected.status] }}（変更不可）
        </div>

        <!-- Delete -->
        <div class="border-t border-gray-100 pt-3">
          <button
            class="w-full rounded-lg border border-red-200 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
            @click="handleDelete"
          >
            このレコードを削除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
