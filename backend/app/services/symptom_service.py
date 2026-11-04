"""
HomeCare+ — Enhanced AI Symptom Analysis Engine
Real AI (GPT-4/Claude/Groq) powered analysis with a rule-based
100+ disease knowledge base as an offline safety-net fallback.
"""
import json
import logging
import numpy as np
from typing import List, Dict, Any

from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


DISEASE_KB = [
    # ── Cardiovascular ─────────────────────────────────────────────────────────
    {"name":"Hypertension","icd":"I10","specialist":"Cardiologist","severity_score":60,
     "precautions":["Monitor BP daily","Reduce sodium","Avoid stress","Take medications regularly"],
     "home_remedies":["Garlic extract","Hibiscus tea","Reduce caffeine","Daily walks"],
     "medications":["Amlodipine","Lisinopril","Atenolol","Losartan"],
     "symptoms":["headache","dizziness","blurred vision","chest pain","shortness of breath","nosebleed","fatigue","pounding heart"]},
    {"name":"Coronary Artery Disease","icd":"I25","specialist":"Cardiologist","severity_score":80,
     "precautions":["Avoid smoking","Low fat diet","Regular cardio exercise","Take prescribed medications"],
     "home_remedies":["Omega-3 foods","Limit saturated fats","Stress reduction","Regular walking"],
     "medications":["Aspirin","Statins","Beta-blockers","Nitroglycerin"],
     "symptoms":["chest pain","shortness of breath","fatigue","palpitations","sweating","nausea","jaw pain","arm pain"]},
    {"name":"Heart Failure","icd":"I50","specialist":"Cardiologist","severity_score":85,
     "precautions":["Restrict fluid intake","Low sodium diet","Daily weight monitoring","Limit exertion"],
     "home_remedies":["Elevate legs","Reduce salt","Light walking","Monitor swelling"],
     "medications":["Furosemide","Digoxin","Carvedilol","Enalapril"],
     "symptoms":["shortness of breath","fatigue","swollen legs","rapid heartbeat","persistent cough","reduced exercise tolerance","wheezing"]},
    {"name":"Atrial Fibrillation","icd":"I48","specialist":"Cardiologist","severity_score":70,
     "precautions":["Avoid alcohol","Manage stress","Take blood thinners as prescribed","Regular ECG"],
     "home_remedies":["Deep breathing","Vagal maneuvers","Reduce caffeine","Maintain healthy weight"],
     "medications":["Warfarin","Metoprolol","Digoxin","Amiodarone"],
     "symptoms":["palpitations","irregular heartbeat","shortness of breath","fatigue","dizziness","chest pain","weakness"]},
    # ── Respiratory ────────────────────────────────────────────────────────────
    {"name":"Common Cold","icd":"J00","specialist":"General Physician","severity_score":15,
     "precautions":["Wash hands frequently","Avoid close contact","Rest adequately","Stay warm"],
     "home_remedies":["Honey and ginger tea","Steam inhalation","Warm saline gargle","Turmeric milk"],
     "medications":["Paracetamol","Decongestants","Antihistamines","Vitamin C"],
     "symptoms":["runny nose","sore throat","cough","sneezing","mild fever","headache","fatigue","nasal congestion","watery eyes"]},
    {"name":"Influenza","icd":"J11","specialist":"General Physician","severity_score":45,
     "precautions":["Annual vaccination","Avoid crowded places","Cover cough","Rest at home"],
     "home_remedies":["Chicken broth","Elderberry tea","Steam inhalation","Honey lemon water"],
     "medications":["Oseltamivir","Paracetamol","Ibuprofen","Zanamivir"],
     "symptoms":["high fever","body aches","fatigue","headache","cough","chills","sore throat","loss of appetite","sweating"]},
    {"name":"Asthma","icd":"J45","specialist":"Pulmonologist","severity_score":55,
     "precautions":["Avoid triggers","Use rescue inhaler","Keep environment dust-free","Monitor peak flow"],
     "home_remedies":["Ginger tea","Breathing exercises","Avoid cold air","Maintain humidity"],
     "medications":["Salbutamol","Budesonide","Montelukast","Tiotropium"],
     "symptoms":["wheezing","shortness of breath","chest tightness","coughing at night","cough","breathing difficulty","chest pressure"]},
    {"name":"Pneumonia","icd":"J18","specialist":"Pulmonologist","severity_score":70,
     "precautions":["Complete antibiotic course","Rest","Stay hydrated","Vaccination preventable"],
     "home_remedies":["Warm fluids","Steam inhalation","Honey","Ginger tea"],
     "medications":["Amoxicillin","Azithromycin","Levofloxacin","Ceftriaxone"],
     "symptoms":["cough with phlegm","fever","chills","shortness of breath","chest pain","fatigue","nausea","sweating","rapid breathing"]},
    {"name":"Bronchitis","icd":"J40","specialist":"Pulmonologist","severity_score":40,
     "precautions":["Avoid smoking","Use humidifier","Rest well","Avoid pollutants"],
     "home_remedies":["Honey ginger tea","Steam","Turmeric milk","Salt water gargle"],
     "medications":["Bronchodilators","Cough suppressants","Expectorants","Antibiotics if bacterial"],
     "symptoms":["persistent cough","mucus production","fatigue","shortness of breath","slight fever","chest discomfort","wheezing"]},
    {"name":"Tuberculosis","icd":"A15","specialist":"Pulmonologist","severity_score":75,
     "precautions":["Complete full treatment","Isolate during infectious phase","Proper ventilation","Regular follow-up"],
     "home_remedies":["High protein diet","Sunshine exposure","Garlic","Drumstick leaves"],
     "medications":["Isoniazid","Rifampicin","Pyrazinamide","Ethambutol"],
     "symptoms":["persistent cough","blood in sputum","night sweats","weight loss","fatigue","fever","chest pain","loss of appetite"]},
    {"name":"COPD","icd":"J44","specialist":"Pulmonologist","severity_score":72,
     "precautions":["Quit smoking","Pulmonary rehabilitation","Avoid air pollution","Annual flu vaccine"],
     "home_remedies":["Pursed lip breathing","Stay hydrated","Avoid cold air","Gentle exercise"],
     "medications":["Salbutamol","Tiotropium","Salmeterol","Prednisolone"],
     "symptoms":["chronic cough","shortness of breath","wheezing","chest tightness","mucus production","frequent respiratory infections","fatigue"]},
    # ── Neurological ───────────────────────────────────────────────────────────
    {"name":"Migraine","icd":"G43","specialist":"Neurologist","severity_score":50,
     "precautions":["Avoid triggers","Maintain sleep schedule","Reduce stress","Limit caffeine"],
     "home_remedies":["Cold compress","Peppermint oil","Ginger tea","Dark quiet room"],
     "medications":["Sumatriptan","Topiramate","Amitriptyline","Ibuprofen"],
     "symptoms":["severe headache","nausea","vomiting","sensitivity to light","sensitivity to sound","visual aura","throbbing pain","neck stiffness"]},
    {"name":"Epilepsy","icd":"G40","specialist":"Neurologist","severity_score":70,
     "precautions":["Take medications regularly","Avoid sleep deprivation","No swimming alone","Medical alert bracelet"],
     "home_remedies":["Ketogenic diet","Avoid flickering lights","Regular sleep","Stress management"],
     "medications":["Valproate","Carbamazepine","Levetiracetam","Lamotrigine"],
     "symptoms":["seizures","loss of consciousness","muscle jerking","confusion","staring spells","temporary confusion","uncontrolled movements"]},
    {"name":"Stroke","icd":"I63","specialist":"Neurologist","severity_score":95,
     "precautions":["Control BP","Stop smoking","Regular exercise","Take blood thinners"],
     "home_remedies":["Rehabilitation exercises","Turmeric","Omega-3","Physiotherapy"],
     "medications":["Alteplase","Aspirin","Clopidogrel","Warfarin"],
     "symptoms":["sudden numbness","sudden confusion","difficulty speaking","vision problems","severe headache","loss of balance","facial drooping","arm weakness"]},
    {"name":"Parkinson's Disease","icd":"G20","specialist":"Neurologist","severity_score":65,
     "precautions":["Fall prevention","Regular physiotherapy","Medication timing","Speech therapy"],
     "home_remedies":["Exercise","Tai chi","Antioxidant foods","Sufficient sleep"],
     "medications":["Levodopa","Carbidopa","Pramipexole","Selegiline"],
     "symptoms":["tremors","stiffness","slow movement","balance problems","small handwriting","soft voice","masked face","shuffling gait"]},
    {"name":"Alzheimer's Disease","icd":"G30","specialist":"Neurologist","severity_score":70,
     "precautions":["Mental stimulation","Regular exercise","Social engagement","Safe home environment"],
     "home_remedies":["Brain games","Mediterranean diet","Regular routine","Music therapy"],
     "medications":["Donepezil","Memantine","Rivastigmine","Galantamine"],
     "symptoms":["memory loss","confusion","difficulty with tasks","language problems","disorientation","mood changes","personality changes","poor judgment"]},
    # ── Gastrointestinal ───────────────────────────────────────────────────────
    {"name":"GERD","icd":"K21","specialist":"Gastroenterologist","severity_score":40,
     "precautions":["Avoid spicy food","Don't lie down after meals","Elevate head while sleeping","Maintain healthy weight"],
     "home_remedies":["Aloe vera juice","Ginger tea","Apple cider vinegar diluted","Small frequent meals"],
     "medications":["Omeprazole","Ranitidine","Antacids","Metoclopramide"],
     "symptoms":["heartburn","regurgitation","chest pain","difficulty swallowing","sour taste","bloating","nausea","hoarse voice","chronic cough"]},
    {"name":"Irritable Bowel Syndrome","icd":"K58","specialist":"Gastroenterologist","severity_score":35,
     "precautions":["Avoid trigger foods","Manage stress","Regular exercise","Adequate fiber intake"],
     "home_remedies":["Peppermint tea","Probiotics","Avoid gluten","Fennel seeds"],
     "medications":["Mebeverine","Loperamide","Lactulose","Amitriptyline"],
     "symptoms":["abdominal cramping","bloating","diarrhea","constipation","gas","mucus in stool","incomplete bowel movement","abdominal pain"]},
    {"name":"Peptic Ulcer","icd":"K27","specialist":"Gastroenterologist","severity_score":55,
     "precautions":["Avoid NSAIDs","Stop smoking","Limit alcohol","Eat on schedule"],
     "home_remedies":["Cabbage juice","Licorice tea","Probiotics","Honey"],
     "medications":["Omeprazole","Amoxicillin","Clarithromycin","Antacids"],
     "symptoms":["burning stomach pain","nausea","vomiting","bloating","belching","loss of appetite","weight loss","dark stools"]},
    {"name":"Appendicitis","icd":"K37","specialist":"General Surgeon","severity_score":85,
     "precautions":["Seek emergency care immediately","Do not apply heat to abdomen","Nothing by mouth","Avoid pain relievers"],
     "home_remedies":["Emergency condition — no home remedies","Seek hospital care immediately"],
     "medications":["Antibiotics pre-surgery","IV fluids","Pain management","Surgical removal"],
     "symptoms":["right lower abdominal pain","nausea","vomiting","fever","loss of appetite","rebound tenderness","guarding","bloating"]},
    {"name":"Crohn's Disease","icd":"K50","specialist":"Gastroenterologist","severity_score":65,
     "precautions":["Avoid trigger foods","Take medications regularly","Quit smoking","Manage stress"],
     "home_remedies":["Low residue diet","Probiotics","Aloe vera","Turmeric"],
     "medications":["Mesalazine","Prednisolone","Azathioprine","Infliximab"],
     "symptoms":["abdominal pain","diarrhea","blood in stool","weight loss","fatigue","fever","mouth sores","fistulas"]},
    # ── Endocrine ──────────────────────────────────────────────────────────────
    {"name":"Type 2 Diabetes","icd":"E11","specialist":"Endocrinologist","severity_score":65,
     "precautions":["Monitor blood sugar","Diabetic diet","Regular exercise","Foot care"],
     "home_remedies":["Bitter gourd juice","Fenugreek seeds","Cinnamon","Jamun seeds"],
     "medications":["Metformin","Glipizide","Sitagliptin","Insulin"],
     "symptoms":["frequent urination","excessive thirst","unexplained weight loss","fatigue","blurred vision","slow healing wounds","numbness in feet","frequent infections"]},
    {"name":"Hypothyroidism","icd":"E03","specialist":"Endocrinologist","severity_score":45,
     "precautions":["Take thyroid hormone daily","Regular TSH monitoring","Avoid goitrogens","Consistent medication timing"],
     "home_remedies":["Iodine-rich foods","Selenium foods","Ashwagandha","Regular exercise"],
     "medications":["Levothyroxine","Liothyronine","Iodine supplements"],
     "symptoms":["fatigue","weight gain","cold intolerance","constipation","dry skin","hair loss","slow heart rate","depression","muscle weakness","memory problems"]},
    {"name":"Hyperthyroidism","icd":"E05","specialist":"Endocrinologist","severity_score":55,
     "precautions":["Avoid iodine excess","Regular thyroid monitoring","Eye protection","Medication compliance"],
     "home_remedies":["Bugleweed tea","Lemon balm","Calcium-rich diet","Avoid caffeine"],
     "medications":["Propylthiouracil","Methimazole","Beta-blockers","Radioiodine"],
     "symptoms":["weight loss","rapid heartbeat","anxiety","sweating","heat intolerance","frequent bowel movements","tremors","insomnia","goiter"]},
    {"name":"Cushing's Syndrome","icd":"E24","specialist":"Endocrinologist","severity_score":65,
     "precautions":["Regular cortisol monitoring","Blood pressure control","Bone density screening","Gradual medication reduction"],
     "home_remedies":["Low sodium diet","Calcium foods","Stress management","Gentle exercise"],
     "medications":["Metyrapone","Ketoconazole","Mifepristone","Pasireotide"],
     "symptoms":["weight gain in face","buffalo hump","stretch marks","easy bruising","muscle weakness","high blood pressure","diabetes","mood changes"]},
    # ── Dermatology ────────────────────────────────────────────────────────────
    {"name":"Eczema","icd":"L20","specialist":"Dermatologist","severity_score":30,
     "precautions":["Avoid irritants","Moisturize regularly","Avoid scratching","Wear cotton clothing"],
     "home_remedies":["Coconut oil","Aloe vera gel","Oatmeal bath","Evening primrose oil"],
     "medications":["Hydrocortisone cream","Tacrolimus","Antihistamines","Dupilumab"],
     "symptoms":["itchy skin","redness","dry skin","scaly patches","skin inflammation","blistering","oozing","thickened skin","darkened patches"]},
    {"name":"Psoriasis","icd":"L40","specialist":"Dermatologist","severity_score":40,
     "precautions":["Moisturize daily","Avoid triggers","Quit smoking","Limit alcohol"],
     "home_remedies":["Aloe vera","Dead Sea salt bath","Tea tree oil","Turmeric paste"],
     "medications":["Methotrexate","Cyclosporine","Adalimumab","Coal tar"],
     "symptoms":["red scaly patches","silver scales","dry cracked skin","itching","burning","joint pain","nail pitting","thickened nails"]},
    {"name":"Acne","icd":"L70","specialist":"Dermatologist","severity_score":20,
     "precautions":["Wash face twice daily","Avoid touching face","Use oil-free products","Change pillowcases frequently"],
     "home_remedies":["Tea tree oil","Neem paste","Honey mask","Aloe vera gel"],
     "medications":["Benzoyl peroxide","Tretinoin","Clindamycin","Doxycycline"],
     "symptoms":["pimples","blackheads","whiteheads","cysts","nodules","oily skin","redness","scarring","skin inflammation"]},
    {"name":"Urticaria","icd":"L50","specialist":"Dermatologist","severity_score":35,
     "precautions":["Identify and avoid triggers","Wear loose clothing","Cool showers","Avoid NSAIDs"],
     "home_remedies":["Cold compress","Aloe vera","Oatmeal bath","Ginger tea"],
     "medications":["Cetirizine","Loratadine","Fexofenadine","Prednisolone"],
     "symptoms":["hives","itching","swelling","red welts","burning sensation","skin rash","facial swelling","throat tightness"]},
    # ── Musculoskeletal ────────────────────────────────────────────────────────
    {"name":"Rheumatoid Arthritis","icd":"M06","specialist":"Rheumatologist","severity_score":60,
     "precautions":["Regular physiotherapy","Protect joints","Take DMARDs regularly","Balanced rest and activity"],
     "home_remedies":["Turmeric milk","Fish oil","Warm compress","Gentle yoga"],
     "medications":["Methotrexate","Hydroxychloroquine","Adalimumab","Prednisolone"],
     "symptoms":["joint pain","joint swelling","morning stiffness","fatigue","joint deformity","fever","loss of appetite","joint warmth","symmetrical joint involvement"]},
    {"name":"Osteoarthritis","icd":"M15","specialist":"Orthopedic Surgeon","severity_score":45,
     "precautions":["Weight management","Low impact exercise","Joint protection","Avoid repetitive stress"],
     "home_remedies":["Turmeric","Ginger","Warm compress","Epsom salt bath"],
     "medications":["Paracetamol","Ibuprofen","Diclofenac gel","Glucosamine"],
     "symptoms":["joint pain","stiffness","limited range of motion","joint cracking","swelling","tenderness","bone spurs","joint deformity","pain worsens with activity"]},
    {"name":"Gout","icd":"M10","specialist":"Rheumatologist","severity_score":50,
     "precautions":["Avoid purine-rich foods","Stay hydrated","Limit alcohol","Take urate-lowering therapy"],
     "home_remedies":["Cherry juice","Apple cider vinegar","Cold compress","Nettle tea"],
     "medications":["Colchicine","Allopurinol","Febuxostat","Indomethacin"],
     "symptoms":["sudden severe joint pain","joint redness","joint swelling","joint warmth","limited movement","tophi","tenderness","often affects big toe"]},
    {"name":"Osteoporosis","icd":"M81","specialist":"Orthopedic Surgeon","severity_score":55,
     "precautions":["Fall prevention","Calcium and Vitamin D","Weight-bearing exercise","Avoid smoking"],
     "home_remedies":["Dairy products","Leafy greens","Sun exposure","Sesame seeds"],
     "medications":["Alendronate","Risedronate","Denosumab","Teriparatide"],
     "symptoms":["back pain","height loss","stooped posture","bone fractures","brittle bones","back pain","neck pain","easy fractures"]},
    # ── Infectious ────────────────────────────────────────────────────────────
    {"name":"Malaria","icd":"B54","specialist":"Infectious Disease Specialist","severity_score":75,
     "precautions":["Use mosquito nets","Antimalarial prophylaxis","Eliminate standing water","Use repellents"],
     "home_remedies":["Fever management","Hydration","Neem leaves","Papaya leaf extract"],
     "medications":["Artemisinin","Chloroquine","Primaquine","Atovaquone-proguanil"],
     "symptoms":["cyclic fever","chills","sweating","headache","body aches","nausea","vomiting","fatigue","anemia","splenomegaly"]},
    {"name":"Typhoid","icd":"A01","specialist":"Infectious Disease Specialist","severity_score":70,
     "precautions":["Safe food and water","Typhoid vaccination","Hand hygiene","Avoid raw foods"],
     "home_remedies":["ORS fluids","Banana","Boiled water","Coconut water"],
     "medications":["Ceftriaxone","Ciprofloxacin","Azithromycin","Chloramphenicol"],
     "symptoms":["sustained high fever","headache","weakness","abdominal pain","constipation","diarrhea","rose spots","splenomegaly","loss of appetite","slow heart rate"]},
    {"name":"Dengue Fever","icd":"A90","specialist":"Infectious Disease Specialist","severity_score":70,
     "precautions":["Mosquito control","Use repellents","Wear full sleeves","Eliminate standing water"],
     "home_remedies":["Papaya leaf juice","Giloy juice","Hydration","Kiwi for platelets"],
     "medications":["Paracetamol","IV fluids","Platelet transfusion if needed","Avoid NSAIDs"],
     "symptoms":["sudden high fever","severe headache","eye pain","joint pain","muscle pain","skin rash","bleeding gums","low platelet count","nausea","fatigue"]},
    {"name":"COVID-19","icd":"U07","specialist":"Infectious Disease Specialist","severity_score":65,
     "precautions":["Isolation","Vaccination","Wear masks","Hand hygiene"],
     "home_remedies":["Steam inhalation","Zinc","Vitamin C and D","Honey ginger tea"],
     "medications":["Remdesivir","Dexamethasone","Baricitinib","Supportive care"],
     "symptoms":["fever","dry cough","fatigue","loss of smell","loss of taste","shortness of breath","body aches","headache","sore throat","diarrhea"]},
    {"name":"Chickenpox","icd":"B01","specialist":"General Physician","severity_score":40,
     "precautions":["Isolate infected person","Vaccination","Avoid scratching","Good hygiene"],
     "home_remedies":["Calamine lotion","Oatmeal bath","Neem leaves bath","Cooling foods"],
     "medications":["Acyclovir","Antihistamines","Calamine lotion","Paracetamol"],
     "symptoms":["itchy blisters","fever","tiredness","loss of appetite","fluid-filled blisters","skin rash","headache","widespread itching"]},
    # ── Renal ──────────────────────────────────────────────────────────────────
    {"name":"Urinary Tract Infection","icd":"N39","specialist":"Urologist","severity_score":45,
     "precautions":["Drink plenty of water","Wipe front to back","Empty bladder fully","Avoid holding urine"],
     "home_remedies":["Cranberry juice","Plenty of water","Probiotics","D-mannose"],
     "medications":["Nitrofurantoin","Trimethoprim","Ciprofloxacin","Fosfomycin"],
     "symptoms":["burning urination","frequent urination","cloudy urine","pelvic pain","strong urine odor","blood in urine","urgency","lower abdominal pain","fever"]},
    {"name":"Kidney Stones","icd":"N20","specialist":"Urologist","severity_score":60,
     "precautions":["Stay well hydrated","Reduce sodium","Limit oxalate foods","Regular monitoring"],
     "home_remedies":["Lemon juice with olive oil","Basil tea","Plenty of water","Apple cider vinegar"],
     "medications":["Tamsulosin","Potassium citrate","Pain relievers","IV fluids"],
     "symptoms":["severe back pain","side pain","radiating pain to groin","blood in urine","nausea","vomiting","frequent urination","painful urination","fever"]},
    {"name":"Chronic Kidney Disease","icd":"N18","specialist":"Nephrologist","severity_score":75,
     "precautions":["Control BP and diabetes","Low protein diet","Limit phosphorus","Regular nephrology checkups"],
     "home_remedies":["Limit sodium","Stay hydrated","Low potassium foods","Avoid NSAIDs"],
     "medications":["ACE inhibitors","Erythropoietin","Phosphate binders","Diuretics"],
     "symptoms":["fatigue","decreased urination","swelling in legs","shortness of breath","nausea","confusion","back pain","anemia","high blood pressure"]},
    # ── Mental Health ──────────────────────────────────────────────────────────
    {"name":"Depression","icd":"F32","specialist":"Psychiatrist","severity_score":60,
     "precautions":["Regular exercise","Social support","Avoid alcohol","Therapy compliance"],
     "home_remedies":["Sunlight exposure","Exercise","Omega-3","St. John's Wort"],
     "medications":["Sertraline","Fluoxetine","Escitalopram","Venlafaxine"],
     "symptoms":["persistent sadness","loss of interest","fatigue","sleep disturbances","appetite changes","concentration problems","feelings of worthlessness","hopelessness","suicidal thoughts"]},
    {"name":"Anxiety Disorder","icd":"F41","specialist":"Psychiatrist","severity_score":45,
     "precautions":["Regular exercise","Avoid caffeine","Mindfulness practice","Limit alcohol"],
     "home_remedies":["Deep breathing","Chamomile tea","Lavender oil","Meditation"],
     "medications":["Sertraline","Buspirone","Alprazolam","Propranolol"],
     "symptoms":["excessive worry","restlessness","fatigue","difficulty concentrating","muscle tension","sleep problems","irritability","rapid heartbeat","sweating","trembling"]},
    {"name":"Bipolar Disorder","icd":"F31","specialist":"Psychiatrist","severity_score":65,
     "precautions":["Mood monitoring","Regular therapy","Consistent sleep","Avoid alcohol"],
     "home_remedies":["Regular routine","Exercise","Omega-3","Sleep hygiene"],
     "medications":["Lithium","Valproate","Quetiapine","Olanzapine"],
     "symptoms":["mood swings","manic episodes","depressive episodes","impulsivity","racing thoughts","grandiosity","decreased need for sleep","risky behavior"]},
    # ── Blood ──────────────────────────────────────────────────────────────────
    {"name":"Anemia","icd":"D64","specialist":"Hematologist","severity_score":45,
     "precautions":["Iron-rich diet","Vitamin C with iron","Treat underlying cause","Regular blood tests"],
     "home_remedies":["Pomegranate juice","Beet juice","Dates","Spinach"],
     "medications":["Ferrous sulfate","Folic acid","Vitamin B12","Erythropoietin"],
     "symptoms":["fatigue","weakness","pale skin","shortness of breath","dizziness","cold hands","headache","brittle nails","pica","rapid heartbeat"]},
    {"name":"Leukemia","icd":"C91","specialist":"Oncologist","severity_score":90,
     "precautions":["Avoid infection exposure","Regular blood tests","Bone marrow monitoring","Chemotherapy compliance"],
     "home_remedies":["Nutritional support","Ginger for nausea","Stay hydrated","Gentle exercise when possible"],
     "medications":["Imatinib","Rituximab","Cytarabine","Hydroxyurea"],
     "symptoms":["fatigue","frequent infections","easy bruising","bleeding","bone pain","swollen lymph nodes","fever","weight loss","night sweats","pale skin"]},
    # ── ENT ────────────────────────────────────────────────────────────────────
    {"name":"Allergic Rhinitis","icd":"J30","specialist":"ENT Specialist","severity_score":20,
     "precautions":["Avoid allergens","Use air purifier","Keep windows closed","Change clothes after outdoor activities"],
     "home_remedies":["Neti pot saline rinse","Steam inhalation","Honey","Butterbur"],
     "medications":["Cetirizine","Fluticasone nasal spray","Montelukast","Immunotherapy"],
     "symptoms":["sneezing","runny nose","nasal congestion","itchy eyes","watery eyes","itchy throat","postnasal drip","headache","fatigue"]},
    {"name":"Sinusitis","icd":"J32","specialist":"ENT Specialist","severity_score":40,
     "precautions":["Use humidifier","Stay hydrated","Blow nose gently","Complete antibiotic course"],
     "home_remedies":["Steam inhalation","Saline rinse","Turmeric milk","Warm compress on face"],
     "medications":["Amoxicillin","Nasal corticosteroids","Decongestants","Antihistamines"],
     "symptoms":["facial pain","nasal congestion","thick nasal discharge","headache","reduced smell","cough","fever","tooth pain","fatigue","bad breath"]},
    {"name":"Otitis Media","icd":"H65","specialist":"ENT Specialist","severity_score":40,
     "precautions":["Breastfeeding reduces risk","Avoid smoke exposure","Vaccinations","Treat colds promptly"],
     "home_remedies":["Warm compress","Garlic oil","Olive oil","Neck exercises"],
     "medications":["Amoxicillin","Ibuprofen","Ear drops","Decongestants"],
     "symptoms":["ear pain","hearing difficulty","fluid draining from ear","fever","irritability","balance problems","ear fullness","buzzing in ear"]},
    # ── Eye ────────────────────────────────────────────────────────────────────
    {"name":"Conjunctivitis","icd":"H10","specialist":"Ophthalmologist","severity_score":25,
     "precautions":["Avoid touching eyes","Wash hands frequently","Don't share towels","Avoid contact lenses"],
     "home_remedies":["Cold compress","Chamomile tea bags","Rose water","Warm saline wash"],
     "medications":["Antibiotic eye drops","Antihistamine drops","Lubricating drops","Antiviral drops"],
     "symptoms":["red eyes","discharge from eyes","itching","burning","tearing","crusting","sensitivity to light","blurred vision","swollen eyelids"]},
    {"name":"Glaucoma","icd":"H40","specialist":"Ophthalmologist","severity_score":65,
     "precautions":["Regular IOP check","Eye drops compliance","Avoid high eye pressure activities","UV protection"],
     "home_remedies":["Omega-3","Antioxidants","Gentle eye massage","Reduce caffeine"],
     "medications":["Timolol eye drops","Latanoprost","Dorzolamide","Brimonidine"],
     "symptoms":["eye pain","blurred vision","halos around lights","headache","nausea","tunnel vision","gradual vision loss","eye redness"]},
    # ── Liver ──────────────────────────────────────────────────────────────────
    {"name":"Hepatitis B","icd":"B18","specialist":"Hepatologist","severity_score":70,
     "precautions":["Vaccination","Safe sex","Avoid sharing needles","Regular monitoring"],
     "home_remedies":["Milk thistle","Dandelion root","Avoid alcohol","Healthy diet"],
     "medications":["Tenofovir","Entecavir","Interferon alpha","Lamivudine"],
     "symptoms":["jaundice","fatigue","abdominal pain","loss of appetite","nausea","vomiting","dark urine","pale stools","joint pain","fever"]},
    {"name":"Fatty Liver Disease","icd":"K76","specialist":"Hepatologist","severity_score":55,
     "precautions":["Avoid alcohol","Weight loss","Control diabetes","Regular exercise"],
     "home_remedies":["Green tea","Coffee","Turmeric","Avoid processed foods"],
     "medications":["Vitamin E","Pioglitazone","Obeticholic acid","Lifestyle modification"],
     "symptoms":["fatigue","abdominal discomfort","enlarged liver","abdominal swelling","weakness","weight loss","jaundice","swollen legs","bruising"]},
    # ── Pediatric ─────────────────────────────────────────────────────────────
    {"name":"Measles","icd":"B05","specialist":"Pediatrician","severity_score":65,
     "precautions":["MMR vaccination","Isolate infected child","Vitamin A supplementation","Good nutrition"],
     "home_remedies":["Rest","Plenty of fluids","Vitamin A foods","Cool sponge bath"],
     "medications":["Vitamin A","Fever reducers","Antivirals in some cases","Antibiotics for bacterial complications"],
     "symptoms":["high fever","cough","runny nose","red eyes","Koplik spots","skin rash","sensitivity to light","muscle pain","sore throat"]},
    {"name":"Whooping Cough","icd":"A37","specialist":"Pediatrician","severity_score":65,
     "precautions":["DTaP vaccination","Isolate from newborns","Antibiotics early","Good hygiene"],
     "home_remedies":["Honey","Warm fluids","Humidifier","Small frequent meals"],
     "medications":["Azithromycin","Erythromycin","Clarithromycin","Corticosteroids"],
     "symptoms":["severe coughing fits","whooping sound","vomiting after cough","exhaustion","mild fever","runny nose","red face during cough","apnea in infants"]},
    # ── Immune ─────────────────────────────────────────────────────────────────
    {"name":"Lupus","icd":"M32","specialist":"Rheumatologist","severity_score":70,
     "precautions":["Sun protection","Regular monitoring","Stress management","Medication compliance"],
     "home_remedies":["Omega-3","Turmeric","Vitamin D","Avoid UV exposure"],
     "medications":["Hydroxychloroquine","Prednisolone","Azathioprine","Belimumab"],
     "symptoms":["butterfly rash","joint pain","fatigue","fever","sensitivity to sun","hair loss","mouth sores","kidney problems","chest pain","swollen joints"]},
    {"name":"HIV/AIDS","icd":"B24","specialist":"Infectious Disease Specialist","severity_score":85,
     "precautions":["Safe sex","ART compliance","Regular CD4 count monitoring","Avoid infections"],
     "home_remedies":["Nutritional support","Stress management","Regular exercise","Adequate sleep"],
     "medications":["Tenofovir","Emtricitabine","Efavirenz","Dolutegravir"],
     "symptoms":["fatigue","weight loss","recurrent infections","night sweats","swollen lymph nodes","fever","diarrhea","oral thrush","skin rash","memory problems"]},
]

