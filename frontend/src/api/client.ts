import axios from 'axios'
import type { Inquiry, InquiryStatus } from '../types/inquiry'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001' })

export interface FetchInquiriesParams {
  status?: InquiryStatus | ''
  inquiry_type?: string
  limit?: number
}

export const runAgent = () => api.post<{ message: string; processed: number; ids: string[] }>('/api/run')

export const fetchInquiries = (params?: FetchInquiriesParams) =>
  api.get<Inquiry[]>('/api/inquiries', {
    params: {
      ...(params?.status ? { status: params.status } : {}),
      ...(params?.inquiry_type ? { inquiry_type: params.inquiry_type } : {}),
      ...(params?.limit ? { limit: params.limit } : {}),
    },
  })

export const fetchInquiry = (id: string) => api.get<Inquiry>(`/api/inquiries/${id}`)

export const updateStatus = (id: string, status: InquiryStatus) =>
  api.patch<Inquiry>(`/api/inquiries/${id}/status`, { status })

export const deleteInquiry = (id: string) =>
  api.delete(`/api/inquiries/${id}`)
