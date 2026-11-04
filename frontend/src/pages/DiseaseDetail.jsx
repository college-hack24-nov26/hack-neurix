import React from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft, MapPin, BookOpen, CheckCircle, AlertTriangle,
  Stethoscope, Pill, Heart, Shield, Info, ChevronRight
} from 'lucide-react'

const diseaseDetails = {
  1: {
    name: 'Type 2 Diabetes', icd: 'E11', organ: 'Endocrine System', category: 'Metabolic',
    severity: 'chronic', specialist: 'Endocrinologist', specialist_type: 'endocrinology',
    overview: 'Type 2 diabetes is a chronic condition that affects the way your body metabolizes sugar (glucose). With type 2 diabetes, your body either resists the effects of insulin — a hormone that regulates the movement of sugar into your cells — or doesn\'t produce enough insulin to maintain normal glucose levels.',
    symptoms: ['Frequent urination (polyuria)', 'Excessive thirst (polydipsia)', 'Unexplained weight loss', 'Fatigue and weakness', 'Blurred vision', 'Slow-healing sores', 'Frequent infections', 'Tingling or numbness in hands or feet', 'Areas of darkened skin'],
    causes: ['Overweight and obesity', 'Physical inactivity', 'Family history and genetics', 'Age over 45', 'Prediabetes', 'Gestational diabetes history', 'Polycystic ovary syndrome'],
    risk_factors: ['Obesity (BMI above 25)', 'Waist circumference over 40 inches (men) or 35 inches (women)', 'Physical inactivity', 'Family history', 'Race/ethnicity', 'Age over 45', 'Prediabetes', 'Gestational diabetes'],
    complications: ['Heart disease and stroke', 'Nerve damage (neuropathy)', 'Kidney damage (nephropathy)', 'Eye damage (retinopathy)', 'Foot damage', 'Hearing impairment', 'Alzheimer\'s disease', 'Depression'],
    treatments: ['Blood sugar monitoring', 'Diabetes medications (Metformin, etc.)', 'Insulin therapy', 'Healthy diet', 'Regular exercise', 'Weight loss', 'Blood pressure and cholesterol medications'],
    medications: ['Metformin (first-line)', 'Sulfonylureas (Glipizide, Glyburide)', 'DPP-4 inhibitors (Sitagliptin)', 'SGLT2 inhibitors (Empagliflozin)', 'GLP-1 receptor agonists (Semaglutide)', 'Insulin (various types)'],
    home_remedies: ['Increase fiber intake', 'Reduce refined carbohydrates', 'Drink more water', 'Exercise regularly (150 min/week)', 'Monitor blood sugar at home', 'Manage stress levels', 'Get adequate sleep'],
    prevention: ['Maintain healthy weight', 'Regular physical activity', 'Healthy eating habits', 'Quit smoking', 'Regular health checkups', 'Monitor blood pressure and cholesterol'],
    precautions: ['Never skip prescribed medications', 'Monitor blood sugar regularly', 'Inspect feet daily', 'Stay hydrated', 'Carry fast-acting sugar for hypoglycemia', 'Wear medical alert identification'],
  },
  2: {
    name: 'Hypertension', icd: 'I10', organ: 'Cardiovascular System', category: 'Cardiovascular',
    severity: 'chronic', specialist: 'Cardiologist', specialist_type: 'cardiology',
    overview: 'Hypertension, or high blood pressure, is a condition where the force of blood against artery walls is consistently too high. Blood pressure is measured in millimetres of mercury (mmHg) and has two numbers: systolic (top number) and diastolic (bottom number). Normal is less than 120/80 mmHg.',
    symptoms: ['Often no symptoms (silent killer)', 'Severe headaches', 'Nosebleed', 'Fatigue or confusion', 'Vision problems', 'Chest pain', 'Difficulty breathing', 'Irregular heartbeat', 'Blood in urine'],
    causes: ['Primary (essential) hypertension — no identifiable cause', 'Secondary hypertension — caused by kidney disease, thyroid problems, sleep apnea, medications, or adrenal gland tumors'],
    risk_factors: ['Age over 65', 'Family history', 'Being overweight or obese', 'Physical inactivity', 'Tobacco use', 'Too much salt', 'Low potassium', 'Excessive alcohol', 'Stress', 'Chronic kidney disease', 'Sleep apnea'],
    complications: ['Heart attack or stroke', 'Aneurysm', 'Heart failure', 'Weakened blood vessels in kidneys', 'Vision loss', 'Metabolic syndrome', 'Trouble with memory', 'Dementia'],
    treatments: ['Lifestyle changes (first-line)', 'Antihypertensive medications', 'DASH diet', 'Regular cardiovascular exercise', 'Stress management', 'Limiting alcohol and sodium'],
    medications: ['ACE inhibitors (Lisinopril, Enalapril)', 'ARBs (Losartan, Valsartan)', 'Beta-blockers (Metoprolol, Atenolol)', 'Calcium channel blockers (Amlodipine)', 'Diuretics (Hydrochlorothiazide, Furosemide)'],
    home_remedies: ['DASH diet (Dietary Approaches to Stop Hypertension)', 'Reduce sodium to under 2,300 mg/day', 'Regular aerobic exercise', 'Limit alcohol', 'Quit smoking', 'Reduce stress', 'Monitor blood pressure at home'],
    prevention: ['Healthy diet rich in fruits and vegetables', 'Regular exercise', 'Healthy weight', 'Limit alcohol and sodium', 'Quit smoking', 'Regular blood pressure checks'],
    precautions: ['Take medications exactly as prescribed', 'Never stop medications without doctor approval', 'Monitor blood pressure daily at home', 'Avoid NSAIDs without doctor guidance', 'Limit caffeine intake'],
  },
}

