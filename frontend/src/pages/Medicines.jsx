import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Search, ExternalLink, Pill, Shield, ShoppingCart, AlertCircle } from 'lucide-react'

const pharmacies = [
  { name: 'Netmeds',     url: 'https://www.netmeds.com', logo: 'NM', color: 'bg-green-500',  desc: 'Pan-India delivery, 20% off on first order', type: 'Online Pharmacy' },
  { name: '1mg',         url: 'https://www.1mg.com',     logo: '1m', color: 'bg-red-500',    desc: 'Genuine medicines, lab tests, consultations',  type: 'Health Platform' },
  { name: 'PharmEasy',   url: 'https://pharmeasy.in',    logo: 'PE', color: 'bg-blue-600',   desc: 'Fast delivery, extensive product range',       type: 'Online Pharmacy' },
  { name: 'MedPlus',     url: 'https://www.medplusmart.com', logo: 'MP', color: 'bg-purple-600', desc: 'Trusted retail chain with online ordering',  type: 'Retail + Online' },
  { name: 'Apollo Pharmacy', url: 'https://www.apollopharmacy.in', logo: 'AP', color: 'bg-orange-600', desc: 'Apollo group — trusted healthcare brand', type: 'Retail + Online' },
  { name: 'Amazon Health', url: 'https://www.amazon.in/health',  logo: 'AH', color: 'bg-yellow-600', desc: 'Health supplements and OTC medicines',    type: 'Marketplace' },
]

const categories = [
  { name: 'Pain Relief', medicines: ['Paracetamol', 'Ibuprofen', 'Aspirin', 'Diclofenac'] },
  { name: 'Antibiotics', medicines: ['Amoxicillin', 'Azithromycin', 'Ciprofloxacin'] },
  { name: 'Vitamins & Supplements', medicines: ['Vitamin D3', 'Vitamin C', 'Omega-3', 'Iron', 'Calcium', 'B12'] },
  { name: 'Antacids', medicines: ['Omeprazole', 'Ranitidine', 'Pantoprazole', 'Antacid syrup'] },
  { name: 'Allergy', medicines: ['Cetirizine', 'Loratadine', 'Fexofenadine'] },
  { name: 'Diabetes', medicines: ['Metformin', 'Insulin', 'Glipizide', 'Sitagliptin'] },
  { name: 'Blood Pressure', medicines: ['Amlodipine', 'Lisinopril', 'Atenolol', 'Losartan'] },
]

export default function Medicines() {
  const [search, setSearch] = useState('')

  const filteredCats = categories.map((cat) => ({
    ...cat,
    medicines: cat.medicines.filter((m) => m.toLowerCase().includes(search.toLowerCase())),
  })).filter((cat) => cat.medicines.length > 0 || !search)

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="section-title">Order Medicines</h1>
        <p className="section-subtitle text-sm">Find and order medicines from trusted pharmacy partners</p>
      </div>

      <div className="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800">
        <Shield size={16} className="text-blue-600 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-blue-700 dark:text-blue-400">
          HomeCare+ redirects to verified pharmacy partners for medicine ordering. Always purchase medicines with a valid prescription for prescription-only drugs. Never self-medicate without medical advice.
        </p>
      </div>

      {/* Trusted Pharmacies */}
      <div>
        <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Trusted Pharmacy Partners</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {pharmacies.map(({ name, url, logo, color, desc, type }) => (
            <motion.a key={name} href={url} target="_blank" rel="noopener noreferrer"
              whileHover={{ y: -2 }}
              className="glass-card p-5 hover:shadow-card-hover transition-all group"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center text-white font-bold text-sm`}>
                  {logo}
                </div>
                <div>
                  <p className="font-semibold text-slate-800 dark:text-slate-100">{name}</p>
                  <p className="text-xs text-slate-400">{type}</p>
                </div>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">{desc}</p>
              <div className="flex items-center gap-1.5 text-xs text-blue-500 font-medium group-hover:gap-2 transition-all">
                <ShoppingCart size={13} /> Order Now <ExternalLink size={11} />
              </div>
            </motion.a>
          ))}
        </div>
      </div>

      {/* Medicine search */}
      <div>
        <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Medicine Reference</h2>
        <div className="relative mb-4">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search medicines..." className="input-field pl-10" />
        </div>

        <div className="space-y-4">
          {filteredCats.map(({ name, medicines }) => (
            <div key={name} className="glass-card p-5">
              <div className="flex items-center gap-2 mb-3">
                <Pill size={16} className="text-blue-500" />
                <h3 className="font-semibold text-slate-800 dark:text-slate-100">{name}</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {medicines.map((m) => (
                  <a key={m}
                    href={`https://www.1mg.com/search/all?name=${encodeURIComponent(m)}`}
                    target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg text-sm hover:bg-blue-100 transition-colors"
                  >
                    {m} <ExternalLink size={11} />
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
        <AlertCircle size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-amber-700 dark:text-amber-400">
          Prescription medications require a valid doctor's prescription. Do not purchase or consume any medication without professional medical advice. Consult your doctor or pharmacist for guidance.
        </p>
      </div>
    </div>
  )
}
