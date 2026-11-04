import React, { useState, useCallback, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  Upload, Image, FileText, Brain, AlertTriangle, CheckCircle, Info, RotateCcw, Loader,
  AlertCircle, Sparkles, XCircle, Activity, HelpCircle, ShieldAlert,
} from 'lucide-react'
import { imageAnalysisService } from '../services/api'
import { useThemeStore } from '../store/themeStore'
import toast from 'react-hot-toast'

const analysisTypes = [
  { key: 'xray',   label: 'X-Ray',          icon: Image,    desc: 'Chest, bone, or other radiographs' },
  { key: 'skin',   label: 'Skin Photo',     icon: Image,    desc: 'Skin conditions, rashes, or lesions' },
  { key: 'report', label: 'Report Photo',   icon: FileText, desc: 'Photo of a lab or medical report' },
  { key: 'scan',   label: 'CT / MRI / Ultrasound', icon: Brain, desc: 'Cross-sectional imaging' },
]

const URGENCY = {
  routine:   { label: 'Routine',   cls: 'border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-300', icon: CheckCircle },
  soon:      { label: 'See a doctor soon', cls: 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-300', icon: Info },
  urgent:    { label: 'Urgent — see a doctor today/tomorrow', cls: 'border-orange-300 dark:border-orange-700 bg-orange-50 dark:bg-orange-900/20 text-orange-800 dark:text-orange-300', icon: AlertTriangle },
  emergency: { label: 'Possible emergency — seek care now (India: call 112)', cls: 'border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300', icon: ShieldAlert },
}

const LIKELIHOOD_CLS = {
  high:     'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  moderate: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  low:      'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
}

const asArray = (v) => (Array.isArray(v) ? v : v ? [v] : [])

function Section({ icon: Icon, iconCls, title, children }) {
  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-2 mb-3">
        <Icon size={17} className={iconCls} />
        <h3 className="font-semibold text-slate-800 dark:text-slate-100">{title}</h3>
      </div>
      {children}
    </div>
  )
}

function BulletList({ items, iconCls = 'text-green-500' }) {
  return (
    <ul className="space-y-2">
      {items.map((t, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
          <CheckCircle size={14} className={`${iconCls} flex-shrink-0 mt-0.5`} /> <span>{t}</span>
        </li>
      ))}
    </ul>
  )
}

