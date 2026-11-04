// HealthCoach.jsx
import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Dumbbell, Apple, Droplets, Moon, Brain, CheckCircle } from 'lucide-react'

const categories = [
  { key: 'diet', label: 'Diet & Nutrition', icon: Apple, color: 'from-green-500 to-teal-500',
    tips: ['Eat 5–9 servings of fruits and vegetables daily', 'Choose whole grains over refined grains', 'Include lean proteins: fish, legumes, poultry', 'Limit sodium to under 2,300 mg/day', 'Stay hydrated — drink 8 glasses of water daily', 'Reduce added sugars and processed foods', 'Include healthy fats: nuts, olive oil, avocado'] },
  { key: 'fitness', label: 'Fitness & Exercise', icon: Dumbbell, color: 'from-blue-500 to-indigo-500',
    tips: ['Aim for 150 minutes of moderate aerobic activity per week', 'Add 2 days of strength training exercises', 'Break up prolonged sitting with short walks', 'Stretch for 10 minutes before and after exercise', 'Start gradually and increase intensity over time', 'Track your steps — aim for 8,000–10,000/day'] },
  { key: 'hydration', label: 'Hydration', icon: Droplets, color: 'from-cyan-500 to-blue-500',
    tips: ['Drink 8–10 glasses (2–2.5L) of water daily', 'Start your day with a glass of water', 'Increase intake during exercise and hot weather', 'Monitor urine color — pale yellow indicates good hydration', 'Include water-rich foods: cucumber, watermelon, oranges', 'Limit caffeinated beverages as they can cause dehydration'] },
  { key: 'sleep', label: 'Sleep Health', icon: Moon, color: 'from-purple-500 to-indigo-500',
    tips: ['Aim for 7–9 hours of sleep per night', 'Maintain a consistent sleep schedule', 'Create a dark, cool, and quiet sleep environment', 'Avoid screens 1 hour before bedtime', 'Avoid caffeine after 2 PM', 'Practice relaxation techniques before sleep'] },
  { key: 'stress', label: 'Stress Management', icon: Brain, color: 'from-rose-500 to-pink-500',
    tips: ['Practice deep breathing exercises daily', 'Try mindfulness meditation for 10 minutes/day', 'Exercise regularly to reduce cortisol levels', 'Maintain strong social connections', 'Set realistic goals and prioritize tasks', 'Seek professional help if stress becomes unmanageable'] },
]

export default function HealthCoach() {
  const [active, setActive] = useState('diet')
  const activeCat = categories.find((c) => c.key === active)

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">AI Health Coach</h1>
        <p className="text-slate-500 text-sm mt-1">Personalized wellness guidance for diet, fitness, and mental health</p>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 flex-wrap">
        {categories.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setActive(key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${active === key ? 'bg-blue-600 text-white shadow-md' : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-blue-300'}`}>
            <Icon size={15} /> {label}
          </button>
        ))}
      </div>

      {activeCat && (
        <motion.div key={active} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <div className={`inline-flex items-center gap-3 px-4 py-2 rounded-xl bg-gradient-to-r ${activeCat.color} text-white mb-5`}>
            <activeCat.icon size={18} />
            <span className="font-semibold">{activeCat.label} Tips</span>
          </div>
          <ul className="space-y-3">
            {activeCat.tips.map((tip, i) => (
              <motion.li key={tip} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }}
                className="flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
                <CheckCircle size={16} className="text-green-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-slate-700 dark:text-slate-300">{tip}</p>
              </motion.li>
            ))}
          </ul>
        </motion.div>
      )}
      <p className="text-xs text-center text-slate-400">Health coaching tips are general guidelines. Individual needs vary. Consult a qualified nutritionist or fitness trainer for personalized plans.</p>
    </div>
  )
}
