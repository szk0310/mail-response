import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import type { Inquiry, InquiryStatus } from '../types/inquiry'
import { deleteInquiry, fetchInquiries, fetchInquiry, runAgent, updateStatus } from '../api/client'

export const useInquiriesStore = defineStore('inquiries', () => {
  const inquiries = ref<Inquiry[]>([])
  const selected = ref<Inquiry | null>(null)
  const loading = ref(false)
  const running = ref(false)
  const error = ref<string | null>(null)
  const filter = reactive({ status: '' as InquiryStatus | '', inquiry_type: '' })

  async function load() {
    loading.value = true
    error.value = null
    try {
      const res = await fetchInquiries({
        status: filter.status || undefined,
        inquiry_type: filter.inquiry_type || undefined,
      })
      inquiries.value = res.data
    } catch (e) {
      error.value = '問い合わせの取得に失敗しました'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  // ローディングスピナーなしでサイレントにリスト更新
  async function silentLoad() {
    try {
      const res = await fetchInquiries({
        status: filter.status || undefined,
        inquiry_type: filter.inquiry_type || undefined,
      })
      inquiries.value = res.data
    } catch (e) {
      console.error('silent load error:', e)
    }
  }

  async function run() {
    running.value = true
    error.value = null
    try {
      const res = await runAgent()
      // 10秒後・30秒後・60秒後にサイレント更新（スピナーなし）
      setTimeout(() => silentLoad(), 10000)
      setTimeout(() => silentLoad(), 30000)
      setTimeout(() => { silentLoad(); running.value = false }, 60000)
      return res.data
    } catch (e) {
      error.value = 'エージェントの実行に失敗しました'
      console.error(e)
      running.value = false
      throw e
    }
  }

  async function select(id: string) {
    loading.value = true
    try {
      const res = await fetchInquiry(id)
      selected.value = res.data
    } catch (e) {
      error.value = '詳細の取得に失敗しました'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function setStatus(id: string, status: InquiryStatus) {
    try {
      const res = await updateStatus(id, status)
      // Update in list
      const idx = inquiries.value.findIndex((i) => i.id === id)
      if (idx !== -1) {
        inquiries.value[idx] = res.data
      }
      // Update selected if open
      if (selected.value?.id === id) {
        selected.value = res.data
      }
    } catch (e) {
      error.value = 'ステータスの更新に失敗しました'
      console.error(e)
      throw e
    }
  }

  async function remove(id: string) {
    try {
      await deleteInquiry(id)
      inquiries.value = inquiries.value.filter((i) => i.id !== id)
      if (selected.value?.id === id) selected.value = null
    } catch (e) {
      error.value = '削除に失敗しました'
      console.error(e)
      throw e
    }
  }

  function clearSelected() {
    selected.value = null
  }

  return {
    inquiries,
    selected,
    loading,
    running,
    error,
    filter,
    load,
    run,
    select,
    setStatus,
    remove,
    clearSelected,
  }
})
