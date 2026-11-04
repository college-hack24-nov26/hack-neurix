import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ChevronRight, Search } from 'lucide-react'

const organs = [
  { id: 'brain', name: 'Brain & Nervous System', icon: '🧠', color: 'from-purple-500 to-purple-600', diseases: ['Migraine', 'Epilepsy', 'Alzheimer\'s Disease', 'Parkinson\'s Disease', 'Stroke', 'Multiple Sclerosis', 'Meningitis', 'Brain Tumor'], specialist: 'Neurologist', count: 45 },
  { id: 'heart', name: 'Heart & Cardiovascular', icon: '❤️', color: 'from-red-500 to-red-600', diseases: ['Hypertension', 'Coronary Artery Disease', 'Heart Failure', 'Arrhythmia', 'Myocardial Infarction', 'Peripheral Artery Disease', 'Cardiomyopathy'], specialist: 'Cardiologist', count: 38 },
  { id: 'lungs', name: 'Lungs & Respiratory', icon: '🫁', color: 'from-blue-500 to-blue-600', diseases: ['Asthma', 'COPD', 'Pneumonia', 'Tuberculosis', 'Lung Cancer', 'Sleep Apnea', 'Pulmonary Fibrosis', 'Bronchitis'], specialist: 'Pulmonologist', count: 42 },
  { id: 'liver', name: 'Liver & Hepatic', icon: '🫀', color: 'from-yellow-500 to-yellow-600', diseases: ['Hepatitis A/B/C', 'Fatty Liver Disease', 'Liver Cirrhosis', 'Liver Cancer', 'Autoimmune Hepatitis', 'Wilson\'s Disease'], specialist: 'Hepatologist', count: 29 },
  { id: 'kidneys', name: 'Kidneys & Renal', icon: '🫘', color: 'from-teal-500 to-teal-600', diseases: ['Chronic Kidney Disease', 'Kidney Stones', 'Urinary Tract Infection', 'Glomerulonephritis', 'Polycystic Kidney Disease', 'Acute Kidney Injury'], specialist: 'Nephrologist', count: 31 },
  { id: 'digestive', name: 'Digestive System', icon: '🫃', color: 'from-green-500 to-green-600', diseases: ['GERD', 'Irritable Bowel Syndrome', 'Crohn\'s Disease', 'Ulcerative Colitis', 'Peptic Ulcer', 'Celiac Disease', 'Appendicitis'], specialist: 'Gastroenterologist', count: 52 },
  { id: 'skin', name: 'Skin & Dermatology', icon: '🧴', color: 'from-orange-500 to-orange-600', diseases: ['Psoriasis', 'Eczema', 'Acne', 'Melanoma', 'Urticaria', 'Vitiligo', 'Rosacea', 'Dermatitis'], specialist: 'Dermatologist', count: 48 },
  { id: 'bones', name: 'Bones & Musculoskeletal', icon: '🦴', color: 'from-slate-500 to-slate-600', diseases: ['Osteoporosis', 'Rheumatoid Arthritis', 'Osteoarthritis', 'Fractures', 'Scoliosis', 'Gout', 'Fibromyalgia'], specialist: 'Orthopedist', count: 55 },
  { id: 'endocrine', name: 'Endocrine System', icon: '⚗️', color: 'from-indigo-500 to-indigo-600', diseases: ['Type 1 Diabetes', 'Type 2 Diabetes', 'Hypothyroidism', 'Hyperthyroidism', 'Cushing\'s Syndrome', 'Addison\'s Disease'], specialist: 'Endocrinologist', count: 34 },
  { id: 'eyes', name: 'Eyes & Vision', icon: '👁️', color: 'from-cyan-500 to-cyan-600', diseases: ['Cataracts', 'Glaucoma', 'Macular Degeneration', 'Diabetic Retinopathy', 'Conjunctivitis', 'Dry Eye Syndrome'], specialist: 'Ophthalmologist', count: 27 },
  { id: 'ears', name: 'Ears, Nose & Throat', icon: '👂', color: 'from-pink-500 to-pink-600', diseases: ['Otitis Media', 'Tinnitus', 'Hearing Loss', 'Sinusitis', 'Tonsillitis', 'Allergic Rhinitis', 'Sleep Apnea'], specialist: 'ENT Specialist', count: 35 },
  { id: 'teeth', name: 'Dental & Oral Health', icon: '🦷', color: 'from-emerald-500 to-emerald-600', diseases: ['Dental Caries', 'Periodontitis', 'Gingivitis', 'Tooth Abscess', 'Oral Cancer', 'Bruxism', 'Temporomandibular Disorder'], specialist: 'Dentist', count: 24 },
  { id: 'reproductive', name: 'Reproductive System', icon: '🔬', color: 'from-rose-500 to-rose-600', diseases: ['PCOS', 'Endometriosis', 'Uterine Fibroids', 'Ovarian Cysts', 'Erectile Dysfunction', 'Prostate Issues'], specialist: 'Gynecologist / Urologist', count: 36 },
  { id: 'blood', name: 'Blood & Hematology', icon: '🩸', color: 'from-red-600 to-rose-600', diseases: ['Anemia', 'Leukemia', 'Lymphoma', 'Thrombocytopenia', 'Hemophilia', 'Sickle Cell Disease', 'Polycythemia'], specialist: 'Hematologist', count: 30 },
]

