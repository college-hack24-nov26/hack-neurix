import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Video, MessageSquare, Clock, Star, X, CheckCircle, Calendar, User, DollarSign, Globe, Phone, Download, Upload } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { telemedicineService } from '../services/api'

const DOCTORS = [
  { id:1, name:'Dr. Priya Sharma', specialization:'General Physician', hospital:'Apollo Hospitals', experience:12, rating:4.9, fee:500, languages:['English','Hindi','Marathi'], status:'available', photo:'PS', color:'bg-blue-500',
    about:'MBBS, MD — General Medicine. Expert in preventive care, chronic disease management, and primary health consultations.', slots:['09:00 AM','10:00 AM','11:00 AM','02:00 PM','03:00 PM','04:00 PM'] },
  { id:2, name:'Dr. Rahul Mehta', specialization:'Cardiologist', hospital:'Fortis Hospital', experience:18, rating:4.8, fee:1200, languages:['English','Hindi','Gujarati'], status:'available', photo:'RM', color:'bg-red-500',
    about:'MBBS, MD (Medicine), DM (Cardiology). Specializes in interventional cardiology, heart failure, and preventive cardiology.', slots:['10:00 AM','11:00 AM','03:00 PM','04:00 PM'] },
  { id:3, name:'Dr. Anjali Nair', specialization:'Dermatologist', hospital:'Manipal Hospital', experience:9, rating:4.7, fee:800, languages:['English','Malayalam','Tamil'], status:'available', photo:'AN', color:'bg-pink-500',
    about:'MBBS, DVD, DNB (Dermatology). Expert in skin disorders, cosmetic dermatology, and hair & nail conditions.', slots:['09:30 AM','11:30 AM','02:30 PM','05:00 PM'] },
  { id:4, name:'Dr. Vikram Rajan', specialization:'Neurologist', hospital:'NIMHANS', experience:15, rating:4.9, fee:1500, languages:['English','Kannada','Tamil'], status:'busy', photo:'VR', color:'bg-purple-500',
    about:'MBBS, MD (Medicine), DM (Neurology). Specializes in epilepsy, stroke management, and movement disorders.', slots:['10:30 AM','02:00 PM'] },
  { id:5, name:'Dr. Fatima Khan', specialization:'Gynecologist', hospital:'Lilavati Hospital', experience:14, rating:4.8, fee:900, languages:['English','Hindi','Urdu'], status:'available', photo:'FK', color:'bg-green-500',
    about:'MBBS, MS (OBG). Expert in obstetrics, high-risk pregnancies, laparoscopic surgery, and women\'s health.', slots:['09:00 AM','10:30 AM','12:00 PM','03:30 PM'] },
  { id:6, name:'Dr. Suresh Patil', specialization:'Orthopedic Surgeon', hospital:'Kokilaben Hospital', experience:20, rating:4.7, fee:1100, languages:['English','Hindi','Marathi'], status:'available', photo:'SP', color:'bg-amber-500',
    about:'MBBS, MS (Ortho), MCh. Specializes in joint replacement, sports injuries, and spine surgery.', slots:['10:00 AM','11:30 AM','03:00 PM','04:30 PM'] },
  { id:7, name:'Dr. Meera Krishnan', specialization:'Pediatrician', hospital:'Rainbow Children\'s Hospital', experience:11, rating:4.9, fee:700, languages:['English','Tamil','Telugu'], status:'available', photo:'MK', color:'bg-teal-500',
    about:'MBBS, MD (Pediatrics). Expert in child development, vaccinations, and pediatric emergency care.', slots:['09:00 AM','10:00 AM','11:00 AM','12:00 PM','02:00 PM'] },
  { id:8, name:'Dr. Arun Gupta', specialization:'Psychiatrist', hospital:'NIMHANS', experience:13, rating:4.8, fee:1000, languages:['English','Hindi'], status:'offline', photo:'AG', color:'bg-indigo-500',
    about:'MBBS, MD (Psychiatry). Specializes in depression, anxiety, bipolar disorder, and schizophrenia.', slots:['11:00 AM','02:00 PM','04:00 PM'] },
]