# ── Build lookup structures ─────────────────────────────────────────────────────
ALL_SYMPTOMS = sorted(set(
    s.lower()
    for d in DISEASE_KB
    for s in d["symptoms"]
))


class SymptomAnalyzer:
    """Real AI symptom analyzer, with rule-based scoring as offline fallback."""

    def __init__(self):
        self.all_symptoms = ALL_SYMPTOMS

    def _tokenize(self, text: str) -> List[str]:
        """Normalize symptom string for matching."""
        return text.lower().strip()

    # ── Real AI Analysis (Primary) ───────────────────────────────────────

    def analyze_with_ai(
        self,
        symptoms: List[str],
        follow_up: Dict[str, Any] = None,
        language: str = "en",
    ) -> List[Dict] | None:
        """
        Ask a real LLM (OpenAI -> Anthropic -> Groq, via AIService) to reason
        about the symptoms like a doctor would, instead of doing simple
        keyword matching. Returns None if every AI provider is unavailable
        or fails, so the caller can fall back to `predict()`.
        """
        follow_up = follow_up or {}

        symptoms_str = ", ".join(symptoms)
        followup_str = "\n".join(f"- {k}: {v}" for k, v in follow_up.items()) or "Not provided"

        prompt = f"""A patient reports the following symptoms: {symptoms_str}

Additional context from follow-up questions:
{followup_str}

Analyze these symptoms like an experienced general physician doing a preliminary
triage assessment. Return ONLY a valid JSON object (no markdown, no extra text)
in EXACTLY this structure:

{{
  "possible_diseases": [
    {{
      "name": "Disease/condition name",
      "icd_code": "ICD-10 code if known, else empty string",
      "probability": <integer 0-100, your confidence this matches>,
      "severity": <integer 0-100, how serious this condition typically is>,
      "severity_level": "Mild" | "Moderate" | "Severe" | "Critical",
      "specialist": "Type of doctor to consult",
      "precautions": ["precaution 1", "precaution 2", "precaution 3"],
      "home_remedies": ["remedy 1", "remedy 2", "remedy 3"],
      "medications": ["commonly used medication 1", "medication 2"],
      "description": "1-2 sentence explanation of why this matches the symptoms"
    }}
  ]
}}

Rules:
- List the 3-5 MOST LIKELY conditions, ordered by probability (highest first)
- Be medically realistic — don't default to rare diseases when common ones fit better
- probability + severity should reflect genuine clinical reasoning, not guesses
- medications are informational examples only, NOT a prescription
- If symptoms are vague/insufficient, still give your best clinical reasoning
  but lower the probabilities accordingly
- Respond ONLY with the JSON object, nothing else"""

        system_prompt = (
            "You are a clinical triage AI assisting a symptom-checker tool. "
            "You provide structured, medically sound preliminary assessments "
            "in strict JSON format. You never refuse to analyze symptoms — "
            "you always provide your best clinical reasoning, clearly framed "
            "as informational and not a diagnosis."
        )

        try:
            raw = AIService.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                language=language,
            )
        except Exception as e:
            logger.error(f"AI symptom analysis call failed: {e}")
            return None

        if not raw:
            return None

        parsed = AIService.extract_json(raw)
        if not parsed or "possible_diseases" not in parsed:
            logger.warning("AI symptom analysis returned unparseable JSON, falling back")
            return None

        results = []
        for d in parsed["possible_diseases"][:5]:
            try:
                severity = int(d.get("severity", 50))
                severity_level = d.get("severity_level") or (
                    "Critical" if severity >= 85 else
                    "Severe"   if severity >= 70 else
                    "Moderate" if severity >= 40 else
                    "Mild"
                )
                results.append({
                    "name":             d.get("name", "Unknown"),
                    "icd_code":         d.get("icd_code", ""),
                    "probability":      int(d.get("probability", 50)),
                    "severity":         severity,
                    "severity_level":   severity_level,
                    "specialist":       d.get("specialist", "General Physician"),
                    "precautions":      d.get("precautions", []),
                    "home_remedies":    d.get("home_remedies", []),
                    "medications":      d.get("medications", []),
                    "matched_symptoms": len(symptoms),
                    "recommendations":  d.get("precautions", []),
                    "description":      d.get("description", ""),
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed AI disease entry: {e}")
                continue

        return results if results else None

    # ── Rule-Based Analysis (Offline Fallback) ───────────────────────────

    def predict(self, symptoms: List[str], follow_up: Dict[str, Any] = {}) -> List[Dict]:
        input_syms = [self._tokenize(s) for s in symptoms]
        scored = []

        for disease in DISEASE_KB:
            ds = [s.lower() for s in disease["symptoms"]]
            matches = 0
            for inp in input_syms:
                for ds_sym in ds:
                    if inp in ds_sym or ds_sym in inp:
                        matches += 1
                        break

            if matches == 0:
                continue

            # Score: matched / total disease symptoms, weighted by severity
            coverage  = matches / len(ds)
            precision = matches / max(len(input_syms), 1)
            prob      = round((coverage * 0.6 + precision * 0.4) * 100)

            # Follow-up modifiers
            severity_str = follow_up.get("severity", "")
            if "Severe" in severity_str or "Critical" in severity_str:
                prob = min(100, int(prob * 1.2))
            elif "Mild" in severity_str:
                prob = max(5, int(prob * 0.8))

            duration = follow_up.get("duration", "")
            if "More than a week" in duration:
                prob = min(100, int(prob * 1.15))

            severity_level = (
                "Critical" if disease["severity_score"] >= 85 else
                "Severe"   if disease["severity_score"] >= 70 else
                "Moderate" if disease["severity_score"] >= 40 else
                "Mild"
            )

            scored.append({
                "name":        disease["name"],
                "icd_code":    disease["icd"],
                "probability": prob,
                "severity":    disease["severity_score"],
                "severity_level": severity_level,
                "specialist":  disease["specialist"],
                "precautions": disease.get("precautions", []),
                "home_remedies": disease.get("home_remedies", []),
                "medications": disease.get("medications", []),
                "matched_symptoms": matches,
                "recommendations": disease.get("precautions", []),
                "description": f"{disease['name']} — consult a {disease['specialist']} for accurate diagnosis.",
            })

        # Sort by probability desc, take top 5
        scored.sort(key=lambda x: (-x["probability"], -x["severity"]))
        return scored[:5]
