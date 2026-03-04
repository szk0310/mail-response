<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useInquiriesStore } from '../stores/inquiries'
import type { InquiryStatus } from '../types/inquiry'
import { INQUIRY_TYPE_LABELS } from '../types/inquiry'
import StatusBadge from './StatusBadge.vue'

const store = useInquiriesStore()

onMounted(() => store.load())

watch(() => [store.filter.status, store.filter.inquiry_type], () => {
  store.load()
})

async function handleRun() {
  try {
    await store.run()
  } catch {
    alert(store.error ?? 'エラーが発生しました')
  }
}

async function handleDelete(id: string) {
  if (!confirm('この問い合わせを削除しますか？')) return
  try {
    await store.remove(id)
  } catch {
    alert(store.error ?? '削除に失敗しました')
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="p-4 md:p-6">
    <!-- Header -->
    <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="text-2xl font-bold text-gray-900">問い合わせ一覧</h1>
      <button
        class="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-indigo-700 disabled:opacity-50"
        :disabled="store.running"
        @click="handleRun"
      >
        <svg v-if="store.running" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span>{{ store.running ? '実行中...' : 'エージェント実行' }}</span>
      </button>
    </div>

    <!-- Filters -->
    <div class="mb-4 flex flex-col gap-2 sm:flex-row">
      <select
        v-model="store.filter.status"
        class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
      >
        <option value="">ステータス: すべて</option>
        <option value="draft">下書き</option>
        <option value="sent">送信済み</option>
        <option value="rejected">却下</option>
      </select>
      <select
        v-model="store.filter.inquiry_type"
        class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
      >
        <option value="">種別: すべて</option>
        <option value="service_pricing">サービス・料金</option>
        <option value="quote_request">見積もり依頼</option>
        <option value="existing_client">既存クライアント</option>
      </select>
      <button
        class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm hover:bg-gray-50"
        @click="store.load"
      >
        更新
      </button>
    </div>

    <!-- Error -->
    <div v-if="store.error" class="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
      {{ store.error }}
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="flex justify-center py-12">
      <svg class="h-8 w-8 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- Empty state -->
    <div v-else-if="store.inquiries.length === 0" class="py-12 text-center text-gray-400">
      問い合わせはありません
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto rounded-lg border border-gray-200 shadow">
      <table class="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left font-semibold text-gray-600">受信日時</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-600">差出人</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-600">件名</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-600">種別</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-600">ステータス</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="inquiry in store.inquiries"
            :key="inquiry.id"
            class="transition hover:bg-gray-50"
          >
            <td class="whitespace-nowrap px-4 py-3 text-gray-500">
              {{ formatDate(inquiry.email_date) }}
            </td>
            <td class="max-w-[160px] truncate px-4 py-3 text-gray-700">
              {{ inquiry.email_sender }}
            </td>
            <td class="max-w-[240px] truncate px-4 py-3 text-gray-900 font-medium">
              {{ inquiry.email_subject }}
            </td>
            <td class="whitespace-nowrap px-4 py-3">
              <span class="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                {{ INQUIRY_TYPE_LABELS[inquiry.inquiry_type] }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3">
              <StatusBadge :status="inquiry.status" />
            </td>
            <td class="px-4 py-3">
              <div class="flex gap-1.5">
                <button
                  class="rounded bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100"
                  @click="store.select(inquiry.id)"
                >
                  詳細
                </button>
                <button
                  class="rounded bg-red-50 px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-100"
                  @click="handleDelete(inquiry.id)"
                >
                  削除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
