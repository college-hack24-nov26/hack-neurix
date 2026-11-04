import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  en: {
    translation: {
      nav: {
        overview: 'Overview', dashboard: 'Dashboard', vitals: 'Vitals',
        aiTools: 'AI Tools', symptomChecker: 'Symptom Checker', aiAssistant: 'AI Assistant',
        imageAnalysis: 'Image Analysis', reportSummarizer: 'Report Summarizer', healthCoach: 'Health Coach',
        medicalLibrary: 'Medical Library', diseases: 'Diseases', organBrowser: 'Organ Browser',
        recordsAndCare: 'Records & Care', records: 'Health Records', telemedicine: 'Telemedicine',
        insurance: 'Insurance', findAndOrder: 'Find & Order', hospitals: 'Nearby Hospitals',
        medicines: 'Medicines', emergency: 'Emergency', settings: 'Settings', logout: 'Logout',
      },
      common: {
        loading: 'Loading...', save: 'Save', cancel: 'Cancel', submit: 'Submit',
        search: 'Search', viewAll: 'View All', back: 'Back', next: 'Next',
        analyze: 'Analyze', upload: 'Upload', delete: 'Delete', edit: 'Edit',
        close: 'Close', confirm: 'Confirm', download: 'Download',
        disclaimer: 'This AI tool does not replace professional medical advice. Always consult a qualified healthcare provider.',
        noData: 'No data available', error: 'An error occurred', retry: 'Retry',
      },
      dashboard: {
        title: 'Dashboard', greeting: 'Welcome back', todayVitals: "Today's Vitals",
        quickActions: 'Quick Actions', checkSymptoms: 'Check Symptoms', logVitals: 'Log Vitals',
        aiAssistant: 'AI Assistant', findHospital: 'Find Hospital', healthStatus: 'Health Status',
        allNormal: 'All vitals are within normal range.',
      },
      symptomChecker: {
        title: 'Symptom Checker', subtitle: 'Describe your symptoms for AI-powered analysis',
        selectSymptoms: 'Select Symptoms', followUp: 'Follow-up Questions', results: 'Analysis Results',
        addSymptom: 'Add symptom', analyze: 'Analyze Symptoms', possibleConditions: 'Possible Conditions',
        mostLikely: 'Most Likely', specialist: 'Consult Specialist', precautions: 'Precautions',
        homeRemedies: 'Home Remedies', medications: 'Suggested Medications', reset: 'Start Over',
        severity: 'Severity', probability: 'Probability',
      },
      vitals: {
        title: 'Health Vitals', logToday: "Log Today's Vitals", weeklyTrends: 'Weekly Trends',
        heartRate: 'Heart Rate', bloodPressure: 'Blood Pressure', oxygenLevel: 'Oxygen Level',
        bloodSugar: 'Blood Sugar', bmi: 'BMI', weight: 'Weight', steps: 'Steps',
        temperature: 'Temperature', saveVitals: 'Save Vitals', normalRanges: 'Normal Reference Ranges',
      },
      records: {
        title: 'Health Records', subtitle: 'Securely store and manage your medical documents',
        upload: 'Upload Record', labReport: 'Lab Report', prescription: 'Prescription',
        scan: 'Medical Scan', document: 'Document', analyzed: 'Analyzed',
      },
      settings: {
        title: 'Settings', subtitle: 'Manage your account and preferences',
        profile: 'Profile', notifications: 'Notifications', appearance: 'Appearance',
        language: 'Language', security: 'Security', saveChanges: 'Save Changes',
        firstName: 'First Name', lastName: 'Last Name', email: 'Email',
        phone: 'Phone', darkMode: 'Dark Mode', languageSettings: 'Language Settings',
      },
      hospitals: {
        title: 'Nearby Healthcare Facilities',
        subtitle: 'Find hospitals, clinics, pharmacies, and dental clinics near you',
        search: 'Search hospitals, specialties...', allFacilities: 'All Facilities',
        hospitals: 'Hospitals', clinics: 'Clinics', pharmacies: 'Pharmacies', dental: 'Dental Clinics',
        findingNearby: 'Finding nearby facilities...', allowLocation: 'Allow location access or search by name.',
        directions: 'Directions', distance: 'Distance', rating: 'Rating',
      },
      telemedicine: {
        title: 'Telemedicine', subtitle: 'Consult qualified doctors online',
        videoConsultation: 'Video Consultation', chatDoctor: 'Chat with Doctor',
        secondOpinion: 'Second Opinion', bookConsultation: 'Book Consultation',
        available: 'Available', unavailable: 'Unavailable', busy: 'Busy',
        experience: 'Experience', fee: 'Consultation Fee', languages: 'Languages',
        rating: 'Rating', specialization: 'Specialization',
        allDoctors: 'All Doctors', selectSpecialty: 'Select Specialty',
      },
    },
  },

  hi: {
    translation: {
      nav: {
        overview: 'अवलोकन', dashboard: 'डैशबोर्ड', vitals: 'महत्वपूर्ण संकेत',
        aiTools: 'AI उपकरण', symptomChecker: 'लक्षण जांच', aiAssistant: 'AI सहायक',
        imageAnalysis: 'छवि विश्लेषण', reportSummarizer: 'रिपोर्ट सारांश', healthCoach: 'स्वास्थ्य कोच',
        medicalLibrary: 'चिकित्सा पुस्तकालय', diseases: 'बीमारियाँ', organBrowser: 'अंग ब्राउज़र',
        recordsAndCare: 'रिकॉर्ड और देखभाल', records: 'स्वास्थ्य रिकॉर्ड', telemedicine: 'टेलीमेडिसिन',
        insurance: 'बीमा', findAndOrder: 'खोजें और ऑर्डर करें', hospitals: 'नजदीकी अस्पताल',
        medicines: 'दवाइयाँ', emergency: 'आपातकाल', settings: 'सेटिंग्स', logout: 'लॉग आउट',
      },
      common: {
        loading: 'लोड हो रहा है...', save: 'सहेजें', cancel: 'रद्द करें', submit: 'जमा करें',
        search: 'खोजें', viewAll: 'सब देखें', back: 'वापस', next: 'आगे',
        analyze: 'विश्लेषण करें', upload: 'अपलोड करें', delete: 'हटाएं', edit: 'संपादित करें',
        close: 'बंद करें', confirm: 'पुष्टि करें', download: 'डाउनलोड',
        disclaimer: 'यह AI टूल पेशेवर चिकित्सा सलाह की जगह नहीं लेता। कृपया किसी योग्य चिकित्सक से परामर्श लें।',
        noData: 'कोई डेटा उपलब्ध नहीं', error: 'कोई त्रुटि हुई', retry: 'पुनः प्रयास',
      },
      dashboard: {
        title: 'डैशबोर्ड', greeting: 'वापस आपका स्वागत है', todayVitals: 'आज के महत्वपूर्ण संकेत',
        quickActions: 'त्वरित क्रियाएं', checkSymptoms: 'लक्षण जांचें', logVitals: 'संकेत दर्ज करें',
        aiAssistant: 'AI सहायक', findHospital: 'अस्पताल खोजें', healthStatus: 'स्वास्थ्य स्थिति',
        allNormal: 'सभी संकेत सामान्य सीमा में हैं।',
      },
      symptomChecker: {
        title: 'लक्षण जांच', subtitle: 'AI-संचालित विश्लेषण के लिए अपने लक्षण बताएं',
        selectSymptoms: 'लक्षण चुनें', followUp: 'अनुवर्ती प्रश्न', results: 'विश्लेषण परिणाम',
        addSymptom: 'लक्षण जोड़ें', analyze: 'लक्षणों का विश्लेषण', possibleConditions: 'संभावित स्थितियां',
        mostLikely: 'सबसे संभावित', specialist: 'विशेषज्ञ से परामर्श', precautions: 'सावधानियां',
        homeRemedies: 'घरेलू उपाय', medications: 'सुझाई दवाएं', reset: 'फिर से शुरू करें',
        severity: 'गंभीरता', probability: 'संभावना',
      },
      vitals: {
        title: 'स्वास्थ्य संकेत', logToday: 'आज के संकेत दर्ज करें', weeklyTrends: 'साप्ताहिक रुझान',
        heartRate: 'हृदय गति', bloodPressure: 'रक्तचाप', oxygenLevel: 'ऑक्सीजन स्तर',
        bloodSugar: 'रक्त शर्करा', bmi: 'बीएमआई', weight: 'वजन', steps: 'कदम',
        temperature: 'तापमान', saveVitals: 'संकेत सहेजें', normalRanges: 'सामान्य संदर्भ सीमाएं',
      },
      records: {
        title: 'स्वास्थ्य रिकॉर्ड', subtitle: 'अपने चिकित्सा दस्तावेज़ सुरक्षित रखें',
        upload: 'रिकॉर्ड अपलोड करें', labReport: 'लैब रिपोर्ट', prescription: 'प्रिस्क्रिप्शन',
        scan: 'मेडिकल स्कैन', document: 'दस्तावेज़', analyzed: 'विश्लेषित',
      },
      settings: {
        title: 'सेटिंग्स', subtitle: 'अपना खाता और प्राथमिकताएं प्रबंधित करें',
        profile: 'प्रोफाइल', notifications: 'सूचनाएं', appearance: 'उपस्थिति',
        language: 'भाषा', security: 'सुरक्षा', saveChanges: 'परिवर्तन सहेजें',
        firstName: 'पहला नाम', lastName: 'अंतिम नाम', email: 'ईमेल',
        phone: 'फोन', darkMode: 'डार्क मोड', languageSettings: 'भाषा सेटिंग्स',
      },
      hospitals: {
        title: 'नजदीकी स्वास्थ्य सुविधाएं', subtitle: 'अपने नजदीक अस्पताल, क्लिनिक, फार्मेसी खोजें',
        search: 'अस्पताल, विशेषज्ञता खोजें...', allFacilities: 'सभी सुविधाएं',
        hospitals: 'अस्पताल', clinics: 'क्लिनिक', pharmacies: 'फार्मेसी', dental: 'डेंटल क्लिनिक',
        findingNearby: 'नजदीकी सुविधाएं खोज रहे हैं...', allowLocation: 'स्थान की अनुमति दें।',
        directions: 'दिशाएं', distance: 'दूरी', rating: 'रेटिंग',
      },
      telemedicine: {
        title: 'टेलीमेडिसिन', subtitle: 'ऑनलाइन योग्य डॉक्टरों से परामर्श करें',
        videoConsultation: 'वीडियो परामर्श', chatDoctor: 'डॉक्टर से चैट',
        secondOpinion: 'दूसरी राय', bookConsultation: 'परामर्श बुक करें',
        available: 'उपलब्ध', unavailable: 'अनुपलब्ध', busy: 'व्यस्त',
        experience: 'अनुभव', fee: 'परामर्श शुल्क', languages: 'भाषाएं',
        rating: 'रेटिंग', specialization: 'विशेषज्ञता',
        allDoctors: 'सभी डॉक्टर', selectSpecialty: 'विशेषज्ञता चुनें',
      },
    },
  },

  mr: {
    translation: {
      nav: {
        overview: 'विहंगावलोकन', dashboard: 'डॅशबोर्ड', vitals: 'महत्त्वाचे संकेत',
        aiTools: 'AI साधने', symptomChecker: 'लक्षण तपासणी', aiAssistant: 'AI सहाय्यक',
        imageAnalysis: 'प्रतिमा विश्लेषण', reportSummarizer: 'अहवाल सारांश', healthCoach: 'आरोग्य प्रशिक्षक',
        medicalLibrary: 'वैद्यकीय ग्रंथालय', diseases: 'आजार', organBrowser: 'अवयव ब्राउझर',
        recordsAndCare: 'नोंदी आणि काळजी', records: 'आरोग्य नोंदी', telemedicine: 'दूरवैद्यक',
        insurance: 'विमा', findAndOrder: 'शोधा आणि ऑर्डर करा', hospitals: 'जवळचे रुग्णालय',
        medicines: 'औषधे', emergency: 'आणीबाणी', settings: 'सेटिंग्ज', logout: 'बाहेर पडा',
      },
      common: {
        loading: 'लोड होत आहे...', save: 'जतन करा', cancel: 'रद्द करा', submit: 'सबमिट करा',
        search: 'शोधा', viewAll: 'सर्व पहा', back: 'मागे', next: 'पुढे',
        analyze: 'विश्लेषण करा', upload: 'अपलोड करा', delete: 'हटवा', edit: 'संपादित करा',
        close: 'बंद करा', confirm: 'पुष्टी करा', download: 'डाउनलोड',
        disclaimer: 'हे AI साधन व्यावसायिक वैद्यकीय सल्ल्याची जागा घेत नाही.',
        noData: 'कोणताही डेटा उपलब्ध नाही', error: 'त्रुटी आली', retry: 'पुन्हा प्रयत्न करा',
      },
      dashboard: {
        title: 'डॅशबोर्ड', greeting: 'परत आपले स्वागत आहे', todayVitals: 'आजचे महत्त्वाचे संकेत',
        quickActions: 'जलद क्रिया', checkSymptoms: 'लक्षणे तपासा', logVitals: 'संकेत नोंदवा',
        aiAssistant: 'AI सहाय्यक', findHospital: 'रुग्णालय शोधा', healthStatus: 'आरोग्य स्थिती',
        allNormal: 'सर्व संकेत सामान्य मर्यादेत आहेत.',
      },
      symptomChecker: {
        title: 'लक्षण तपासणी', subtitle: 'AI-चालित विश्लेषणासाठी आपली लक्षणे सांगा',
        selectSymptoms: 'लक्षणे निवडा', analyze: 'लक्षणांचे विश्लेषण', possibleConditions: 'संभाव्य स्थिती',
        mostLikely: 'सर्वात संभाव्य', specialist: 'तज्ञांचा सल्ला', precautions: 'खबरदारी',
        homeRemedies: 'घरगुती उपाय', medications: 'सुचवलेली औषधे', reset: 'पुन्हा सुरू करा',
        severity: 'तीव्रता', probability: 'संभाव्यता',
      },
      settings: {
        title: 'सेटिंग्ज', subtitle: 'आपले खाते व्यवस्थापित करा',
        profile: 'प्रोफाइल', notifications: 'सूचना', appearance: 'देखावा',
        language: 'भाषा', security: 'सुरक्षा', saveChanges: 'बदल जतन करा',
        darkMode: 'डार्क मोड', languageSettings: 'भाषा सेटिंग्ज',
      },
      hospitals: {
        title: 'जवळच्या आरोग्य सुविधा', subtitle: 'तुमच्या जवळचे रुग्णालय, क्लिनिक शोधा',
        search: 'रुग्णालय शोधा...', allFacilities: 'सर्व सुविधा',
        hospitals: 'रुग्णालये', clinics: 'क्लिनिक', pharmacies: 'फार्मसी', dental: 'दंत क्लिनिक',
        findingNearby: 'जवळच्या सुविधा शोधत आहोत...', allowLocation: 'स्थान परवानगी द्या.',
        directions: 'दिशा', distance: 'अंतर', rating: 'रेटिंग',
      },
      telemedicine: {
        title: 'दूरवैद्यक', subtitle: 'ऑनलाइन पात्र डॉक्टरांचा सल्ला घ्या',
        videoConsultation: 'व्हिडिओ सल्ला', chatDoctor: 'डॉक्टरशी चॅट',
        secondOpinion: 'दुसरे मत', bookConsultation: 'सल्ला बुक करा',
        available: 'उपलब्ध', unavailable: 'अनुपलब्ध', busy: 'व्यस्त',
        experience: 'अनुभव', fee: 'सल्ला शुल्क',
      },
    },
  },

  ta: {
    translation: {
      nav: {
        overview: 'கண்ணோட்டம்', dashboard: 'டாஷ்போர்டு', vitals: 'உயிர் அறிகுறிகள்',
        aiTools: 'AI கருவிகள்', symptomChecker: 'அறிகுறி சோதனை', aiAssistant: 'AI உதவியாளர்',
        imageAnalysis: 'படப் பகுப்பாய்வு', reportSummarizer: 'அறிக்கை சுருக்கம்', healthCoach: 'சுகாதார பயிற்சியாளர்',
        medicalLibrary: 'மருத்துவ நூலகம்', diseases: 'நோய்கள்', organBrowser: 'உறுப்பு உலாவி',
        records: 'சுகாதார பதிவுகள்', telemedicine: 'தொலைதூர மருத்துவம்',
        hospitals: 'அருகிலுள்ள மருத்துவமனைகள்', medicines: 'மருந்துகள்',
        emergency: 'அவசரகாலம்', settings: 'அமைப்புகள்', logout: 'வெளியேறு',
      },
      common: {
        loading: 'ஏற்றுகிறது...', save: 'சேமி', cancel: 'ரத்துசெய்', submit: 'சமர்ப்பி',
        search: 'தேடு', viewAll: 'அனைத்தும் காண்', back: 'திரும்பு', next: 'அடுத்து',
        analyze: 'பகுப்பாய்வு', upload: 'பதிவேற்று', delete: 'நீக்கு', edit: 'திருத்து',
        close: 'மூடு', confirm: 'உறுதிப்படுத்து', download: 'பதிவிறக்கம்',
        disclaimer: 'இந்த AI கருவி தொழில்முறை மருத்துவ ஆலோசனைக்கு மாற்றாக இல்லை.',
        noData: 'தரவு கிடைக்கவில்லை', error: 'பிழை ஏற்பட்டது', retry: 'மீண்டும் முயற்சி',
      },
      dashboard: {
        title: 'டாஷ்போர்டு', greeting: 'மீண்டும் வரவேற்கிறோம்', quickActions: 'விரைவு நடவடிக்கைகள்',
        checkSymptoms: 'அறிகுறிகளை சரிபார்', logVitals: 'உயிர் அறிகுறிகளை பதிவு செய்',
        aiAssistant: 'AI உதவியாளர்', findHospital: 'மருத்துவமனை கண்டுபிடி',
      },
      symptomChecker: {
        title: 'அறிகுறி சோதனை', subtitle: 'AI பகுப்பாய்வுக்கு உங்கள் அறிகுறிகளை விவரிக்கவும்',
        analyze: 'அறிகுறிகளை பகுப்பாய்வு', possibleConditions: 'சாத்தியமான நிலைகள்',
        precautions: 'முன்னெச்சரிக்கைகள்', homeRemedies: 'வீட்டு வைத்தியம்',
        medications: 'பரிந்துரைக்கப்பட்ட மருந்துகள்', reset: 'மீண்டும் தொடங்கு',
      },
      settings: {
        title: 'அமைப்புகள்', profile: 'சுயவிவரம்', language: 'மொழி',
        languageSettings: 'மொழி அமைப்புகள்', saveChanges: 'மாற்றங்களை சேமி',
        darkMode: 'இருண்ட பயன்முறை',
      },
      hospitals: {
        title: 'அருகிலுள்ள சுகாதார வசதிகள்',
        search: 'மருத்துவமனை தேடு...', allFacilities: 'அனைத்து வசதிகள்',
        hospitals: 'மருத்துவமனைகள்', clinics: 'கிளினிக்குகள்', pharmacies: 'மருந்தகங்கள்',
        directions: 'திசைகள்', distance: 'தூரம்', rating: 'மதிப்பீடு',
      },
      telemedicine: {
        title: 'தொலைதூர மருத்துவம்', bookConsultation: 'ஆலோசனை பதிவு செய்',
        available: 'கிடைக்கும்', experience: 'அனுபவம்', fee: 'ஆலோசனை கட்டணம்',
      },
    },
  },

  te: {
    translation: {
      nav: {
        overview: 'అవలోకనం', dashboard: 'డ్యాష్‌బోర్డ్', vitals: 'ముఖ్య సంకేతాలు',
        aiTools: 'AI సాధనాలు', symptomChecker: 'లక్షణ తనిఖీ', aiAssistant: 'AI సహాయకుడు',
        records: 'ఆరోగ్య రికార్డులు', telemedicine: 'టెలిమెడిసిన్',
        hospitals: 'సమీప ఆసుపత్రులు', medicines: 'ఔషధాలు',
        emergency: 'అత్యవసర', settings: 'సెట్టింగ్‌లు', logout: 'లాగ్ అవుట్',
      },
      common: {
        loading: 'లోడ్ అవుతోంది...', save: 'సేవ్ చేయండి', cancel: 'రద్దు', submit: 'సమర్పించండి',
        search: 'వెతకండి', back: 'వెనుకకు', next: 'తరువాత', analyze: 'విశ్లేషించండి',
        disclaimer: 'ఈ AI సాధనం వృత్తిపరమైన వైద్య సలహాను భర్తీ చేయదు.',
        noData: 'డేటా అందుబాటులో లేదు', error: 'లోపం సంభవించింది', retry: 'మళ్ళీ ప్రయత్నించండి',
      },
      dashboard: {
        title: 'డ్యాష్‌బోర్డ్', greeting: 'తిరిగి స్వాగతం', quickActions: 'త్వరిత చర్యలు',
        checkSymptoms: 'లక్షణాలు తనిఖీ చేయండి', aiAssistant: 'AI సహాయకుడు',
      },
      symptomChecker: {
        title: 'లక్షణ తనిఖీ', analyze: 'లక్షణాలను విశ్లేషించండి',
        possibleConditions: 'సాధ్యమయ్యే పరిస్థితులు', precautions: 'జాగ్రత్తలు',
        homeRemedies: 'ఇంటి చిట్కాలు', medications: 'సూచించిన ఔషధాలు',
      },
      settings: {
        title: 'సెట్టింగ్‌లు', profile: 'ప్రొఫైల్', language: 'భాష',
        languageSettings: 'భాషా సెట్టింగ్‌లు', saveChanges: 'మార్పులు సేవ్ చేయండి',
      },
      telemedicine: {
        title: 'టెలిమెడిసిన్', bookConsultation: 'సంప్రదింపు బుక్ చేయండి',
        available: 'అందుబాటులో', experience: 'అనుభవం', fee: 'సంప్రదింపు రుసుము',
      },
    },
  },

  kn: {
    translation: {
      nav: {
        overview: 'ಅವಲೋಕನ', dashboard: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', vitals: 'ಪ್ರಮುಖ ಸಂಕೇತಗಳು',
        aiTools: 'AI ಸಾಧನಗಳು', symptomChecker: 'ರೋಗಲಕ್ಷಣ ಪರಿಶೀಲಕ', aiAssistant: 'AI ಸಹಾಯಕ',
        imageAnalysis: 'ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆ', reportSummarizer: 'ವರದಿ ಸಾರಾಂಶ', healthCoach: 'ಆರೋಗ್ಯ ತರಬೇತಿದಾರ',
        medicalLibrary: 'ವೈದ್ಯಕೀಯ ಗ್ರಂಥಾಲಯ', diseases: 'ರೋಗಗಳು', organBrowser: 'ಅಂಗ ಬ್ರೌಸರ್',
        records: 'ಆರೋಗ್ಯ ದಾಖಲೆಗಳು', telemedicine: 'ಟೆಲಿಮೆಡಿಸಿನ್',
        hospitals: 'ಹತ್ತಿರದ ಆಸ್ಪತ್ರೆಗಳು', medicines: 'ಔಷಧಗಳು',
        emergency: 'ತುರ್ತು', settings: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', logout: 'ಲಾಗ್ ಔಟ್',
      },
      common: {
        loading: 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...', save: 'ಉಳಿಸಿ', cancel: 'ರದ್ದು', submit: 'ಸಲ್ಲಿಸಿ',
        search: 'ಹುಡುಕಿ', back: 'ಹಿಂದೆ', next: 'ಮುಂದೆ', analyze: 'ವಿಶ್ಲೇಷಿಸಿ',
        disclaimer: 'ಈ AI ಸಾಧನವು ವೃತ್ತಿಪರ ವೈದ್ಯಕೀಯ ಸಲಹೆಯನ್ನು ಬದಲಿಸುವುದಿಲ್ಲ.',
        noData: 'ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ', error: 'ದೋಷ ಸಂಭವಿಸಿದೆ', retry: 'ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ',
      },
      dashboard: {
        title: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', greeting: 'ಮತ್ತೆ ಸ್ವಾಗತ', quickActions: 'ತ್ವರಿತ ಕ್ರಿಯೆಗಳು',
        checkSymptoms: 'ರೋಗಲಕ್ಷಣಗಳನ್ನು ಪರಿಶೀಲಿಸಿ', aiAssistant: 'AI ಸಹಾಯಕ',
      },
      symptomChecker: {
        title: 'ರೋಗಲಕ್ಷಣ ಪರಿಶೀಲಕ', analyze: 'ರೋಗಲಕ್ಷಣಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಿ',
        possibleConditions: 'ಸಾಧ್ಯ ರೋಗಗಳು', precautions: 'ಮುಂಜಾಗ್ರತೆಗಳು',
        homeRemedies: 'ಮನೆ ಪರಿಹಾರಗಳು', medications: 'ಸೂಚಿಸಲಾದ ಔಷಧಗಳು',
      },
      settings: {
        title: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', profile: 'ಪ್ರೊಫೈಲ್', language: 'ಭಾಷೆ',
        languageSettings: 'ಭಾಷಾ ಸೆಟ್ಟಿಂಗ್‌ಗಳು', saveChanges: 'ಬದಲಾವಣೆಗಳನ್ನು ಉಳಿಸಿ', darkMode: 'ಡಾರ್ಕ್ ಮೋಡ್',
      },
      telemedicine: {
        title: 'ಟೆಲಿಮೆಡಿಸಿನ್', bookConsultation: 'ಸಮಾಲೋಚನೆ ಬುಕ್ ಮಾಡಿ',
        available: 'ಲಭ್ಯ', experience: 'ಅನುಭವ', fee: 'ಸಮಾಲೋಚನಾ ಶುಲ್ಕ',
      },
    },
  },

  ml: {
    translation: {
      nav: {
        overview: 'അവലോകനം', dashboard: 'ഡാഷ്‌ബോർഡ്', vitals: 'ജീവൻ നിർണായകങ്ങൾ',
        aiTools: 'AI ഉപകരണങ്ങൾ', symptomChecker: 'ലക്ഷണ പരിശോധന', aiAssistant: 'AI സഹായി',
        records: 'ആരോഗ്യ രേഖകൾ', telemedicine: 'ടെലിമെഡിസിൻ',
        hospitals: 'അടുത്തുള്ള ആശുപത്രികൾ', medicines: 'മരുന്നുകൾ',
        emergency: 'അടിയന്തിരം', settings: 'ക്രമീകരണങ്ങൾ', logout: 'ലോഗ് ഔട്ട്',
      },
      common: {
        loading: 'ലോഡ് ചെയ്യുന്നു...', save: 'സേവ് ചെയ്യുക', cancel: 'റദ്ദാക്കുക', submit: 'സമർപ്പിക്കുക',
        search: 'തിരയുക', back: 'തിരികെ', next: 'അടുത്തത്', analyze: 'വിശകലനം ചെയ്യുക',
        disclaimer: 'ഈ AI ഉപകരണം പ്രൊഫഷണൽ വൈദ്യ ഉപദേശം മാറ്റിവെക്കുന്നില്ല.',
        noData: 'ഡേറ്റ ലഭ്യമല്ല', error: 'ഒരു പിഴവ് സംഭവിച്ചു', retry: 'വീണ്ടും ശ്രമിക്കുക',
      },
      dashboard: {
        title: 'ഡാഷ്‌ബോർഡ്', greeting: 'തിരിച്ചു സ്വാഗതം', quickActions: 'ദ്രുത പ്രവർത്തനങ്ങൾ',
        checkSymptoms: 'ലക്ഷണങ്ങൾ പരിശോധിക്കുക', aiAssistant: 'AI സഹായി',
      },
      symptomChecker: {
        title: 'ലക്ഷണ പരിശോധന', analyze: 'ലക്ഷണങ്ങൾ വിശകലനം ചെയ്യുക',
        possibleConditions: 'സാധ്യ അവസ്ഥകൾ', precautions: 'മുൻകരുതലുകൾ',
        homeRemedies: 'വീട്ടു ചികിത്സകൾ', medications: 'നിർദ്ദേശിച്ച മരുന്നുകൾ',
      },
      settings: {
        title: 'ക്രമീകരണങ്ങൾ', profile: 'പ്രൊഫൈൽ', language: 'ഭാഷ',
        languageSettings: 'ഭാഷ ക്രമീകരണങ്ങൾ', saveChanges: 'മാറ്റങ്ങൾ സേവ് ചെയ്യുക', darkMode: 'ഡാർക്ക് മോഡ്',
      },
      telemedicine: {
        title: 'ടെലിമെഡിസിൻ', bookConsultation: 'കൺസൾട്ടേഷൻ ബുക്ക് ചെയ്യുക',
        available: 'ലഭ്യം', experience: 'അനുഭവം', fee: 'കൺസൾട്ടേഷൻ ഫീസ്',
      },
    },
  },

  gu: {
    translation: {
      nav: {
        overview: 'ઝલક', dashboard: 'ડેશબોર્ડ', vitals: 'મહત્વપૂર્ણ ચિહ્નો',
        aiTools: 'AI સાધનો', symptomChecker: 'લક્ષણ તપાસ', aiAssistant: 'AI સહાયક',
        records: 'આરોગ્ય રેકોર્ડ્સ', telemedicine: 'ટેલિમેડિસિન',
        hospitals: 'નજીકના હોસ્પિટલ', medicines: 'દવાઓ',
        emergency: 'કટોકટી', settings: 'સેટિંગ્સ', logout: 'લૉગ આઉટ',
      },
      common: {
        loading: 'લોડ કરી રહ્યું છે...', save: 'સાચવો', cancel: 'રદ કરો', submit: 'સ​મ​ર્પ​ણ',
        search: 'શોધો', back: 'પાછા', next: 'આગળ', analyze: 'વિશ્લેષણ',
        disclaimer: 'આ AI સાધન વ્યાવસાયિક ચિકિત્સા સલાહ નો વિકલ્પ નથી.',
        noData: 'ડેટા ઉપલબ્ધ નથી', error: 'ભૂલ આવી', retry: 'ફરીથી પ્રયાસ',
      },
      dashboard: {
        title: 'ડેશ​બો​ર્ડ', greeting: 'પાછા આવ્યા', quickActions: 'ઝડપી ક્રિયાઓ',
        checkSymptoms: 'લક્ષણો તપાસો', aiAssistant: 'AI સહ​ા​ય​ક',
      },
      symptomChecker: {
        title: 'લ​ક્ષ​ણ ત​પ​ા​સ', analyze: 'લ​ક્ષ​ણ​ો​નું વ​િ​શ​્​લ​ે​ષ​ણ',
        possibleConditions: 'સ​ં​ભ​વ​િ​ત ​સ​્​થ​િ​ત​િ​ઓ', homeRemedies: 'ઘ​ર​ે​ળ​ું ​ઉ​પ​ા​ય',
      },
      settings: {
        title: 'સ​ે​ટ​િ​ં​ગ​્​સ', profile: 'પ​્​ર​ો​ફ​ા​ઇ​લ', language: 'ભ​ા​ષ​ા',
        languageSettings: 'ભ​ા​ષ​ા ​સ​ે​ટ​િ​ં​ગ​્​સ', saveChanges: 'ફ​ે​ર​ફ​ા​ર​ ​સ​ા​ચ​વ​ો',
      },
      telemedicine: {
        title: 'ટ​ે​લ​િ​મ​ે​ડ​િ​સ​િ​ન', bookConsultation: 'પ​ર​ા​મ​ર​્​શ ​બ​ુ​ક ​ક​ર​ો',
        available: 'ઉ​પ​લ​બ​્​ધ', experience: 'અ​ન​ુ​ભ​વ',
      },
    },
  },

  bn: {
    translation: {
      nav: {
        overview: 'সংক্ষিপ্ত বিবরণ', dashboard: 'ড্যাশবোর্ড', vitals: 'গুরুত্বপূর্ণ সংকেত',
        aiTools: 'AI সরঞ্জাম', symptomChecker: 'উপসর্গ পরীক্ষক', aiAssistant: 'AI সহকারী',
        records: 'স্বাস্থ্য রেকর্ড', telemedicine: 'টেলিমেডিসিন',
        hospitals: 'কাছাকাছি হাসপাতাল', medicines: 'ওষুধ',
        emergency: 'জরুরি', settings: 'সেটিংস', logout: 'লগ আউট',
      },
      common: {
        loading: 'লোড হচ্ছে...', save: 'সংরক্ষণ করুন', cancel: 'বাতিল', submit: 'জমা দিন',
        search: 'অনুসন্ধান', back: 'পিছনে', next: 'পরবর্তী', analyze: 'বিশ্লেষণ',
        disclaimer: 'এই AI সরঞ্জাম পেশাদার চিকিৎসা পরামর্শের বিকল্প নয়।',
        noData: 'কোনো ডেটা নেই', error: 'ত্রুটি ঘটেছে', retry: 'আবার চেষ্টা করুন',
      },
      dashboard: {
        title: 'ড্যাশবোর্ড', greeting: 'ফিরে আসুন স্বাগতম', quickActions: 'দ্রুত ক্রিয়া',
        checkSymptoms: 'উপসর্গ পরীক্ষা করুন', aiAssistant: 'AI সহকারী',
      },
      symptomChecker: {
        title: 'উপসর্গ পরীক্ষক', analyze: 'উপসর্গ বিশ্লেষণ করুন',
        possibleConditions: 'সম্ভাব্য অবস্থা', precautions: 'সতর্কতা',
        homeRemedies: 'ঘরোয়া প্রতিকার', medications: 'পরামর্শকৃত ওষুধ',
      },
      settings: {
        title: 'সেটিংস', profile: 'প্রোফাইল', language: 'ভাষা',
        languageSettings: 'ভাষা সেটিংস', saveChanges: 'পরিবর্তন সংরক্ষণ করুন', darkMode: 'ডার্ক মোড',
      },
      telemedicine: {
        title: 'টেলিমেডিসিন', bookConsultation: 'পরামর্শ বুক করুন',
        available: 'উপলব্ধ', experience: 'অভিজ্ঞতা', fee: 'পরামর্শ ফি',
      },
    },
  },

  pa: {
    translation: {
      nav: {
        overview: 'ਸਮੀਖਿਆ', dashboard: 'ਡੈਸ਼ਬੋਰਡ', vitals: 'ਮਹੱਤਵਪੂਰਨ ਸੰਕੇਤ',
        aiTools: 'AI ਟੂਲਸ', symptomChecker: 'ਲੱਛਣ ਜਾਂਚ', aiAssistant: 'AI ਸਹਾਇਕ',
        records: 'ਸਿਹਤ ਰਿਕਾਰਡ', telemedicine: 'ਟੈਲੀਮੈਡੀਸਿਨ',
        hospitals: 'ਨਜ਼ਦੀਕੀ ਹਸਪਤਾਲ', medicines: 'ਦਵਾਈਆਂ',
        emergency: 'ਐਮਰਜੈਂਸੀ', settings: 'ਸੈਟਿੰਗ', logout: 'ਲਾਗ ਆਊਟ',
      },
      common: {
        loading: 'ਲੋਡ ਹੋ ਰਿਹਾ ਹੈ...', save: 'ਸੁਰੱਖਿਅਤ ਕਰੋ', cancel: 'ਰੱਦ ਕਰੋ', submit: 'ਜਮ੍ਹਾਂ ਕਰੋ',
        search: 'ਖੋਜ', back: 'ਵਾਪਸ', next: 'ਅਗਲਾ', analyze: 'ਵਿਸ਼ਲੇਸ਼ਣ',
        disclaimer: 'ਇਹ AI ਟੂਲ ਪੇਸ਼ੇਵਰ ਡਾਕਟਰੀ ਸਲਾਹ ਦੀ ਥਾਂ ਨਹੀਂ ਲੈਂਦਾ।',
        noData: 'ਕੋਈ ਡੇਟਾ ਨਹੀਂ', error: 'ਗਲਤੀ ਹੋਈ', retry: 'ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ',
      },
      dashboard: {
        title: 'ਡੈਸ਼ਬੋਰਡ', greeting: 'ਵਾਪਸ ਆਉਣ ਤੇ ਸੁਆਗਤ', quickActions: 'ਤੇਜ਼ ਕਾਰਵਾਈਆਂ',
        checkSymptoms: 'ਲੱਛਣ ਜਾਂਚੋ', aiAssistant: 'AI ਸਹਾਇਕ',
      },
      symptomChecker: {
        title: 'ਲੱਛਣ ਜਾਂਚ', analyze: 'ਲੱਛਣਾਂ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ',
        possibleConditions: 'ਸੰਭਾਵਿਤ ਸਥਿਤੀਆਂ', precautions: 'ਸਾਵਧਾਨੀਆਂ',
        homeRemedies: 'ਘਰੇਲੂ ਉਪਾਅ', medications: 'ਸੁਝਾਈਆਂ ਦਵਾਈਆਂ',
      },
      settings: {
        title: 'ਸੈਟਿੰਗ', profile: 'ਪ੍ਰੋਫਾਈਲ', language: 'ਭਾਸ਼ਾ',
        languageSettings: 'ਭਾਸ਼ਾ ਸੈਟਿੰਗ', saveChanges: 'ਤਬਦੀਲੀਆਂ ਸੁਰੱਖਿਅਤ ਕਰੋ', darkMode: 'ਡਾਰਕ ਮੋਡ',
      },
      telemedicine: {
        title: 'ਟੈਲੀਮੈਡੀਸਿਨ', bookConsultation: 'ਸਲਾਹ-ਮਸ਼ਵਰਾ ਬੁੱਕ ਕਰੋ',
        available: 'ਉਪਲਬਧ', experience: 'ਤਜ਼ਰਬਾ', fee: 'ਸਲਾਹ ਫੀਸ',
      },
    },
  },

  ur: {
    translation: {
      nav: {
        overview: 'جائزہ', dashboard: 'ڈیش بورڈ', vitals: 'اہم علامات',
        aiTools: 'AI آلات', symptomChecker: 'علامات جانچ', aiAssistant: 'AI مددگار',
        imageAnalysis: 'تصویر تجزیہ', reportSummarizer: 'رپورٹ خلاصہ', healthCoach: 'صحت کوچ',
        medicalLibrary: 'طبی لائبریری', diseases: 'بیماریاں', organBrowser: 'اعضاء براؤزر',
        records: 'صحت کے ریکارڈ', telemedicine: 'ٹیلی میڈیسن',
        hospitals: 'قریبی اسپتال', medicines: 'دوائیں',
        emergency: 'ہنگامی', settings: 'ترتیبات', logout: 'لاگ آؤٹ',
      },
      common: {
        loading: 'لوڈ ہو رہا ہے...', save: 'محفوظ کریں', cancel: 'منسوخ', submit: 'جمع کریں',
        search: 'تلاش کریں', back: 'واپس', next: 'آگے', analyze: 'تجزیہ کریں',
        disclaimer: 'یہ AI آلہ پیشہ ور طبی مشورے کی جگہ نہیں لیتا۔',
        noData: 'ڈیٹا دستیاب نہیں', error: 'خرابی ہوئی', retry: 'دوبارہ کوشش کریں',
      },
      dashboard: {
        title: 'ڈیش بورڈ', greeting: 'واپس خوش آمدید', quickActions: 'فوری اقدامات',
        checkSymptoms: 'علامات جانچیں', aiAssistant: 'AI مددگار',
      },
      symptomChecker: {
        title: 'علامات جانچ', analyze: 'علامات کا تجزیہ کریں',
        possibleConditions: 'ممکنہ بیماریاں', precautions: 'احتیاطی تدابیر',
        homeRemedies: 'گھریلو علاج', medications: 'تجویز کردہ دوائیں',
      },
      settings: {
        title: 'ترتیبات', profile: 'پروفائل', language: 'زبان',
        languageSettings: 'زبان کی ترتیبات', saveChanges: 'تبدیلیاں محفوظ کریں', darkMode: 'ڈارک موڈ',
      },
      telemedicine: {
        title: 'ٹیلی میڈیسن', bookConsultation: 'مشاورت بک کریں',
        available: 'دستیاب', experience: 'تجربہ', fee: 'مشاورت فیس',
      },
    },
  },
}

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('homecare-lang') || 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
  })

export default i18n