export default function ImageAnalysis() {
  const { language } = useThemeStore()
  const [analysisType, setAnalysisType] = useState('xray')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)          // { message, attempts }
  const [aiStatus, setAiStatus] = useState(null)
  const [diag, setDiag] = useState(null)
  const [diagLoading, setDiagLoading] = useState(false)

  useEffect(() => {
    imageAnalysisService.status()
      .then(({ data }) => setAiStatus(data))
      .catch(() => setAiStatus({ vision_available: false, chat_available: false, message: 'Could not reach the AI status service. Is the backend running?' }))
  }, [])

  // Free the object URL when the preview changes or the page unmounts.
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  const onDrop = useCallback((accepted, rejected) => {
    if (rejected?.length) {
      const code = rejected[0].errors?.[0]?.code
      toast.error(code === 'file-too-large' ? 'File is larger than 20 MB.' : 'Please upload a JPG, PNG, WEBP, BMP or TIFF image. PDF reports go in the Report Summarizer.')
      return
    }
    if (!accepted.length) return
    setFile(accepted[0])
    setPreview(URL.createObjectURL(accepted[0]))
    setResult(null)
    setError(null)
    setDiag(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'] },
    maxSize: 20 * 1024 * 1024,
    maxFiles: 1,
  })

  const handleAnalyze = async () => {
    if (!file) { toast.error('Please upload an image first'); return }
    setLoading(true); setError(null); setDiag(null)
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('type', analysisType)
      form.append('language', language || 'en')
      const { data } = await imageAnalysisService.analyze(form)
      setResult(data)
    } catch (err) {
      const data = err.response?.data
      const detail = data?.detail
      const message = typeof detail === 'string'
        ? detail
        : Array.isArray(detail) ? 'The upload was not accepted. Please try a different image.'
        : err.code === 'ECONNABORTED' ? 'The analysis took too long. Please try again.'
        : err.response ? 'Analysis failed. Please try again.'
        : 'Could not reach the server. Check your connection and that the backend is running.'
      setError({ message, attempts: data?.attempts || [], status: err.response?.status })
    } finally {
      setLoading(false)
    }
  }

  const runDiagnostics = async () => {
    setDiagLoading(true)
    try {
      const { data } = await imageAnalysisService.diagnose()
      setDiag(data)
    } catch {
      toast.error('Diagnostics failed — is the backend running and are you logged in?')
    } finally {
      setDiagLoading(false)
    }
  }

  const reset = () => { setFile(null); setPreview(null); setResult(null); setError(null); setDiag(null) }

  const noVision = aiStatus && !aiStatus.vision_available
  const urgency = result && URGENCY[result.urgency]
  const conditions = asArray(result?.possible_conditions).map((c) => (typeof c === 'string' ? { name: c, likelihood: 'low' } : c))
  const unusable = result?.status === 'unusable_image'
  const qualityRating = result?.image_quality?.rating

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="section-title">AI Medical Image Analysis</h1>
          <p className="section-subtitle text-sm">Upload an X-ray, scan, skin photo, or report photo for an AI explanation in plain language</p>
        </div>
        {(result || error) && <button onClick={reset} className="btn-secondary text-sm px-4 py-2"><RotateCcw size={14} /> New Analysis</button>}
      </div>

      {noVision && (
        <div className="flex items-start gap-3 p-4 rounded-xl border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20">
          <AlertCircle size={18} className="text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">Image analysis is not set up yet</p>
            <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
              Add <code>ANTHROPIC_API_KEY</code>, <code>OPENAI_API_KEY</code> or <code>GROQ_API_KEY</code> to <code>backend/.env</code> and restart the backend.
              Groq has a free vision model.
            </p>
          </div>
        </div>
      )}

      {aiStatus?.vision_available && !result && !error && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 text-xs font-medium text-emerald-700 dark:text-emerald-400 w-fit">
          <Sparkles size={13} /> Real AI vision is active ({(aiStatus.vision_providers || []).join(' → ')})
        </div>
      )}

      {/* Error panel — shows WHY it failed instead of a fake result */}
      {error && !result && (
        <div className="p-5 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 space-y-3">
          <div className="flex items-start gap-3">
            <XCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-red-800 dark:text-red-300">Analysis could not be completed</p>
              <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error.message}</p>
              {error.attempts.length > 0 && (
                <ul className="mt-2 space-y-1 text-xs text-red-700 dark:text-red-400">
                  {error.attempts.map((a) => <li key={a.provider}><b className="capitalize">{a.provider}</b>: {a.reason}</li>)}
                </ul>
              )}
            </div>
          </div>
          {error.status === 503 && (
            <div className="flex flex-wrap items-center gap-3">
              <button onClick={runDiagnostics} disabled={diagLoading} className="btn-secondary text-xs px-3 py-1.5">
                {diagLoading ? <><Loader size={12} className="animate-spin" /> Testing…</> : <><Activity size={12} /> Test AI connection</>}
              </button>
              <button onClick={handleAnalyze} disabled={loading} className="btn-secondary text-xs px-3 py-1.5">Try again</button>
            </div>
          )}
          {diag && (
            <ul className="text-xs space-y-1">
              {diag.providers.length === 0 && <li className="text-red-700 dark:text-red-400">{diag.message}</li>}
              {diag.providers.map((p) => (
                <li key={p.provider} className={p.ok ? 'text-emerald-700 dark:text-emerald-400' : 'text-red-700 dark:text-red-400'}>
                  <b className="capitalize">{p.provider}</b>: {p.ok ? `working (${p.model}, ${p.latency_ms} ms)` : p.reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {!result ? (
        <div className="space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {analysisTypes.map(({ key, label, icon: Icon, desc }) => (
              <button key={key} onClick={() => setAnalysisType(key)}
                className={`p-4 rounded-xl text-left border transition-all ${
                  analysisType === key
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md'
                    : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-blue-300'}`}>
                <Icon size={20} className={analysisType === key ? 'text-blue-600' : 'text-slate-400'} />
                <p className={`font-semibold text-sm mt-2 ${analysisType === key ? 'text-blue-700 dark:text-blue-400' : 'text-slate-700 dark:text-slate-300'}`}>{label}</p>
                <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
              </button>
            ))}
          </div>

          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
              isDragActive ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/10' : 'border-slate-200 dark:border-slate-700 hover:border-blue-300 bg-white dark:bg-slate-800'}`}
          >
            <input {...getInputProps()} />
            {preview ? (
              <div className="flex flex-col items-center gap-3">
                <img src={preview} alt="Preview" className="max-h-56 rounded-xl object-contain shadow-md" />
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{file?.name}</p>
                <p className="text-xs text-slate-400">{(file?.size / 1024 / 1024).toFixed(2)} MB — click to change</p>
              </div>
            ) : (
              <>
                <Upload size={36} className="text-slate-400 mx-auto mb-3" />
                <p className="font-medium text-slate-600 dark:text-slate-400 mb-1">
                  {isDragActive ? 'Drop the image here' : 'Drag and drop an image, or click to select'}
                </p>
                <p className="text-xs text-slate-400">JPG, PNG, WEBP, BMP, TIFF — max 20 MB</p>
              </>
            )}
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <HelpCircle size={13} /> Have a PDF report? Use the <Link to="/report-summarizer" className="underline text-blue-600">Report Summarizer</Link>.
            For best results use a sharp, well-lit, complete image without filters.
          </p>

          <div className="flex items-center gap-3 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
            <AlertTriangle size={16} className="text-amber-600 flex-shrink-0" />
            <p className="text-xs text-amber-700 dark:text-amber-400">
              AI analysis is for information only and is not a medical diagnosis. Always consult a healthcare professional.
            </p>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={!file || loading || noVision}
            className="btn-primary w-full justify-center py-3.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center gap-2"><Loader size={16} className="animate-spin" /> Analyzing image… this can take up to a minute</span>
            ) : noVision ? (
              <span className="flex items-center gap-2"><AlertCircle size={16} /> Vision AI not configured</span>
            ) : <><Brain size={18} /> Analyze with AI</>}
          </button>
        </div>
      ) : (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
          {unusable ? (
            <div className="p-5 rounded-xl border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20">
              <div className="flex items-start gap-3">
                <AlertTriangle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-800 dark:text-amber-300">This image could not be analysed</p>
                  <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">{result.summary}</p>
                </div>
              </div>
            </div>
          ) : (
            <>
              {urgency && (
                <div className={`flex items-start gap-3 p-4 rounded-xl border ${urgency.cls}`}>
                  <urgency.icon size={18} className="flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold">{urgency.label}</p>
                    {result.urgency_reason && <p className="text-xs mt-0.5 opacity-90">{result.urgency_reason}</p>}
                  </div>
                </div>
              )}

              <div className="glass-card p-6">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div>
                    <h2 className="font-semibold text-slate-800 dark:text-slate-100 text-lg">Analysis Complete</h2>
                    {result.detected_type && <p className="text-xs text-slate-500 mt-0.5">Detected: {result.detected_type}</p>}
                    {qualityRating && (
                      <p className="text-xs text-slate-500 mt-0.5">
                        Image quality: <b className="capitalize">{qualityRating}</b>
                        {asArray(result.image_quality?.issues).length > 0 && ` — ${asArray(result.image_quality.issues).join(' ')}`}
                      </p>
                    )}
                  </div>
                  <div className="text-center flex-shrink-0">
                    <p className="text-2xl font-bold text-blue-600">{result.confidence ?? 0}%</p>
                    <p className="text-xs text-slate-500">AI Confidence</p>
                  </div>
                </div>
                <div className="w-full h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min(100, result.confidence ?? 0)}%` }}
                    transition={{ duration: 0.8 }} className="h-full rounded-full bg-gradient-to-r from-blue-500 to-teal-500" />
                </div>
                <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed mt-4">{result.summary}</p>
              </div>

              <div className="grid md:grid-cols-2 gap-5">
                <Section icon={Info} iconCls="text-blue-500" title="Key Findings">
                  {asArray(result.key_findings).length
                    ? <BulletList items={asArray(result.key_findings)} />
                    : <p className="text-sm text-slate-500">No specific findings were reported.</p>}
                </Section>
                <Section icon={Brain} iconCls="text-purple-500" title="Possible Conditions">
                  {conditions.length ? (
                    <ul className="space-y-3">
                      {conditions.map((c, i) => (
                        <li key={i} className="text-sm">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-slate-700 dark:text-slate-200">{c.name}</span>
                            <span className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded ${LIKELIHOOD_CLS[c.likelihood] || LIKELIHOOD_CLS.low}`}>{c.likelihood}</span>
                          </div>
                          {c.reasoning && <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{c.reasoning}</p>}
                        </li>
                      ))}
                    </ul>
                  ) : <p className="text-sm text-slate-500">Nothing specific to suggest from this image.</p>}
                </Section>
              </div>

              <Section icon={CheckCircle} iconCls="text-green-500" title="Recommendations">
                <BulletList items={asArray(result.recommendations)} />
              </Section>

              <div className="grid md:grid-cols-2 gap-5">
                {asArray(result.questions_for_doctor).length > 0 && (
                  <Section icon={HelpCircle} iconCls="text-teal-500" title="Questions to ask your doctor">
                    <BulletList items={asArray(result.questions_for_doctor)} iconCls="text-teal-500" />
                  </Section>
                )}
                {asArray(result.limitations).length > 0 && (
                  <Section icon={Info} iconCls="text-slate-400" title="What this AI cannot tell">
                    <BulletList items={asArray(result.limitations)} iconCls="text-slate-400" />
                  </Section>
                )}
              </div>
            </>
          )}

          <div className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
            <AlertTriangle size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-700 dark:text-amber-400">{result.disclaimer}</p>
          </div>
          {result.provider && (
            <p className="text-[11px] text-slate-400 text-right">
              Analysed by {result.provider} ({result.model}) in {((result.processing_ms || 0) / 1000).toFixed(1)}s
            </p>
          )}
        </motion.div>
      )}
    </div>
  )
}
