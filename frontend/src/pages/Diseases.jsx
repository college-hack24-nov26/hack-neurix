import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Search, Filter, ChevronRight, BookOpen, AlertCircle } from 'lucide-react'

const diseasesData = [
  { id: 1, name: 'Type 2 Diabetes', organ: 'Endocrine', category: 'Metabolic', severity: 'chronic', specialist: 'Endocrinologist',
    overview: 'A metabolic disorder characterized by high blood sugar, insulin resistance, and relative insulin deficiency.',
    symptoms: ['Frequent urination', 'Excessive thirst', 'Unexplained weight loss', 'Fatigue', 'Blurred vision'],
    icd: 'E11' },
  { id: 2, name: 'Hypertension', organ: 'Heart', category: 'Cardiovascular', severity: 'chronic', specialist: 'Cardiologist',
    overview: 'A long-term medical condition where blood pressure in the arteries is persistently elevated.',
    symptoms: ['Headache', 'Shortness of breath', 'Nosebleeds', 'Dizziness', 'Chest pain'],
    icd: 'I10' },
  { id: 3, name: 'Asthma', organ: 'Lungs', category: 'Respiratory', severity: 'chronic', specialist: 'Pulmonologist',
    overview: 'A condition in which airways narrow, swell, and may produce extra mucus, making breathing difficult.',
    symptoms: ['Wheezing', 'Shortness of breath', 'Chest tightness', 'Coughing at night'],
    icd: 'J45' },
  { id: 4, name: 'Migraine', organ: 'Brain', category: 'Neurological', severity: 'episodic', specialist: 'Neurologist',
    overview: 'A primary headache disorder characterized by recurrent headaches that are moderate to severe.',
    symptoms: ['Severe headache', 'Nausea', 'Vomiting', 'Sensitivity to light', 'Aura'],
    icd: 'G43' },
  { id: 5, name: 'Gastroesophageal Reflux Disease', organ: 'Digestive', category: 'Gastrointestinal', severity: 'chronic', specialist: 'Gastroenterologist',
    overview: 'A digestive disorder that occurs when acidic stomach juices flow back into the food pipe.',
    symptoms: ['Heartburn', 'Regurgitation', 'Chest pain', 'Difficulty swallowing', 'Sour taste'],
    icd: 'K21' },
  { id: 6, name: 'Chronic Kidney Disease', organ: 'Kidneys', category: 'Renal', severity: 'chronic', specialist: 'Nephrologist',
    overview: 'Gradual loss of kidney function over time, affecting the body\'s ability to filter waste.',
    symptoms: ['Fatigue', 'Swollen ankles', 'Shortness of breath', 'Nausea', 'Decreased urination'],
    icd: 'N18' },
  { id: 7, name: 'Rheumatoid Arthritis', organ: 'Bones', category: 'Autoimmune', severity: 'chronic', specialist: 'Rheumatologist',
    overview: 'An autoimmune and inflammatory disease causing pain, swelling, and stiffness in the joints.',
    symptoms: ['Joint pain', 'Stiffness', 'Swollen joints', 'Fatigue', 'Loss of joint function'],
    icd: 'M06' },
  { id: 8, name: 'Pneumonia', organ: 'Lungs', category: 'Respiratory', severity: 'acute', specialist: 'Pulmonologist',
    overview: 'An infection that inflames the air sacs in one or both lungs, which may fill with fluid or pus.',
    symptoms: ['Cough with phlegm', 'Fever', 'Chills', 'Shortness of breath', 'Chest pain'],
    icd: 'J18' },
  { id: 9, name: 'Hypothyroidism', organ: 'Endocrine', category: 'Hormonal', severity: 'chronic', specialist: 'Endocrinologist',
    overview: 'A condition where the thyroid gland doesn\'t produce enough thyroid hormones.',
    symptoms: ['Fatigue', 'Weight gain', 'Cold sensitivity', 'Dry skin', 'Depression'],
    icd: 'E03' },
  { id: 10, name: 'Psoriasis', organ: 'Skin', category: 'Dermatological', severity: 'chronic', specialist: 'Dermatologist',
    overview: 'A skin disease that causes red, itchy scaly patches, most commonly on the knees, elbows, trunk, and scalp.',
    symptoms: ['Red patches', 'Silvery scales', 'Dry cracked skin', 'Itching', 'Thickened nails'],
    icd: 'L40' },
  { id: 11, name: 'Cataracts', organ: 'Eyes', category: 'Ophthalmological', severity: 'progressive', specialist: 'Ophthalmologist',
    overview: 'A clouding of the normally clear lens of the eye, causing blurry vision.',
    symptoms: ['Blurred vision', 'Halos around lights', 'Faded colors', 'Night blindness', 'Double vision'],
    icd: 'H26' },
  { id: 12, name: 'Dental Caries', organ: 'Teeth', category: 'Dental', severity: 'progressive', specialist: 'Dentist',
    overview: 'Tooth decay caused by bacteria that produce acid, breaking down tooth enamel.',
    symptoms: ['Toothache', 'Sensitivity to sweets', 'Visible pits or holes', 'Staining on teeth'],
    icd: 'K02' },
  { id: 13, name: 'Anemia', organ: 'Blood', category: 'Hematological', severity: 'variable', specialist: 'Hematologist',
    overview: 'A condition where you lack enough healthy red blood cells to carry adequate oxygen to tissues.',
    symptoms: ['Fatigue', 'Weakness', 'Pale skin', 'Shortness of breath', 'Dizziness'],
    icd: 'D64' },
  { id: 14, name: 'Appendicitis', organ: 'Digestive', category: 'Gastrointestinal', severity: 'acute', specialist: 'General Surgeon',
    overview: 'Inflammation of the appendix requiring prompt surgical treatment.',
    symptoms: ['Right lower abdominal pain', 'Nausea', 'Vomiting', 'Loss of appetite', 'Fever'],
    icd: 'K37' },
  { id: 15, name: 'Conjunctivitis', organ: 'Eyes', category: 'Ophthalmological', severity: 'acute', specialist: 'Ophthalmologist',
    overview: 'Inflammation or infection of the conjunctiva, the clear tissue covering the white part of the eye.',
    symptoms: ['Red eyes', 'Discharge', 'Itching', 'Tearing', 'Gritty feeling'],
    icd: 'H10' },
  { id: 16, name: 'Otitis Media', organ: 'Ears', category: 'ENT', severity: 'acute', specialist: 'ENT Specialist',
    overview: 'Infection or inflammation of the middle ear, common in children.',
    symptoms: ['Ear pain', 'Fluid drainage', 'Hearing loss', 'Fever', 'Irritability'],
    icd: 'H66' },
]

