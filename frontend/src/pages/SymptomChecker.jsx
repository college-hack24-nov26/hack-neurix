import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Plus, X, ChevronRight, AlertTriangle, CheckCircle, Info, ArrowRight, RotateCcw, Sparkles } from 'lucide-react'
import { symptomService } from '../services/api'
import { useThemeStore } from '../store/themeStore'
import toast from 'react-hot-toast'

const commonSymptoms = [
  'Fever', 'Headache', 'Cough', 'Fatigue', 'Nausea', 'Vomiting',
  'Chest Pain', 'Shortness of Breath', 'Dizziness', 'Sore Throat',
  'Body Aches', 'Runny Nose', 'Diarrhea', 'Abdominal Pain', 'Back Pain',
  'Joint Pain', 'Skin Rash', 'Loss of Appetite', 'Chills', 'Sweating',
  'Swelling', 'Numbness', 'Blurred Vision', 'Ear Pain', 'Toothache',
]

const severityColor = (s) => {
  if (s >= 70) return { bar: 'bg-red-500',    badge: 'badge-danger',   label: 'High Risk' }
  if (s >= 40) return { bar: 'bg-yellow-500', badge: 'badge-warning',  label: 'Moderate' }
  return             { bar: 'bg-green-500',   badge: 'badge-success',  label: 'Low Risk' }
}