// Fallback for diseases not in detail DB
const getDetail = (id) => diseaseDetails[id] || {
  name: 'Disease Information', icd: 'N/A', organ: 'Various', category: 'General',
  severity: 'variable', specialist: 'General Physician', specialist_type: 'general',
  overview: 'Detailed information for this condition is being updated. Please consult our AI Assistant or a healthcare professional for more information.',
  symptoms: ['Please consult a doctor for accurate symptoms'], causes: [], risk_factors: [],
  complications: [], treatments: [], medications: [], home_remedies: [], prevention: [], precautions: [],
}

const Section = ({ title, icon: Icon, items, color = 'blue' }) => {
  if (!items?.length) return null
  const colors = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-500',
    green: 'bg-green-50 dark:bg-green-900/20 text-green-500',
    red: 'bg-red-50 dark:bg-red-900/20 text-red-500',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-500',
    yellow: 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-500',
    teal: 'bg-teal-50 dark:bg-teal-900/20 text-teal-500',
  }
  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-9 h-9 rounded-xl ${colors[color]} flex items-center justify-center`}>
          <Icon size={18} />
        </div>
        <h3 className="font-semibold text-slate-800 dark:text-slate-100">{title}</h3>
      </div>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2.5 text-sm text-slate-600 dark:text-slate-400">
            <CheckCircle size={14} className="text-green-500 flex-shrink-0 mt-0.5" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function DiseaseDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const disease = getDetail(Number(id))

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-slate-500 hover:text-blue-600 transition-colors">
        <ArrowLeft size={16} /> Back to Diseases
      </button>

      {/* Header card */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6"
      >
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{disease.name}</h1>
              <span className="text-xs font-mono text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded">{disease.icd}</span>
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              <span className="badge-info">{disease.category}</span>
              <span className="badge-warning">{disease.severity}</span>
              <span className="text-xs text-slate-500 dark:text-slate-400">{disease.organ}</span>
            </div>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{disease.overview}</p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 mt-6 pt-6 border-t border-slate-100 dark:border-slate-700">
          <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
            <Stethoscope size={16} className="text-blue-500" />
            Recommended Specialist: <span className="font-semibold text-blue-600">{disease.specialist}</span>
          </div>
          <Link
            to={`/hospitals?specialist=${disease.specialist_type}`}
            className="btn-primary text-sm px-4 py-2.5 ml-auto"
          >
            <MapPin size={15} /> Find {disease.specialist} Nearby
          </Link>
        </div>
      </motion.div>

      {/* Content grid */}
      <div className="grid md:grid-cols-2 gap-5">
        <Section title="Symptoms" icon={AlertTriangle} items={disease.symptoms} color="yellow" />
        <Section title="Causes" icon={Info} items={disease.causes} color="blue" />
        <Section title="Risk Factors" icon={Shield} items={disease.risk_factors} color="red" />
        <Section title="Complications" icon={AlertTriangle} items={disease.complications} color="red" />
        <Section title="Treatments" icon={Stethoscope} items={disease.treatments} color="green" />
        <Section title="Medications" icon={Pill} items={disease.medications} color="purple" />
        <Section title="Home Remedies" icon={Heart} items={disease.home_remedies} color="teal" />
        <Section title="Prevention" icon={Shield} items={disease.prevention} color="green" />
      </div>

      {/* Precautions */}
      {disease.precautions?.length > 0 && (
        <div className="flex items-start gap-3 p-5 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
          <AlertTriangle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-800 dark:text-amber-400 mb-2">Important Precautions</p>
            <ul className="space-y-1">
              {disease.precautions.map((p) => (
                <li key={p} className="text-sm text-amber-700 dark:text-amber-500 flex items-start gap-2">
                  <ChevronRight size={13} className="flex-shrink-0 mt-0.5" /> {p}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-xs text-center text-slate-400 px-4 py-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
        This information is for educational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional for diagnosis and treatment decisions.
      </p>
    </div>
  )
}