const categories = ['All', 'Cardiovascular', 'Respiratory', 'Neurological', 'Gastrointestinal', 'Metabolic', 'Hormonal', 'Renal', 'Dermatological', 'Dental', 'Ophthalmological', 'ENT', 'Autoimmune', 'Hematological']
const severityColors = {
  chronic:     'badge-warning',
  acute:       'badge-danger',
  episodic:    'badge-info',
  progressive: 'badge-warning',
  variable:    'badge-info',
}

export default function Diseases() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('All')
  const [filtered, setFiltered] = useState(diseasesData)

  useEffect(() => {
    let d = diseasesData
    if (search) d = d.filter((x) => x.name.toLowerCase().includes(search.toLowerCase()) || x.symptoms.some((s) => s.toLowerCase().includes(search.toLowerCase())))
    if (category !== 'All') d = d.filter((x) => x.category === category)
    setFiltered(d)
  }, [search, category])

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="section-title">Disease Library</h1>
          <p className="section-subtitle text-sm">Comprehensive information on {diseasesData.length}+ medical conditions</p>
        </div>
        <Link to="/organs" className="btn-secondary text-sm px-4 py-2.5">
          <BookOpen size={16} /> Browse by Organ
        </Link>
      </div>

      {/* Search + Filter */}
      <div className="glass-card p-5 space-y-4">
        <div className="relative">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search diseases, symptoms..."
            className="input-field pl-10"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {categories.map((c) => (
            <button key={c} onClick={() => setCategory(c)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                category === c
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((disease, i) => (
          <motion.div
            key={disease.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
          >
            <Link to={`/diseases/${disease.id}`}
              className="glass-card p-5 hover:shadow-card-hover transition-all duration-200 block group">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-slate-800 dark:text-slate-100 group-hover:text-blue-600 transition-colors">{disease.name}</h3>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{disease.icd} · {disease.organ}</p>
                </div>
                <ChevronRight size={16} className="text-slate-400 group-hover:text-blue-500 transition-colors flex-shrink-0 mt-1" />
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mb-3">{disease.overview}</p>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {disease.symptoms.slice(0, 3).map((s) => (
                  <span key={s} className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded text-xs">{s}</span>
                ))}
                {disease.symptoms.length > 3 && (
                  <span className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-400 rounded text-xs">+{disease.symptoms.length - 3}</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className={`${severityColors[disease.severity]}`}>{disease.severity}</span>
                <span className="text-xs text-blue-500 dark:text-blue-400 font-medium">{disease.specialist}</span>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16">
          <AlertCircle size={40} className="text-slate-300 dark:text-slate-600 mx-auto mb-3" />
          <p className="text-slate-500 dark:text-slate-400">No diseases found matching your search.</p>
        </div>
      )}
    </div>
  )
}
