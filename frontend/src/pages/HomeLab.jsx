import React, { useEffect, useState } from 'react'
import { Calendar, CheckCircle, Download, FlaskConical, Search, Star, Upload } from 'lucide-react'
import toast from 'react-hot-toast'
import { laboratoryService } from '../services/api'

const toLocalDateTimeValue = (date) => {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

export default function HomeLab() {
  const [tab, setTab] = useState('book')
  const [labs, setLabs] = useState([])
  const [bookings, setBookings] = useState([])
  const [reports, setReports] = useState([])
  const [selectedLab, setSelectedLab] = useState(null)
  const [testIds, setTestIds] = useState([])
  const [areaName, setAreaName] = useState('')
  const [form, setForm] = useState({
    patient_name: '', patient_phone: '', address: '', pincode: '400001',
    landmark: '', preferred_at: '', special_instructions: '',
  })
  const [loading, setLoading] = useState(false)

  const refresh = async () => {
    try {
      const [catalogue, bookingRes, reportRes] = await Promise.all([
        areaName.trim()
          ? laboratoryService.getNearby(areaName.trim())
          : Promise.resolve({ data: { laboratories: [] } }),
        laboratoryService.getBookings(),
        laboratoryService.getReports(),
      ])
      setLabs(catalogue.data.laboratories || [])
      setBookings(bookingRes.data.bookings || [])
      setReports(reportRes.data.reports || [])
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not load Laboratory data')
    }
  }

  useEffect(() => { refresh() }, [])

  const toggleTest = (id) => setTestIds((current) =>
    current.includes(id) ? current.filter((value) => value !== id) : [...current, id]
  )

  const submitBooking = async (event) => {
    event.preventDefault()
    if (!selectedLab || !testIds.length || !form.patient_name || !form.patient_phone || !form.address || !form.preferred_at) {
      toast.error('Complete the booking details and select at least one test')
      return
    }
    const preferredTime = new Date(form.preferred_at)
    if (Number.isNaN(preferredTime.getTime())) {
      toast.error('Select a valid collection date and time')
      return
    }
    if (preferredTime.getTime() < Date.now() + 30 * 60 * 1000) {
      toast.error('Preferred collection time must be at least 30 minutes in the future')
      return
    }
    setLoading(true)
    try {
      await laboratoryService.book({
        ...form,
        laboratory_id: selectedLab.id,
        test_ids: testIds,
        preferred_at: new Date(form.preferred_at).toISOString(),
      })
      toast.success('Laboratory booking submitted')
      setSelectedLab(null)
      setTestIds([])
      await refresh()
      setTab('bookings')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Booking failed')
    } finally {
      setLoading(false)
    }
  }

  const uploadReport = async (bookingId, file) => {
    if (!file) return
    try {
      await laboratoryService.uploadReport(bookingId, file)
      toast.success('Report uploaded securely')
      await refresh()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Report upload failed')
    }
  }

  const downloadReport = async (report) => {
    try {
      const response = await laboratoryService.downloadReport(report.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = report.title
      link.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      toast.error('Could not download report')
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-blue-600"><FlaskConical size={22} /><span className="text-sm font-bold uppercase tracking-wider">Diagnostics</span></div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">Laboratory</h1>
          <p className="text-sm text-slate-500 mt-1">Book verified lab tests for home sample collection.</p>
        </div>
        <div className="flex rounded-xl border border-slate-200 dark:border-slate-700 p-1 bg-white dark:bg-slate-900">
          {[['book', 'Book Tests'], ['bookings', 'My Bookings'], ['reports', 'Reports']].map(([value, label]) =>
            <button key={value} onClick={() => setTab(value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === value ? 'bg-blue-600 text-white' : 'text-slate-500'}`}>{label}</button>
          )}
        </div>
      </div>

      {tab === 'book' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1 max-w-xs">
              <Search size={16} className="absolute left-3 top-3 text-slate-400" />
              <input value={areaName} onChange={(e) => setAreaName(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') refresh() }}
                className="w-full pl-9 pr-3 py-2.5 border rounded-xl bg-white dark:bg-slate-900 dark:border-slate-700 text-sm"
                placeholder="Enter your area, city or pincode" />
            </div>
            <button onClick={refresh} className="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm">Search</button>
          </div>
          {labs.map((lab) => (
            <div key={lab.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-bold text-slate-900 dark:text-white">{lab.name}</h2>
                    {lab.verification_status === 'verified' && <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-1 rounded-full">Verified</span>}
                  </div>
                  <p className="text-sm text-slate-500 mt-1">{lab.address}, {lab.city}</p>
                  <p className="text-xs text-slate-400 mt-2 flex items-center gap-1"><Star size={12} className="text-amber-500 fill-amber-500" /> {lab.rating}</p>
                </div>
                <button onClick={() => { setSelectedLab(lab); setTestIds([]); setForm((current) => ({ ...current, preferred_at: '' })) }}
                  className="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium">Choose Tests</button>
              </div>
            </div>
          ))}
          {!labs.length && (
            <div className="text-center py-16 text-slate-500">
              {areaName.trim() ? 'No verified laboratories found in this area.' : 'Enter your area name to find nearby laboratories.'}
            </div>
          )}
        </div>
      )}

      {selectedLab && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <form onSubmit={submitBooking} className="bg-white dark:bg-slate-900 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-5">
            <div className="flex justify-between items-center"><h2 className="text-lg font-bold">Book {selectedLab.name}</h2><button type="button" onClick={() => setSelectedLab(null)}>Close</button></div>
            <div className="grid sm:grid-cols-2 gap-3">
              {selectedLab.tests.map((test) => (
                <label key={test.id} className={`border rounded-xl p-3 cursor-pointer ${testIds.includes(test.id) ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-slate-200 dark:border-slate-700'}`}>
                  <input type="checkbox" className="mr-2" checked={testIds.includes(test.id)} onChange={() => toggleTest(test.id)} />
                  <span className="font-medium text-sm">{test.name}</span>
                  <span className="float-right text-blue-600 font-bold text-sm">₹{test.price}</span>
                  <span className="block text-xs text-slate-400 mt-1 ml-5">{test.sample_type} · {test.turnaround_hours}h</span>
                </label>
              ))}
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              {[
                ['patient_name', 'Patient name'], ['patient_phone', 'Phone number'],
                ['address', 'Collection address'], ['landmark', 'Landmark'],
              ].map(([key, label]) => (
                <input key={key} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  placeholder={label} className="border rounded-xl px-3 py-2.5 dark:bg-slate-800 dark:border-slate-700 text-sm" />
              ))}
              <input type="datetime-local"
                value={form.preferred_at}
                min={toLocalDateTimeValue(new Date(Date.now() + 30 * 60 * 1000))}
                onChange={(e) => setForm({ ...form, preferred_at: e.target.value })}
                className="border rounded-xl px-3 py-2.5 dark:bg-slate-800 dark:border-slate-700 text-sm" />
            </div>
            <button disabled={loading} className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold disabled:opacity-60">
              {loading ? 'Submitting...' : 'Confirm Home Collection'}
            </button>
          </form>
        </div>
      )}

      {tab === 'bookings' && (
        <div className="space-y-3">
          {bookings.map((booking) => (
            <div key={booking.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
              <div className="flex justify-between gap-4">
                <div><p className="text-xs text-slate-400">{booking.booking_ref}</p><h3 className="font-bold mt-1">{booking.laboratory}</h3><p className="text-sm text-slate-500 mt-1"><Calendar size={14} className="inline mr-1" />{new Date(booking.preferred_at).toLocaleString()}</p></div>
                <span className="h-fit px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700">{booking.status.replaceAll('_', ' ')}</span>
              </div>
              <label className="inline-flex items-center gap-2 mt-4 text-sm text-blue-600 cursor-pointer">
                <Upload size={16} /> Upload report
                <input type="file" accept=".pdf,image/jpeg,image/png" className="hidden" onChange={(e) => uploadReport(booking.id, e.target.files[0])} />
              </label>
            </div>
          ))}
          {!bookings.length && <div className="text-center py-16 text-slate-500">No Laboratory bookings yet.</div>}
        </div>
      )}

      {tab === 'reports' && (
        <div className="grid sm:grid-cols-2 gap-4">
          {reports.map((report) => (
            <div key={report.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
              <CheckCircle size={20} className="text-emerald-500 mb-2" /><h3 className="font-bold text-sm">{report.title}</h3>
              <p className="text-xs text-slate-400 mt-1">{new Date(report.uploaded_at).toLocaleString()}</p>
              <button onClick={() => downloadReport(report)} className="mt-4 flex items-center gap-2 text-sm font-medium text-blue-600"><Download size={16} /> Download secure report</button>
            </div>
          ))}
          {!reports.length && <div className="col-span-full text-center py-16 text-slate-500">No reports available.</div>}
        </div>
      )}
    </div>
  )
}
