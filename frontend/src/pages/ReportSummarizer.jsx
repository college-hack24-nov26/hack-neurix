import React, { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { FileText, Upload, Brain, AlertTriangle, CheckCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { imageAnalysisService } from '../services/api'
import toast from 'react-hot-toast'
import { useThemeStore } from '../store/themeStore'


const statusIcon = (s) => {
  if (s === 'low')    return <TrendingDown size={14} className="text-blue-500" />
  if (s === 'high')   return <TrendingUp   size={14} className="text-red-500" />
  return                     <Minus        size={14} className="text-green-500" />
}
const statusBadge = (s) => {
  if (s === 'low')    return 'badge-info'
  if (s === 'high')   return 'badge-danger'
  return                     'badge-success'
}

export default function ReportSummarizer() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const { language } = useThemeStore()

  const onDrop = useCallback((accepted) => {
    if (accepted.length) { setFile(accepted[0]); setResult(null) }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'image/*': ['.jpg', '.jpeg', '.png', '.webp'], 'text/plain': ['.txt'] },
    maxFiles: 1, maxSize: 20 * 1024 * 1024,
  })

  const handleSummarize = async () => {
    if (!file) { toast.error('Please upload a report first'); return }
    setLoading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('language', language || 'en')
      const { data } = await imageAnalysisService.summarizeReport(form)
      setResult(data)
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : 'Summarization failed. Please try again.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">AI Report Summarizer</h1>
        <p className="text-slate-500 text-sm mt-1">Upload a lab report for an AI-generated easy-to-understand summary</p>
      </div>

      {!result ? (
        <div className="space-y-5">
          <div {...getRootProps()} className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all glass-card ${isDragActive ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/10' : 'hover:border-blue-300'}`}>
            <input {...getInputProps()} />
            <FileText size={40} className="text-slate-400 mx-auto mb-3" />
            {file ? (
              <><p className="font-medium text-slate-700 dark:text-slate-300">{file.name}</p><p className="text-xs text-slate-400 mt-1">Click to change file</p></>
            ) : (
              <><p className="font-medium text-slate-600 dark:text-slate-400">Upload your medical report (PDF or image)</p><p className="text-xs text-slate-400 mt-1">Lab reports, blood tests, pathology results — Max 20 MB</p></>
            )}
          </div>
          <button onClick={handleSummarize} disabled={!file || loading} className="btn-primary w-full justify-center py-3.5">
            {loading ? <span className="flex items-center gap-2"><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z"/></svg>Analyzing report...</span> : <><Brain size={18} /> Summarize Report</>}
          </button>
        </div>
      ) : (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
          <div className="glass-card p-6">
            <div className="flex flex-wrap gap-3 mb-4 text-sm text-slate-500 dark:text-slate-400">
              <span className="font-semibold text-slate-800 dark:text-slate-100">{result.report_type}</span>
              <span>·</span><span>{result.test_date}</span><span>·</span><span>{result.lab_name}</span>
            </div>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{result.summary}</p>
          </div>

          <div className="glass-card p-6 overflow-x-auto">
            <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Test Results Breakdown</h2>
            <table className="w-full text-sm">
              <thead><tr className="text-left border-b border-slate-100 dark:border-slate-700">
                {['Parameter', 'Value', 'Normal Range', 'Status', 'Note'].map((h) => (
                  <th key={h} className="pb-3 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr></thead>
              <tbody className="divide-y divide-slate-50 dark:divide-slate-800">
                {(result.findings || []).map((f, i) => (
                  <tr key={`${f.parameter}-${i}`} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="py-3 pr-4 font-medium text-slate-700 dark:text-slate-300">{f.parameter}</td>
                    <td className="py-3 pr-4 font-bold text-slate-800 dark:text-slate-100">{f.value}</td>
                    <td className="py-3 pr-4 text-slate-400">{f.normal_range}</td>
                    <td className="py-3 pr-4"><span className={`${statusBadge(f.status)} flex items-center gap-1`}>{statusIcon(f.status)} {f.status}</span></td>
                    <td className="py-3 text-slate-500 dark:text-slate-400 text-xs">{f.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="glass-card p-5">
            <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-3">Recommendations</h2>
            <ul className="space-y-2">{(result.recommendations || []).map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
                <CheckCircle size={14} className="text-green-500 flex-shrink-0 mt-0.5" /> {r}
              </li>
            ))}</ul>
          </div>

          <div className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
            <AlertTriangle size={15} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-700 dark:text-amber-400">{result.disclaimer}</p>
          </div>
          <button onClick={() => { setResult(null); setFile(null) }} className="btn-secondary">Analyze Another Report</button>
        </motion.div>
      )}
    </div>
  )
}