const SPECIALTIES = ['All', 'General Physician', 'Cardiologist', 'Dermatologist', 'Neurologist', 'Gynecologist', 'Orthopedic Surgeon', 'Pediatrician', 'Psychiatrist']

const statusConfig = {
  available: { label: 'Available', color: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400' },
  busy:      { label: 'Busy',      color: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-400' },
  offline:   { label: 'Offline',   color: 'text-slate-500 bg-slate-100 dark:bg-slate-700 dark:text-slate-400' },
}

function BookingModal({ doctor, onClose }) {
  const [step, setStep] = useState(1)
  const [slot, setSlot] = useState('')
  const [type, setType] = useState('video')
  const [reason, setReason] = useState('')
  const [booked, setBooked] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const confirm = async () => {
    if (!slot) { toast.error('Please select a time slot'); return }
    setSubmitting(true)
    try {
      await telemedicineService.book({
        doctor_id: doctor.id,
        slot,
        consult_type: type,
        reason,
      })
      setBooked(true)
      setTimeout(() => { onClose(); toast.success(`Consultation booked with ${doctor.name} at ${slot}`) }, 1200)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not book consultation')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-700">
          <h3 className="font-bold text-slate-800 dark:text-slate-100">Book Consultation</h3>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {booked ? (
            <div className="text-center py-6">
              <CheckCircle size={52} className="text-green-500 mx-auto mb-3" />
              <p className="font-bold text-slate-800 dark:text-slate-100">Consultation Booked!</p>
              <p className="text-slate-400 text-sm mt-1">{doctor.name} · {slot}</p>
            </div>
          ) : (
            <>
              {/* Doctor info */}
              <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
                <div className={`w-12 h-12 rounded-xl ${doctor.color} flex items-center justify-center text-white font-bold text-lg flex-shrink-0`}>
                  {doctor.photo}
                </div>
                <div>
                  <p className="font-semibold text-slate-800 dark:text-slate-100 text-sm">{doctor.name}</p>
                  <p className="text-xs text-slate-400">{doctor.specialization} · {doctor.hospital}</p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 font-medium mt-0.5">Fee: ₹{doctor.fee}</p>
                </div>
              </div>

              {/* Consultation type */}
              <div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Consultation Type</p>
                <div className="grid grid-cols-2 gap-2">
                  {[['video','Video Call',Video],['chat','Chat',MessageSquare]].map(([val,label,Icon])=>(
                    <button key={val} onClick={()=>setType(val)}
                      className={`flex items-center gap-2 p-3 rounded-xl border text-sm font-medium transition-all ${type===val?'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300':'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'}`}>
                      <Icon size={16} /> {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Time slots */}
              <div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Select Time Slot</p>
                <div className="grid grid-cols-3 gap-2">
                  {doctor.slots.map(s => (
                    <button key={s} onClick={() => setSlot(s)}
                      className={`py-2 px-1 rounded-lg border text-xs font-medium transition-all ${slot===s?'border-blue-500 bg-blue-600 text-white':'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-blue-300'}`}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Reason */}
              <div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Reason for Visit</p>
                <textarea value={reason} onChange={e=>setReason(e.target.value)}
                  placeholder="Briefly describe your symptoms or concern..."
                  rows={2} className="input-field resize-none text-sm" />
              </div>

              <button onClick={confirm} disabled={submitting}
                className="btn-primary w-full justify-center py-3 disabled:opacity-60 disabled:cursor-not-allowed">
                <CheckCircle size={16} /> {submitting ? 'Booking...' : `Confirm Booking · ₹${doctor.fee}`}
              </button>
            </>
          )}
        </div>
      </motion.div>
    </div>
  )
}

export default function Telemedicine() {
  const { t } = useTranslation()
  const [specialty, setSpecialty] = useState('All')
  const [search, setSearch] = useState('')
  const [bookingDoctor, setBookingDoctor] = useState(null)
  const [activeTab, setActiveTab] = useState('doctors')
  const [consultations, setConsultations] = useState([])

  const loadConsultations = async () => {
    try {
      const response = await telemedicineService.getConsultations()
      setConsultations(response.data.consultations || [])
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not load consultations')
    }
  }

  useEffect(() => {
    if (activeTab === 'consultations') loadConsultations()
  }, [activeTab])

  const uploadPrescription = async (bookingId, file) => {
    if (!file) return
    if (file.type !== 'application/pdf') {
      toast.error('Only PDF prescriptions are allowed')
      return
    }
    try {
      await telemedicineService.uploadPrescription(bookingId, file)
      toast.success('Prescription PDF uploaded')
      await loadConsultations()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Prescription upload failed')
    }
  }

  const downloadPrescription = async (bookingId, title) => {
    try {
      const response = await telemedicineService.downloadPrescription(bookingId)
      const url = URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = title || 'prescription.pdf'
      link.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not download prescription')
    }
  }

  const filtered = DOCTORS.filter(d => {
    const matchSpec = specialty === 'All' || d.specialization === specialty
    const matchSearch = !search || d.name.toLowerCase().includes(search.toLowerCase()) || d.specialization.toLowerCase().includes(search.toLowerCase())
    return matchSpec && matchSearch
  })

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{t('telemedicine.title', 'Telemedicine')}</h1>
        <p className="text-slate-500 text-sm mt-1">{t('telemedicine.subtitle', 'Consult qualified doctors online — secure, fast, convenient')}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[['50+','Verified Doctors'],['24/7','Available'],['₹500','Starting Fee'],['4.8','Average Rating']].map(([val, label]) => (
          <div key={label} className="glass-card p-4 text-center">
            <p className="text-xl font-bold text-blue-600">{val}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Tab switcher */}
      <div className="flex gap-2">
        {[['doctors','Find Doctors'],['consultations','My Consultations'],['howItWorks','How It Works']].map(([key,label]) => (
          <button key={key} onClick={() => setActiveTab(key)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeTab===key?'bg-blue-600 text-white':'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'}`}>
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'doctors' && (
        <>
          {/* Filters */}
          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <User size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input value={search} onChange={e=>setSearch(e.target.value)}
                placeholder="Search doctors by name or specialty..."
                className="input-field pl-10" />
            </div>
            <select value={specialty} onChange={e=>setSpecialty(e.target.value)} className="input-field md:w-56">
              {SPECIALTIES.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>

          {/* Doctor cards */}
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
            {filtered.map((doc, i) => {
              const sc = statusConfig[doc.status]
              return (
                <motion.div key={doc.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className="glass-card p-5 hover:shadow-card-hover transition-all">
                  {/* Header */}
                  <div className="flex items-start gap-3 mb-4">
                    <div className={`w-14 h-14 rounded-2xl ${doc.color} flex items-center justify-center text-white font-bold text-xl flex-shrink-0`}>
                      {doc.photo}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-slate-800 dark:text-slate-100 text-sm leading-tight">{doc.name}</p>
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">{doc.specialization}</p>
                      <p className="text-xs text-slate-400 truncate">{doc.hospital}</p>
                    </div>
                    <span className={`text-xs font-medium px-2.5 py-1 rounded-full flex-shrink-0 ${sc.color}`}>
                      {sc.label}
                    </span>
                  </div>

                  {/* About */}
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4 line-clamp-2">{doc.about}</p>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-2 mb-4">
                    <div className="text-center p-2 bg-slate-50 dark:bg-slate-800 rounded-xl">
                      <p className="text-sm font-bold text-slate-800 dark:text-slate-100">{doc.experience}y</p>
                      <p className="text-xs text-slate-400">Exp.</p>
                    </div>
                    <div className="text-center p-2 bg-slate-50 dark:bg-slate-800 rounded-xl">
                      <p className="text-sm font-bold text-yellow-500 flex items-center justify-center gap-0.5">
                        <Star size={11} className="fill-yellow-400" />{doc.rating}
                      </p>
                      <p className="text-xs text-slate-400">Rating</p>
                    </div>
                    <div className="text-center p-2 bg-slate-50 dark:bg-slate-800 rounded-xl">
                      <p className="text-sm font-bold text-slate-800 dark:text-slate-100">₹{doc.fee}</p>
                      <p className="text-xs text-slate-400">Fee</p>
                    </div>
                  </div>

                  {/* Languages */}
                  <div className="flex gap-1 flex-wrap mb-4">
                    {doc.languages.map(l => (
                      <span key={l} className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 rounded text-xs">{l}</span>
                    ))}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => doc.status !== 'offline' ? setBookingDoctor(doc) : toast.error('Doctor is currently offline')}
                      disabled={doc.status === 'offline'}
                      className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                        doc.status === 'offline'
                          ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}>
                      <Video size={15} />
                      {t('telemedicine.bookConsultation', 'Book Consultation')}
                    </button>
                    <button
                      onClick={() => doc.status !== 'offline' ? setBookingDoctor(doc) : toast.error('Doctor is offline')}
                      className="p-2.5 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-500 hover:text-blue-500 hover:border-blue-300 transition-all">
                      <MessageSquare size={15} />
                    </button>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </>
      )}

      {activeTab === 'consultations' && (
        <div className="space-y-4">
          {!consultations.length && (
            <div className="glass-card p-10 text-center text-slate-500">
              No consultations booked yet.
            </div>
          )}
          {consultations.map((consultation) => (
            <div key={consultation.booking_id} className="glass-card p-5">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <p className="font-bold text-slate-800 dark:text-slate-100">{consultation.doctor}</p>
                  <p className="text-sm text-blue-600">{consultation.specialization}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {consultation.slot} · {consultation.type} · {consultation.status}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {consultation.prescription ? (
                    <button
                      onClick={() => downloadPrescription(
                        consultation.booking_id,
                        consultation.prescription.title,
                      )}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium">
                      <Download size={15} /> Download Prescription
                    </button>
                  ) : (
                    <span className="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 text-xs">
                      Prescription pending
                    </span>
                  )}
                  <label className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-sm font-medium cursor-pointer">
                    <Upload size={15} /> {consultation.prescription ? 'Replace PDF' : 'Upload PDF (Doctor)'}
                    <input
                      type="file"
                      accept=".pdf,application/pdf"
                      className="hidden"
                      onChange={(event) => uploadPrescription(
                        consultation.booking_id,
                        event.target.files?.[0],
                      )}
                    />
                  </label>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'howItWorks' && (
        <div className="space-y-4">
          <div className="grid md:grid-cols-3 gap-5">
            {[
              { step:'01', icon:User,          title:'Choose a Doctor',     desc:'Browse verified specialists by specialty, language, and availability. Read profiles and ratings.' },
              { step:'02', icon:Calendar,      title:'Book a Slot',         desc:'Select a convenient time slot and consultation type — video call or text chat.' },
              { step:'03', icon:Video,         title:'Start Consultation',  desc:'Join your consultation at the scheduled time. Share reports, ask questions, get prescriptions.' },
            ].map(({step,icon:Icon,title,desc}) => (
              <div key={step} className="glass-card p-6 text-center">
                <div className="w-12 h-12 rounded-2xl bg-blue-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">{step}</div>
                <Icon size={24} className="text-blue-500 mx-auto mb-3" />
                <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">{title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          <div className="glass-card p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Use AI Assistant for instant guidance</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">Get 24/7 AI-powered health guidance while waiting for your doctor consultation.</p>
            <Link to="/chat" className="btn-primary inline-flex"><MessageSquare size={16} /> Open AI Assistant</Link>
          </div>
        </div>
      )}

      {bookingDoctor && (
        <BookingModal doctor={bookingDoctor} onClose={() => setBookingDoctor(null)} />
      )}
    </div>
  )
}