export default function SymptomChecker() {
  const { language } = useThemeStore()
  const [step, setStep] = useState(1)           // 1: select, 2: follow-up, 3: results
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState([])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [followUpAnswers, setFollowUpAnswers] = useState({})
  // Full symptom catalogue from the database (~960 entries) powers the search box;
  // the quick-pick chips below stay as the built-in common list if the request fails.
  const [catalogue, setCatalogue] = useState([])
  useEffect(() => {
    symptomService.getSymptoms()
      .then((res) => setCatalogue((res.data?.symptoms || []).map((s) => s.name)))
      .catch(() => {})
  }, [])
  const [followUpQuestions] = useState([
    { id: 'duration',  question: 'How long have you had these symptoms?',
      options: ['Less than 24 hours', '1–3 days', '4–7 days', 'More than a week'] },
    { id: 'severity',  question: 'How severe are your symptoms?',
      options: ['Mild — slightly uncomfortable', 'Moderate — affects daily activities', 'Severe — very uncomfortable', 'Critical — need immediate help'] },
    { id: 'age_group', question: 'What is your age group?',
      options: ['Under 18', '18–35', '36–60', 'Over 60'] },
    { id: 'chronic',   question: 'Do you have any chronic conditions?',
      options: ['None', 'Diabetes', 'Hypertension', 'Heart disease', 'Other'] },
  ])

  const searchPool = catalogue.length ? catalogue : commonSymptoms
  const q = query.trim().toLowerCase()
  const selectedLower = selected.map((x) => x.toLowerCase())
  // names starting with the query first, then names that merely contain it
  const filtered = [
    ...searchPool.filter((s) => s.toLowerCase().startsWith(q)),
    ...searchPool.filter((s) => !s.toLowerCase().startsWith(q) && s.toLowerCase().includes(q)),
  ].filter((s) => !selectedLower.includes(s.toLowerCase()))

  const addSymptom = (s) => {
    if (selected.length >= 10) { toast.error('Maximum 10 symptoms at once'); return }
    setSelected([...selected, s])
    setQuery('')
  }

  const removeSymptom = (s) => setSelected(selected.filter((x) => x !== s))

  const handleAnalyze = async () => {
    if (selected.length === 0) { toast.error('Please select at least one symptom'); return }
    if (Object.keys(followUpAnswers).length < followUpQuestions.length) {
      toast.error('Please answer all follow-up questions')
      return
    }
    setLoading(true)
    try {
      const { data } = await symptomService.analyze({
        symptoms: selected,
        follow_up: followUpAnswers,
        language,
      })
      setResults(data)
      setStep(3)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setStep(1)
    setSelected([])
    setResults(null)
    setFollowUpAnswers({})
    setQuery('')
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="section-title">AI Symptom Checker</h1>
          <p className="section-subtitle text-sm">Describe your symptoms for AI-powered health insights</p>
        </div>
        {step > 1 && (
          <button onClick={reset} className="btn-secondary text-sm px-4 py-2">
            <RotateCcw size={15} /> Start Over
          </button>
        )}
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-3">
        {['Select Symptoms', 'Follow-up Questions', 'Results'].map((label, i) => (
          <React.Fragment key={label}>
            <div className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                step > i + 1 ? 'bg-green-500 text-white' :
                step === i + 1 ? 'bg-blue-600 text-white' :
                'bg-slate-200 dark:bg-slate-700 text-slate-500'
              }`}>
                {step > i + 1 ? <CheckCircle size={14} /> : i + 1}
              </div>
              <span className={`text-sm font-medium hidden sm:block ${step === i + 1 ? 'text-blue-600' : 'text-slate-400'}`}>{label}</span>
            </div>
            {i < 2 && <div className={`flex-1 h-0.5 ${step > i + 1 ? 'bg-green-500' : 'bg-slate-200 dark:bg-slate-700'}`} />}
          </React.Fragment>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* STEP 1 — Select Symptoms */}
        {step === 1 && (
          <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
            className="space-y-6">
            <div className="glass-card p-6">
              <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">What symptoms are you experiencing?</h2>

              {/* Search input */}
              <div className="relative mb-4">
                <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && query.trim()) addSymptom(query.trim()) }}
                  placeholder="Type a symptom and press Enter, or select below..."
                  className="input-field pl-10"
                />
              </div>

              {/* Selected symptoms */}
              {selected.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                  {selected.map((s) => (
                    <span key={s} className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium">
                      {s}
                      <button onClick={() => removeSymptom(s)} className="hover:text-blue-200">
                        <X size={13} />
                      </button>
                    </span>
                  ))}
                </div>
              )}

              {/* Common symptom chips */}
              <div>
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">Common Symptoms</p>
                <div className="flex flex-wrap gap-2">
                  {(query ? filtered : commonSymptoms.filter((s) => !selected.includes(s))).slice(0, 20).map((s) => (
                    <button key={s} onClick={() => addSymptom(s)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-600 dark:text-slate-400 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all">
                      <Plus size={12} /> {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => { if (selected.length === 0) { toast.error('Select at least one symptom'); return } setStep(2) }}
                className="btn-primary"
              >
                Continue <ChevronRight size={16} />
              </button>
            </div>
          </motion.div>
        )}

        {/* STEP 2 — Follow-up Questions */}
        {step === 2 && (
          <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
            className="space-y-6">
            <div className="glass-card p-6 space-y-6">
              <h2 className="font-semibold text-slate-800 dark:text-slate-100">Help us understand better</h2>
              {followUpQuestions.map(({ id, question, options }) => (
                <div key={id}>
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">{question}</p>
                  <div className="grid grid-cols-2 gap-2">
                    {options.map((opt) => (
                      <button key={opt} onClick={() => setFollowUpAnswers({ ...followUpAnswers, [id]: opt })}
                        className={`p-3 rounded-xl text-sm font-medium text-left border transition-all ${
                          followUpAnswers[id] === opt
                            ? 'bg-blue-600 text-white border-blue-600 shadow-md'
                            : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-blue-300'
                        }`}>
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3 justify-end">
              <button onClick={() => setStep(1)} className="btn-secondary">Back</button>
              <button onClick={handleAnalyze} disabled={loading} className="btn-primary">
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z"/>
                    </svg>
                    <span>Analyzing...</span>
                  </span>
                ) : <><span>Analyze Symptoms</span> <ArrowRight size={16} /></>}
              </button>
            </div>
          </motion.div>
        )}

        {/* STEP 3 — Results */}
        {step === 3 && results && (
          <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
            className="space-y-6">
            {/* Analyzed symptoms summary */}
            <div className="glass-card p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">Analyzed Symptoms</p>
                {results.ai_powered ? (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 rounded-full text-xs font-semibold">
                    <Sparkles size={12} /> AI-Powered Analysis
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded-full text-xs font-medium">
                    Offline Analysis
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {results.analyzed_symptoms.map((s) => (
                  <span key={s} className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-lg text-sm font-medium">{s}</span>
                ))}
              </div>
            </div>

            {/* Disease results */}
            <div className="space-y-4">
              <h2 className="font-semibold text-slate-800 dark:text-slate-100 text-lg">Possible Conditions</h2>
              {results.possible_diseases.map((disease, i) => {
                const sc = severityColor(disease.severity)
                return (
                  <motion.div key={disease.name}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="glass-card p-6"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                      <div className="flex items-center gap-3">
                        {i === 0 && <span className="badge-warning text-xs">Most Likely</span>}
                        <h3 className="font-semibold text-slate-800 dark:text-slate-100 text-lg">{disease.name}</h3>
                        <span className="text-xs text-slate-400 font-mono">{disease.icd_code}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-center">
                          <p className="text-2xl font-bold text-blue-600">{disease.probability}%</p>
                          <p className="text-xs text-slate-500">Probability</p>
                        </div>
                        <span className={sc.badge}>{sc.label}</span>
                      </div>
                    </div>

                    {/* Probability bar */}
                    <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-2 mb-4">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${disease.probability}%` }}
                        transition={{ duration: 0.8, delay: i * 0.1 + 0.2 }}
                        className={`h-2 rounded-full ${sc.bar}`}
                      />
                    </div>

                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{disease.description}</p>

                    <div className="grid md:grid-cols-3 gap-4 mb-4">
                      {disease.precautions?.length > 0 && (
                        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                          <p className="text-xs font-semibold text-blue-700 dark:text-blue-400 uppercase tracking-wider mb-2">Precautions</p>
                          <ul className="space-y-1">
                            {disease.precautions.slice(0,4).map((item) => (
                              <li key={item} className="flex items-start gap-1.5 text-xs text-slate-600 dark:text-slate-400">
                                <CheckCircle size={11} className="text-blue-500 flex-shrink-0 mt-0.5" />{item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {disease.home_remedies?.length > 0 && (
                        <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-xl">
                          <p className="text-xs font-semibold text-green-700 dark:text-green-400 uppercase tracking-wider mb-2">Home Remedies</p>
                          <ul className="space-y-1">
                            {disease.home_remedies.slice(0,4).map((item) => (
                              <li key={item} className="flex items-start gap-1.5 text-xs text-slate-600 dark:text-slate-400">
                                <CheckCircle size={11} className="text-green-500 flex-shrink-0 mt-0.5" />{item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {disease.medications?.length > 0 && (
                        <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
                          <p className="text-xs font-semibold text-purple-700 dark:text-purple-400 uppercase tracking-wider mb-2">Medications</p>
                          <ul className="space-y-1">
                            {disease.medications.slice(0,4).map((item) => (
                              <li key={item} className="flex items-start gap-1.5 text-xs text-slate-600 dark:text-slate-400">
                                <CheckCircle size={11} className="text-purple-500 flex-shrink-0 mt-0.5" />{item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
                      <p className="text-xs text-slate-500">
                        Recommended specialist: <span className="font-semibold text-blue-600">{disease.specialist}</span>
                      </p>
                      <span className="text-xs px-2.5 py-1 bg-slate-100 dark:bg-slate-700 rounded-lg text-slate-500 font-medium">
                        {disease.severity_level || 'Moderate'}
                      </span>
                    </div>
                  </motion.div>
                )
              })}
            </div>

            {/* Disclaimer */}
            <div className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
              <AlertTriangle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-amber-800 dark:text-amber-300">{results.disclaimer}</p>
            </div>

            <div className="flex gap-3">
              <button onClick={reset} className="btn-secondary">
                <RotateCcw size={15} /> New Check
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function MapPin({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
    </svg>
  )
}
