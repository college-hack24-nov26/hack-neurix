import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Shield, Plus, Trash2, FileText } from 'lucide-react'
import { insuranceService } from '../services/api'
import toast from 'react-hot-toast'

export default function Insurance() {
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ provider: '', policyNumber: '', type: 'Individual', coverage: '', premium: '', renewalDate: '' })

  const loadPolicies = async () => {
    try {
      const { data } = await insuranceService.getAll()
      setPolicies(data.policies || [])
    } catch { toast.error('Failed to load policies.') }
    finally { setLoading(false) }
  }

  useEffect(() => { loadPolicies() }, [])

  const handleAdd = async () => {
    if (!form.provider || !form.policyNumber) { toast.error('Fill in required fields'); return }
    setSaving(true)
    try {
      const { data } = await insuranceService.add(form)
      setPolicies([data, ...policies])
      setShowAdd(false)
      setForm({ provider: '', policyNumber: '', type: 'Individual', coverage: '', premium: '', renewalDate: '' })
      toast.success('Insurance policy added!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add policy.')
    } finally { setSaving(false) }
  }

  const handleDelete = async (id) => {
    try {
      await insuranceService.delete(id)
      setPolicies(policies.filter((x) => x.id !== id))
      toast.success('Policy removed.')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Delete failed.')
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Insurance Management</h1>
          <p className="text-slate-500 text-sm mt-1">Store and manage your health insurance policies</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-primary text-sm px-4 py-2.5"><Plus size={15} /> Add Policy</button>
      </div>

      {showAdd && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Add Insurance Policy</h2>
          <div className="grid grid-cols-2 gap-4 mb-4">
            {[['provider', 'Insurance Provider'], ['policyNumber', 'Policy Number'], ['coverage', 'Coverage Amount'], ['premium', 'Annual Premium'], ['renewalDate', 'Renewal Date', 'date']].map(([key, label, type = 'text']) => (
              <div key={key}>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{label}</label>
                <input type={type} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} className="input-field" />
              </div>
            ))}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Policy Type</label>
              <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className="input-field">
                {['Individual', 'Family Floater', 'Group', 'Critical Illness', 'Senior Citizen'].map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={handleAdd} disabled={saving} className="btn-primary">{saving ? 'Saving...' : 'Save Policy'}</button>
            <button onClick={() => setShowAdd(false)} className="btn-secondary">Cancel</button>
          </div>
        </motion.div>
      )}

      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : (
        <div className="space-y-4">
          {policies.length === 0 && (
            <div className="text-center py-12 text-slate-400">No insurance policies added yet.</div>
          )}
          {policies.map((p) => (
            <motion.div key={p.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
                    <Shield size={22} className="text-blue-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-800 dark:text-slate-100">{p.provider}</p>
                    <p className="text-xs text-slate-400 font-mono">{p.policyNumber}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="badge-success">{p.status}</span>
                  <button className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors" onClick={() => handleDelete(p.id)}>
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
                {[['Type', p.type], ['Coverage', p.coverage], ['Premium', p.premium], ['Renews', p.renewalDate]].map(([label, value]) => (
                  <div key={label}>
                    <p className="text-xs text-slate-400">{label}</p>
                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mt-0.5">{value || '—'}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <div className="glass-card p-5">
        <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-3">Claims Guidance</h2>
        <div className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
          {['Keep all original bills and discharge summaries', 'Notify insurer within 24 hours of hospitalization for cashless claims', 'Pre-authorization is required for planned hospitalizations', 'Submit reimbursement claims within 30 days of discharge', 'Keep digital copies of all medical records and prescriptions'].map((tip) => (
            <div key={tip} className="flex items-start gap-2"><FileText size={13} className="text-blue-500 flex-shrink-0 mt-0.5" /> {tip}</div>
          ))}
        </div>
      </div>
    </div>
  )
}
