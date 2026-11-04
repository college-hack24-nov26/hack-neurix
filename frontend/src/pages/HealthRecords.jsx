import React, { useState, useCallback, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { FileText, Upload, Trash2, Eye, Brain, Download, Search, File, Image, AlertCircle } from 'lucide-react'
import { recordsService } from '../services/api'
import toast from 'react-hot-toast'

const typeLabels = {
  lab_report:  { label: 'Lab Report',   bg: 'bg-blue-50 dark:bg-blue-900/20',   text: 'text-blue-600 dark:text-blue-400' },
  scan:        { label: 'Medical Scan', bg: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-600 dark:text-purple-400' },
  prescription:{ label: 'Prescription', bg: 'bg-green-50 dark:bg-green-900/20',  text: 'text-green-600 dark:text-green-400' },
  document:    { label: 'Document',     bg: 'bg-slate-50 dark:bg-slate-800',      text: 'text-slate-600 dark:text-slate-400' },
  xray:        { label: 'X-Ray',        bg: 'bg-amber-50 dark:bg-amber-900/20',   text: 'text-amber-600 dark:text-amber-400' },
}

function formatBytes(bytes) {
  if (!bytes) return 'N/A'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function HealthRecords() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [uploading, setUploading] = useState(false)
  const [uploadForm, setUploadForm] = useState({ name: '', type: 'lab_report' })
  const [showUpload, setShowUpload] = useState(false)
  const [analyzingId, setAnalyzingId] = useState(null)

  const loadRecords = async () => {
    try {
      const { data } = await recordsService.getAll()
      setRecords(data.records || [])
    } catch {
      toast.error('Failed to load records.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadRecords() }, [])

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length === 0) return
    const file = acceptedFiles[0]
    setUploadForm((f) => ({ ...f, name: f.name || file.name.replace(/\.[^.]+$/, '') }))
    setShowUpload(true)
  }, [])

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxSize: 20 * 1024 * 1024,
  })

  const handleUpload = async () => {
    if (!uploadForm.name) { toast.error('Please enter a name for this record'); return }
    if (!acceptedFiles[0]) { toast.error('Please select a file to upload'); return }
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', acceptedFiles[0])
      formData.append('name', uploadForm.name)
      formData.append('record_type', uploadForm.type)
      const { data } = await recordsService.upload(formData)
      setRecords((prev) => [data, ...prev])
      toast.success('Record uploaded successfully!')
      setShowUpload(false)
      setUploadForm({ name: '', type: 'lab_report' })
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await recordsService.delete(id)
      setRecords((prev) => prev.filter((r) => r.id !== id))
      toast.success('Record deleted.')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Delete failed.')
    }
  }

  const handleAnalyze = async (id) => {
    setAnalyzingId(id)
    try {
      const { data } = await recordsService.analyze(id)
      setRecords((prev) => prev.map((r) => r.id === id ? { ...r, is_analyzed: true, ai_analysis: data.ai_analysis } : r))
      toast.success('AI analysis complete!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed.')
    } finally {
      setAnalyzingId(null)
    }
  }

  const filtered = records.filter((r) => {
    const name = r.name || ''
    const tags = r.tags || []
    const matchSearch = name.toLowerCase().includes(search.toLowerCase()) ||
      tags.some((t) => t.toLowerCase().includes(search.toLowerCase()))
    const matchFilter = filter === 'all' || r.record_type === filter
    return matchSearch && matchFilter
  })

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="section-title">Health Records</h1>
          <p className="section-subtitle text-sm">Securely store and manage your medical documents</p>
        </div>
        <button onClick={() => setShowUpload(!showUpload)} className="btn-primary text-sm px-4 py-2.5">
          <Upload size={15} /> Upload Record
        </button>
      </div>

      {showUpload && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Upload Medical Record</h2>
          <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${isDragActive ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/10' : 'border-slate-200 dark:border-slate-700 hover:border-blue-300'}`}>
            <input {...getInputProps()} />
            <Upload size={32} className="mx-auto text-slate-400 mb-3" />
            {isDragActive ? (
              <p className="text-blue-600 font-medium">Drop the file here</p>
            ) : (
              <>
                <p className="text-slate-600 dark:text-slate-400 font-medium">Drag and drop a file here, or click to select</p>
                <p className="text-xs text-slate-400 mt-1">Supports: PDF, JPG, PNG, WEBP — Max 20 MB</p>
              </>
            )}
            {acceptedFiles[0] && (
              <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-900/20 text-green-600 rounded-lg text-sm">
                <File size={14} /> {acceptedFiles[0].name}
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Record Name</label>
              <input value={uploadForm.name} onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })} placeholder="e.g. Blood test March 2025" className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Record Type</label>
              <select value={uploadForm.type} onChange={(e) => setUploadForm({ ...uploadForm, type: e.target.value })} className="input-field">
                <option value="lab_report">Lab Report</option>
                <option value="prescription">Prescription</option>
                <option value="scan">Medical Scan</option>
                <option value="xray">X-Ray</option>
                <option value="document">Other Document</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button onClick={handleUpload} disabled={uploading} className="btn-primary">{uploading ? 'Uploading...' : 'Save Record'}</button>
            <button onClick={() => setShowUpload(false)} className="btn-secondary">Cancel</button>
          </div>
        </motion.div>
      )}

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search records..." className="input-field pl-10" />
        </div>
        <div className="flex gap-2 flex-wrap">
          {['all', 'lab_report', 'prescription', 'scan'].map((f) => (
            <button key={f} onClick={() => setFilter(f)} className={`px-3 py-2 rounded-xl text-xs font-medium transition-all capitalize ${filter === f ? 'bg-blue-600 text-white' : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'}`}>
              {f === 'all' ? 'All' : f.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading records...</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((record, i) => {
            const tc = typeLabels[record.record_type] || typeLabels.document
            const isAnalyzing = analyzingId === record.id
            return (
              <motion.div key={record.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="glass-card p-4 hover:shadow-card-hover transition-all">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl ${tc.bg} flex items-center justify-center flex-shrink-0`}>
                    {record.mime_type?.startsWith('image/') ? <Image size={22} className={tc.text} /> : <FileText size={22} className={tc.text} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-semibold text-slate-800 dark:text-slate-100 truncate">{record.name}</p>
                      {record.is_analyzed && <span className="badge-success text-xs">Analyzed</span>}
                    </div>
                    <div className="flex items-center gap-3 mt-1 flex-wrap">
                      <span className={`text-xs font-medium ${tc.text}`}>{tc.label}</span>
                      <span className="text-xs text-slate-400">{formatDate(record.uploaded_at)}</span>
                      <span className="text-xs text-slate-400">{formatBytes(record.file_size)}</span>
                      {(record.tags || []).map((t) => (
                        <span key={t} className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-500 rounded text-xs">{t}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {!record.is_analyzed && (
                      <button onClick={() => handleAnalyze(record.id)} disabled={isAnalyzing} className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg text-xs font-medium hover:bg-blue-100 transition-colors disabled:opacity-60">
                        <Brain size={13} /> {isAnalyzing ? 'Analyzing...' : 'Analyze'}
                      </button>
                    )}
                    <button onClick={() => handleDelete(record.id)} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-16">
          <AlertCircle size={40} className="text-slate-300 dark:text-slate-600 mx-auto mb-3" />
          <p className="text-slate-500 dark:text-slate-400">{records.length === 0 ? 'No records yet. Upload your first medical document.' : 'No records match your search.'}</p>
        </div>
      )}

      <p className="text-xs text-center text-slate-400">Files are stored securely. Only you can access your health records.</p>
    </div>
  )
}