const container = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } }
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } }

export default function OrganBrowser() {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)

  const filtered = organs.filter((o) =>
    o.name.toLowerCase().includes(search.toLowerCase()) ||
    o.diseases.some((d) => d.toLowerCase().includes(search.toLowerCase()))
  )

  const selectedOrgan = selected ? organs.find((o) => o.id === selected) : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="section-title">Browse by Organ System</h1>
        <p className="section-subtitle text-sm">Explore diseases organized by body systems and organs</p>
      </div>

      <div className="relative">
        <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
        <input value={search} onChange={(e) => setSearch(e.target.value)}
          placeholder="Search organ systems or diseases..." className="input-field pl-10" />
      </div>

      {selectedOrgan ? (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <button onClick={() => setSelected(null)} className="flex items-center gap-2 text-sm text-slate-500 hover:text-blue-600 mb-4 transition-colors">
            ← Back to all organs
          </button>
          <div className="glass-card p-6">
            <div className={`inline-flex items-center gap-3 px-4 py-2 rounded-xl bg-gradient-to-r ${selectedOrgan.color} text-white mb-4`}>
              <span className="text-2xl">{selectedOrgan.icon}</span>
              <div>
                <p className="font-bold">{selectedOrgan.name}</p>
                <p className="text-xs opacity-80">{selectedOrgan.count} conditions</p>
              </div>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Specialist: <span className="font-semibold text-blue-600">{selectedOrgan.specialist}</span>
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {selectedOrgan.diseases.map((d, i) => (
                <motion.div key={d} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                  <Link to={`/diseases?search=${encodeURIComponent(d)}`}
                    className="flex items-center justify-between p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-blue-300 hover:shadow-sm text-sm text-slate-700 dark:text-slate-300 transition-all group">
                    {d}
                    <ChevronRight size={14} className="text-slate-400 group-hover:text-blue-500" />
                  </Link>
                </motion.div>
              ))}
              <Link to={`/diseases?organ=${selectedOrgan.id}`}
                className="flex items-center justify-between p-3 rounded-xl border-2 border-dashed border-blue-200 dark:border-blue-800 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-sm transition-all">
                View all {selectedOrgan.count} conditions <ChevronRight size={14} />
              </Link>
            </div>
          </div>
        </motion.div>
      ) : (
        <motion.div variants={container} initial="hidden" animate="show"
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {filtered.map((organ) => (
            <motion.button key={organ.id} variants={item}
              onClick={() => setSelected(organ.id)}
              className="glass-card p-5 text-left hover:shadow-card-hover transition-all duration-200 group"
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${organ.color} flex items-center justify-center text-2xl mb-3 group-hover:scale-110 transition-transform`}>
                {organ.icon}
              </div>
              <p className="font-semibold text-sm text-slate-800 dark:text-slate-100 leading-tight">{organ.name}</p>
              <p className="text-xs text-slate-400 mt-1">{organ.count} conditions</p>
              <div className="flex items-center gap-1 mt-3 text-xs text-blue-500 font-medium">
                Explore <ChevronRight size={12} />
              </div>
            </motion.button>
          ))}
        </motion.div>
      )}
    </div>
  )
}
