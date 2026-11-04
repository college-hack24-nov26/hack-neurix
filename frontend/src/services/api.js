import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // The instance default is application/json, and axios then turns a FormData body into
    // JSON (the file is lost -> server answers 422). Force multipart for every file upload;
    // the browser adds the boundary itself.
    if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
      config.headers.set('Content-Type', 'multipart/form-data')
    }
    const stored = localStorage.getItem('homecare-auth')
    if (stored) {
      const { state } = JSON.parse(stored)
      if (state?.token) {
        config.headers.Authorization = `Bearer ${state.token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    const config = response.config || {}
    const method = (config.method || 'get').toLowerCase()
    const url = config.url || ''

    if (!['post', 'put', 'patch', 'delete'].includes(method) || url.startsWith('/history')) {
      return response
    }

    const labels = {
      '/symptoms/analyze': ['symptom_check', 'Symptom check completed'],
      '/chat/message': ['chat_message', 'Sent an AI assistant message'],
      '/analysis/image': ['image_analysis', 'Analyzed a medical image'],
      '/analysis/report': ['report_summary', 'Summarized a medical report'],
      '/health/metrics': ['vital_added', 'Added a health metric'],
      '/records': ['health_record', method === 'delete' ? 'Deleted a health record' : 'Updated health records'],
      '/insurance': ['insurance', method === 'delete' ? 'Deleted insurance policy' : 'Updated insurance policy'],
      '/telemedicine': ['consultation', 'Booked telemedicine consultation'],
      '/laboratories': ['laboratory', 'Booked a laboratory test'],
      '/auth/profile': ['profile', 'Updated profile settings'],
      '/auth/password': ['security', 'Changed account password'],
    }

    const match = Object.entries(labels).find(([prefix]) => url.startsWith(prefix))
    if (match) {
      const [action, title] = match[1]
      api.post('/history', {
        action,
        title,
        details: method === 'delete' ? { method: 'DELETE' } : {},
        route: window.location.pathname,
      }).catch(() => {})
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('homecare-auth')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// ─── API service methods ───────────────────────────────────────────────────────

export const authService = {
  login:       (data)   => api.post('/auth/login', data),
  register:    (data)   => api.post('/auth/register', data),
  getProfile:  ()       => api.get('/auth/profile'),
  updateProfile:(data)  => api.put('/auth/profile', data),
  changePassword:(data) => api.put('/auth/password', data),
}

export const symptomService = {
  // data = { symptoms: [...], follow_up: {...} } — pass directly, no extra wrapping
  analyze:     (data)     => api.post('/symptoms/analyze', data),
  getSymptoms: ()         => api.get('/symptoms/list'),
  getFollowUp: (data)     => api.post('/symptoms/followup', data),
}

export const diseaseService = {
  getAll:      (params)   => api.get('/diseases', { params }),
  getById:     (id)       => api.get(`/diseases/${id}`),
  getByOrgan:  (organ)    => api.get(`/diseases/organ/${organ}`),
  search:      (q)        => api.get(`/diseases/search?q=${q}`),
  getOrgans:   ()         => api.get('/diseases/organs'),
}

export const chatService = {
  sendMessage: (messages, lang) => api.post('/chat/message', { messages, language: lang }),
  getHistory:  ()               => api.get('/chat/history'),
  clearHistory: ()              => api.delete('/chat/history'),
}

export const healthService = {
  getMetrics:  ()        => api.get('/health/metrics'),
  addMetric:   (data)    => api.post('/health/metrics', data),
  getHistory:  (type)    => api.get(`/health/metrics/${type}`),
  getDashboard:()        => api.get('/health/dashboard'),
}

export const recordsService = {
  getAll:   ()       => api.get('/records'),
  upload:   (form)   => api.post('/records/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getById:  (id)     => api.get(`/records/${id}`),
  delete:   (id)     => api.delete(`/records/${id}`),
  analyze:  (id)     => api.post(`/records/${id}/analyze`),
}

export const hospitalService = {
  getNearby: (lat, lng, radius) =>
    api.get('/hospitals/nearby', { params: { lat, lng, radius } }),
  search:    (q) => api.get(`/hospitals/search?q=${q}`),
  getById:   (id) => api.get(`/hospitals/${id}`),
}

export const insuranceService = {
  getAll:    ()     => api.get('/insurance'),
  add:       (data) => api.post('/insurance', data),
  update:    (id, data) => api.put(`/insurance/${id}`, data),
  delete:    (id)   => api.delete(`/insurance/${id}`),
}

export const imageAnalysisService = {
  status:   () => api.get('/analysis/status'),
  // Live connectivity test of every configured vision provider (needs login).
  diagnose: () => api.get('/analysis/diagnose', { timeout: 120000 }),
  analyze: (form) => api.post('/analysis/image', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 150000,
  }),
  summarizeReport: (form) => api.post('/analysis/report', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 150000,
  }),
}

export const telemedicineService = {
  getDoctors: (specialty) => api.get('/telemedicine/doctors', { params: specialty ? { specialization: specialty } : {} }),
  book:       (data)      => api.post('/telemedicine/book', data),
  getConsultations: () => api.get('/telemedicine/consultations'),
  uploadPrescription: (bookingId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/telemedicine/consultations/${bookingId}/prescription`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  downloadPrescription: (bookingId) =>
    api.get(`/telemedicine/consultations/${bookingId}/prescription/download`, { responseType: 'blob' }),
}

export const laboratoryService = {
  getCatalogue: (area) => api.get('/laboratories/catalogue', { params: area ? { area } : {} }),
  getNearby:    (area) => api.get('/laboratories/nearby', { params: { area } }),
  book:         (data)    => api.post('/laboratories/book', data),
  getBookings:  ()        => api.get('/laboratories/bookings'),
  getReports:   ()        => api.get('/laboratories/reports'),
  uploadReport: (bookingId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/laboratories/bookings/${bookingId}/reports`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  downloadReport: (reportId) => api.get(`/laboratories/reports/${reportId}/download`, {
    responseType: 'blob',
  }),
}

export const historyService = {
  getAll: () => api.get('/history'),
  add: (data) => api.post('/history', data),
  delete: (id) => api.delete(`/history/${id}`),
  clear: () => api.delete('/history'),
}
