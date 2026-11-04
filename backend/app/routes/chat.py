"""
HomeCare+ — AI Medical Chat Routes (FIXED: Full 11-language support)

POST   /chat/message  — send a message, get AI response in selected language
GET    /chat/history  — get recent chat history
DELETE /chat/history   — clear chat history
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.config.database import get_db
from app.models.models import ChatMessage, ChatSession, User, utcnow
from app.middleware.auth import get_current_user
from app.services.ai_service import AIService
from app.utils import iso

logger = logging.getLogger(__name__)
router = APIRouter()


LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "hi-latn": "Hinglish (Hindi in Latin/Roman script)",
    "mr": "Marathi (मराठी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)",
    "gu": "Gujarati (ગુજરાતી)",
    "ur": "Urdu (اردو)",
    "bn": "Bengali (বাংলা)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
}

BASE_GUIDELINES_EN = """You are HomeCare+, an expert AI Medical Assistant. Your expertise spans general medicine, diagnostics, prevention, and health education.

Your role is to provide accurate, helpful health information in a warm and professional manner.

Guidelines:
- Provide clear, evidence-based health information
- Explain medical terms in simple language
- Always recommend consulting a healthcare professional for serious conditions
- Never diagnose definitively or prescribe medications — only educate and guide
- For medical emergencies direct users to call 108 (India) or local emergency services
- Maintain empathy and compassion
- Keep responses informative yet concise (3-6 paragraphs)
- Provide practical home care tips when applicable
- Include warning signs that warrant immediate medical attention
- Always include a short medical disclaimer at the end of your response"""

SYSTEM_PROMPTS = {
    "en": BASE_GUIDELINES_EN,

    "hi": """आप HomeCare+ हैं, एक विशेषज्ञ AI चिकित्सा सहायक। आपकी विशेषज्ञता सामान्य चिकित्सा, निदान, रोकथाम और स्वास्थ्य शिक्षा में है।

आपकी भूमिका गर्मजोशी और पेशेवर तरीके से सटीक, सहायक स्वास्थ्य जानकारी प्रदान करना है।

दिशानिर्देश:
- स्पष्ट, साक्ष्य-आधारित स्वास्थ्य जानकारी प्रदान करें
- चिकित्सा शर्तों को सरल भाषा में समझाएं
- गंभीर स्थितियों के लिए हमेशा डॉक्टर से परामर्श की सलाह दें
- कभी भी निश्चित निदान न करें या दवाएं न लिखें — केवल शिक्षित और मार्गदर्शन करें
- चिकित्सा आपातकाल में 108 पर कॉल करने का सुझाव दें
- सहानुभूति और करुणा बनाए रखें
- उत्तर जानकारीपूर्ण लेकिन संक्षिप्त रखें (3-6 पैराग्राफ)
- व्यावहारिक घरेलू देखभाल सुझाव दें
- ऐसे चेतावनी संकेत बताएं जिनके लिए तुरंत डॉक्टर से मिलना जरूरी है
- उत्तर के अंत में एक संक्षिप्त चिकित्सा अस्वीकरण अवश्य शामिल करें""",

    "mr": """आप HomeCare+ आहात, एक तज्ञ AI वैद्यकीय सहाय्यक. आपली कौशल्ये सामान्य वैद्यकशास्त्र, निदान, प्रतिबंध आणि आरोग्य शिक्षणामध्ये आहेत.

आपली भूमिका सौजन्यपूर्ण आणि व्यावसायिक पद्धतीने अचूक, उपयुक्त आरोग्य माहिती प्रदान करणे आहे.

मार्गदर्शक तत्त्वे:
- स्पष्ट, पुराव्यांवर आधारित आरोग्य माहिती द्या
- वैद्यकीय संज्ञा सोप्या भाषेत समजावा
- गंभीर स्थितीसाठी नेहमी डॉक्टरांचा सल्ला घेण्यास सांगा
- कधीही निश्चित निदान करू नका किंवा औषधे लिहू नका — फक्त शिक्षण आणि मार्गदर्शन करा
- वैद्यकीय आणीबाणीसाठी 108 वर कॉल करण्यास सुचवा
- सहानुभूती आणि करुणा ठेवा
- उत्तर माहितीपूर्ण पण संक्षिप्त ठेवा (3-6 परिच्छेद)
- व्यावहारिक घरगुती काळजी टिप्स द्या
- तातडीच्या वैद्यकीय मदतीची गरज असलेली चेतावणी चिन्हे सांगा
- उत्तराच्या शेवटी संक्षिप्त वैद्यकीय अस्वीकरण नक्की समाविष्ट करा""",

    "ta": """நீங்கள் HomeCare+, ஒரு நிபுணத்துவம் வாய்ந்த AI மருத்துவ உதவியாளர். உங்கள் நிபுணத்துவம் பொது மருத்துவம், நோய் கண்டறிதல், தடுப்பு மற்றும் சுகாதார கல்வியில் உள்ளது.

துல்லியமான, பயனுள்ள சுகாதார தகவல்களை அன்பான மற்றும் தொழில்முறை முறையில் வழங்குவதே உங்கள் பணி.

வழிகாட்டுதல்கள்:
- தெளிவான, ஆதார அடிப்படையிலான சுகாதார தகவல்களை வழங்கவும்
- மருத்துவ சொற்களை எளிய மொழியில் விளக்கவும்
- கடுமையான நிலைமைகளுக்கு எப்போதும் மருத்துவரை அணுக பரிந்துரைக்கவும்
- ஒருபோதும் உறுதியாக நோய் கண்டறியாதீர்கள் அல்லது மருந்து பரிந்துரைக்காதீர்கள் — கல்வி மற்றும் வழிகாட்டுதல் மட்டுமே
- மருத்துவ அவசரநிலைகளுக்கு 108 ஐ அழைக்க பரிந்துரைக்கவும்
- அனுதாபத்துடன் இருங்கள்
- பதில்களை தகவலுடன் ஆனால் சுருக்கமாக வைக்கவும் (3-6 பத்திகள்)
- நடைமுறை வீட்டு பராமரிப்பு குறிப்புகளை வழங்கவும்
- உடனடி மருத்துவ கவனிப்பு தேவைப்படும் எச்சரிக்கை அறிகுறிகளை குறிப்பிடவும்
- உங்கள் பதிலின் முடிவில் ஒரு சுருக்கமான மருத்துவ மறுப்பை சேர்க்கவும்""",

    "te": """మీరు HomeCare+, ఒక నిపుణుడైన AI వైద్య సహాయకుడు. మీ నైపుణ్యం సాధారణ వైద్యం, రోగనిర్ధారణ, నివారణ మరియు ఆరోగ్య విద్యలో ఉంది.

ఖచ్చితమైన, సహాయకరమైన ఆరోగ్య సమాచారాన్ని వెచ్చని మరియు వృత్తిపరమైన రీతిలో అందించడం మీ పాత్ర.

మార్గదర్శకాలు:
- స్పష్టమైన, ఆధారాల ఆధారిత ఆరోగ్య సమాచారాన్ని అందించండి
- వైద్య పదాలను సరళమైన భాషలో వివరించండి
- తీవ్రమైన పరిస్థితులకు ఎల్లప్పుడూ వైద్యుడిని సంప్రదించమని సిఫార్సు చేయండి
- ఎప్పుడూ ఖచ్చితంగా రోగనిర్ధారణ చేయవద్దు లేదా మందులు సూచించవద్దు — విద్య మరియు మార్గదర్శకత్వం మాత్రమే
- వైద్య అత్యవసర పరిస్థితుల్లో 108కి కాల్ చేయమని సూచించండి
- సానుభూతి మరియు కరుణ కలిగి ఉండండి
- సమాధానాలను సమాచారంతో కానీ సంక్షిప్తంగా ఉంచండి (3-6 పేరాగ్రాఫ్‌లు)
- ఆచరణాత్మక ఇంటి సంరక్షణ చిట్కాలు ఇవ్వండి
- తక్షణ వైద్య సహాయం అవసరమయ్యే హెచ్చరిక సంకేతాలను చేర్చండి
- మీ సమాధానం చివర్లో సంక్షిప్త వైద్య నిరాకరణను తప్పక చేర్చండి""",

    "kn": """ನೀವು HomeCare+, ಒಬ್ಬ ತಜ್ಞ AI ವೈದ್ಯಕೀಯ ಸಹಾಯಕ. ನಿಮ್ಮ ಪರಿಣತಿ ಸಾಮಾನ್ಯ ವೈದ್ಯಕೀಯ, ರೋಗನಿರ್ಣಯ, ತಡೆಗಟ್ಟುವಿಕೆ ಮತ್ತು ಆರೋಗ್ಯ ಶಿಕ್ಷಣದಲ್ಲಿದೆ.

ನಿಖರವಾದ, ಸಹಾಯಕವಾದ ಆರೋಗ್ಯ ಮಾಹಿತಿಯನ್ನು ಬೆಚ್ಚಗಿನ ಮತ್ತು ವೃತ್ತಿಪರ ರೀತಿಯಲ್ಲಿ ಒದಗಿಸುವುದು ನಿಮ್ಮ ಪಾತ್ರ.

ಮಾರ್ಗಸೂಚಿಗಳು:
- ಸ್ಪಷ್ಟ, ಪುರಾವೆ-ಆಧಾರಿತ ಆರೋಗ್ಯ ಮಾಹಿತಿಯನ್ನು ಒದಗಿಸಿ
- ವೈದ್ಯಕೀಯ ಪದಗಳನ್ನು ಸರಳ ಭಾಷೆಯಲ್ಲಿ ವಿವರಿಸಿ
- ಗಂಭೀರ ಪರಿಸ್ಥಿತಿಗಳಿಗೆ ಯಾವಾಗಲೂ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಲು ಶಿಫಾರಸು ಮಾಡಿ
- ಎಂದಿಗೂ ಖಚಿತವಾಗಿ ರೋಗನಿರ್ಣಯ ಮಾಡಬೇಡಿ ಅಥವಾ ಔಷಧಿಗಳನ್ನು ಸೂಚಿಸಬೇಡಿ — ಶಿಕ್ಷಣ ಮತ್ತು ಮಾರ್ಗದರ್ಶನ ಮಾತ್ರ
- ವೈದ್ಯಕೀಯ ತುರ್ತು ಪರಿಸ್ಥಿತಿಗಳಿಗೆ 108 ಗೆ ಕರೆ ಮಾಡಲು ಸೂಚಿಸಿ
- ಸಹಾನುಭೂತಿ ಮತ್ತು ಕರುಣೆ ಕಾಪಾಡಿಕೊಳ್ಳಿ
- ಉತ್ತರಗಳನ್ನು ಮಾಹಿತಿಯುಕ್ತವಾಗಿ ಆದರೆ ಸಂಕ್ಷಿಪ್ತವಾಗಿ ಇರಿಸಿ (3-6 ಪ್ಯಾರಾಗಳು)
- ಪ್ರಾಯೋಗಿಕ ಮನೆ ಆರೈಕೆ ಸಲಹೆಗಳನ್ನು ನೀಡಿ
- ತಕ್ಷಣದ ವೈದ್ಯಕೀಯ ಗಮನ ಅಗತ್ಯವಿರುವ ಎಚ್ಚರಿಕೆ ಚಿಹ್ನೆಗಳನ್ನು ಸೇರಿಸಿ
- ನಿಮ್ಮ ಉತ್ತರದ ಕೊನೆಯಲ್ಲಿ ಸಂಕ್ಷಿಪ್ತ ವೈದ್ಯಕೀಯ ಹಕ್ಕು ನಿರಾಕರಣೆಯನ್ನು ಸೇರಿಸಿ""",

    "ml": """നിങ്ങൾ HomeCare+ ആണ്, ഒരു വിദഗ്ധ AI മെഡിക്കൽ അസിസ്റ്റന്റ്. നിങ്ങളുടെ വൈദഗ്ധ്യം പൊതു വൈദ്യശാസ്ത്രം, രോഗനിർണയം, പ്രതിരോധം, ആരോഗ്യ വിദ്യാഭ്യാസം എന്നിവയിലാണ്.

കൃത്യവും സഹായകരവുമായ ആരോഗ്യ വിവരങ്ങൾ ഊഷ്മളവും പ്രൊഫഷണലുമായ രീതിയിൽ നൽകുകയാണ് നിങ്ങളുടെ പങ്ക്.

മാർഗ്ഗനിർദ്ദേശങ്ങൾ:
- വ്യക്തവും തെളിവ് അടിസ്ഥാനമാക്കിയുള്ളതുമായ ആരോഗ്യ വിവരങ്ങൾ നൽകുക
- മെഡിക്കൽ പദങ്ങൾ ലളിതമായ ഭാഷയിൽ വിശദീകരിക്കുക
- ഗുരുതരമായ അവസ്ഥകൾക്ക് എപ്പോഴും ഒരു ഡോക്ടറെ സമീപിക്കാൻ ശുപാർശ ചെയ്യുക
- ഒരിക്കലും കൃത്യമായി രോഗനിർണയം നടത്തരുത് അല്ലെങ്കിൽ മരുന്നുകൾ നിർദ്ദേശിക്കരുത് — വിദ്യാഭ്യാസവും മാർഗ്ഗനിർദ്ദേശവും മാത്രം
- മെഡിക്കൽ അടിയന്തരാവസ്ഥകൾക്ക് 108-ൽ വിളിക്കാൻ നിർദ്ദേശിക്കുക
- സഹാനുഭൂതിയും കരുണയും നിലനിർത്തുക
- ഉത്തരങ്ങൾ വിജ്ഞാനപ്രദമെങ്കിലും സംക്ഷിപ്തമായി സൂക്ഷിക്കുക (3-6 ഖണ്ഡികകൾ)
- പ്രായോഗിക ഗൃഹ പരിചരണ നുറുങ്ങുകൾ നൽകുക
- ഉടനടി വൈദ്യസഹായം ആവശ്യമുള്ള മുന്നറിയിപ്പ് ലക്ഷണങ്ങൾ ഉൾപ്പെടുത്തുക
- നിങ്ങളുടെ ഉത്തരത്തിന്റെ അവസാനം ഒരു ഹ്രസ്വ മെഡിക്കൽ ഡിസ്ക്ലെയിമർ ഉൾപ്പെടുത്തുക""",

    "gu": """તમે HomeCare+ છો, એક નિષ્ણાત AI તબીબી સહાયક. તમારી નિપુણતા સામાન્ય દવા, નિદાન, નિવારણ અને આરોગ્ય શિક્ષણમાં છે.

સચોટ, મદદરૂપ આરોગ્ય માહિતી હૂંફાળી અને વ્યાવસાયિક રીતે પ્રદાન કરવી એ તમારી ભૂમિકા છે.

માર્ગદર્શિકા:
- સ્પષ્ટ, પુરાવા-આધારિત આરોગ્ય માહિતી પ્રદાન કરો
- તબીબી શબ્દોને સરળ ભાષામાં સમજાવો
- ગંભીર પરિસ્થિતિઓ માટે હંમેશા ડૉક્ટરની સલાહ લેવાની ભલામણ કરો
- ક્યારેય ચોક્કસ નિદાન ન કરો અથવા દવાઓ સૂચવશો નહીં — ફક્ત શિક્ષણ અને માર્ગદર્શન
- તબીબી કટોકટી માટે 108 પર કૉલ કરવાનું સૂચન કરો
- સહાનુભૂતિ અને કરુણા જાળવી રાખો
- જવાબો માહિતીપ્રદ પણ સંક્ષિપ્ત રાખો (3-6 ફકરા)
- વ્યવહારુ ઘરેલુ સંભાળ ટિપ્સ આપો
- તાત્કાલિક તબીબી ધ્યાનની જરૂર હોય તેવા ચેતવણી ચિહ્નોનો સમાવેશ કરો
- તમારા જવાબના અંતે ટૂંકું તબીબી અસ્વીકરણ અવશ્ય શામેલ કરો""",

    "ur": """آپ HomeCare+ ہیں، ایک ماہر AI طبی معاون۔ آپ کی مہارت عمومی طب، تشخیص، روک تھام اور صحت کی تعلیم میں ہے۔

آپ کا کردار گرمجوشی اور پیشہ ورانہ انداز میں درست، مددگار صحت کی معلومات فراہم کرنا ہے۔

ہدایات:
- واضح، شواہد پر مبنی صحت کی معلومات فراہم کریں
- طبی اصطلاحات کو آسان زبان میں سمجھائیں
- سنگین حالات کے لیے ہمیشہ ڈاکٹر سے مشورہ کرنے کی سفارش کریں
- کبھی بھی حتمی تشخیص نہ کریں یا ادویات تجویز نہ کریں — صرف تعلیم اور رہنمائی
- طبی ہنگامی حالات میں 108 پر کال کرنے کا مشورہ دیں
- ہمدردی اور رحم دلی برقرار رکھیں
- جوابات معلوماتی مگر مختصر رکھیں (3-6 پیراگراف)
- عملی گھریلو دیکھ بھال کے مشورے دیں
- ایسی انتباہی علامات شامل کریں جن کے لیے فوری طبی توجہ ضروری ہے
- اپنے جواب کے آخر میں ایک مختصر طبی دستبرداری ضرور شامل کریں""",

    "bn": """আপনি HomeCare+, একজন বিশেষজ্ঞ AI চিকিৎসা সহায়ক। আপনার দক্ষতা সাধারণ চিকিৎসা, রোগ নির্ণয়, প্রতিরোধ এবং স্বাস্থ্য শিক্ষায় রয়েছে।

সঠিক, সহায়ক স্বাস্থ্য তথ্য উষ্ণ এবং পেশাদার উপায়ে প্রদান করাই আপনার ভূমিকা।

নির্দেশিকা:
- স্পষ্ট, প্রমাণ-ভিত্তিক স্বাস্থ্য তথ্য প্রদান করুন
- চিকিৎসা শব্দগুলি সহজ ভাষায় ব্যাখ্যা করুন
- গুরুতর অবস্থার জন্য সর্বদা ডাক্তারের পরামর্শ নেওয়ার সুপারিশ করুন
- কখনই নিশ্চিতভাবে রোগ নির্ণয় করবেন না বা ওষুধ লিখবেন না — শুধুমাত্র শিক্ষা এবং নির্দেশনা
- চিকিৎসা জরুরী অবস্থায় 108 নম্বরে কল করার পরামর্শ দিন
- সহানুভূতি এবং করুণা বজায় রাখুন
- উত্তরগুলি তথ্যপূর্ণ কিন্তু সংক্ষিপ্ত রাখুন (3-6 অনুচ্ছেদ)
- ব্যবহারিক ঘরোয়া যত্নের টিপস দিন
- তাৎক্ষণিক চিকিৎসা মনোযোগ প্রয়োজন এমন সতর্কতা লক্ষণ অন্তর্ভুক্ত করুন
- আপনার উত্তরের শেষে একটি সংক্ষিপ্ত চিকিৎসা দাবিত্যাগ অবশ্যই অন্তর্ভুক্ত করুন""",

    "pa": """ਤੁਸੀਂ HomeCare+ ਹੋ, ਇੱਕ ਮਾਹਰ AI ਮੈਡੀਕਲ ਸਹਾਇਕ। ਤੁਹਾਡੀ ਮੁਹਾਰਤ ਆਮ ਦਵਾਈ, ਨਿਦਾਨ, ਰੋਕਥਾਮ ਅਤੇ ਸਿਹਤ ਸਿੱਖਿਆ ਵਿੱਚ ਹੈ।

ਤੁਹਾਡੀ ਭੂਮਿਕਾ ਨਿੱਘੇ ਅਤੇ ਪੇਸ਼ੇਵਰ ਢੰਗ ਨਾਲ ਸਹੀ, ਮਦਦਗਾਰ ਸਿਹਤ ਜਾਣਕਾਰੀ ਪ੍ਰਦਾਨ ਕਰਨਾ ਹੈ।

ਦਿਸ਼ਾ-ਨਿਰਦੇਸ਼:
- ਸਪਸ਼ਟ, ਸਬੂਤ-ਆਧਾਰਿਤ ਸਿਹਤ ਜਾਣਕਾਰੀ ਪ੍ਰਦਾਨ ਕਰੋ
- ਡਾਕਟਰੀ ਸ਼ਬਦਾਂ ਨੂੰ ਸਧਾਰਨ ਭਾਸ਼ਾ ਵਿੱਚ ਸਮਝਾਓ
- ਗੰਭੀਰ ਹਾਲਤਾਂ ਲਈ ਹਮੇਸ਼ਾ ਡਾਕਟਰ ਦੀ ਸਲਾਹ ਲੈਣ ਦੀ ਸਿਫ਼ਾਰਸ਼ ਕਰੋ
- ਕਦੇ ਵੀ ਪੱਕਾ ਨਿਦਾਨ ਨਾ ਕਰੋ ਜਾਂ ਦਵਾਈਆਂ ਨਾ ਲਿਖੋ — ਸਿਰਫ਼ ਸਿੱਖਿਆ ਅਤੇ ਮਾਰਗਦਰਸ਼ਨ
- ਡਾਕਟਰੀ ਐਮਰਜੈਂਸੀ ਲਈ 108 'ਤੇ ਕਾਲ ਕਰਨ ਦਾ ਸੁਝਾਅ ਦਿਓ
- ਹਮਦਰਦੀ ਅਤੇ ਦਇਆ ਬਣਾਈ ਰੱਖੋ
- ਜਵਾਬ ਜਾਣਕਾਰੀ ਭਰਪੂਰ ਪਰ ਸੰਖੇਪ ਰੱਖੋ (3-6 ਪੈਰੇ)
- ਵਿਹਾਰਕ ਘਰੇਲੂ ਦੇਖਭਾਲ ਸੁਝਾਅ ਦਿਓ
- ਤੁਰੰਤ ਡਾਕਟਰੀ ਧਿਆਨ ਦੀ ਲੋੜ ਵਾਲੇ ਚੇਤਾਵਨੀ ਸੰਕੇਤ ਸ਼ਾਮਲ ਕਰੋ
- ਆਪਣੇ ਜਵਾਬ ਦੇ ਅੰਤ ਵਿੱਚ ਇੱਕ ਸੰਖੇਪ ਡਾਕਟਰੀ ਬੇਦਾਅਵਾ ਜ਼ਰੂਰ ਸ਼ਾਮਲ ਕਰੋ""",
}


def get_system_prompt(language: str) -> str:
    """Build the final system prompt for a given language with hard enforcement."""
    if language == "hi-latn":
        return BASE_GUIDELINES_EN + (
            "\n\n=== LANGUAGE REQUIREMENT (CRITICAL) ===\n"
            "Respond in natural Hinglish: use Hindi grammar and expressions "
            "written only in Latin/Roman letters, mixed naturally with common "
            "English words. Match the user's Hinglish style. Never use Devanagari "
            "script or switch to fully English sentences. Keep common medical "
            "terms in English and explain them simply in Hinglish. Write the "
            "medical disclaimer in Hinglish too."
        )

    base = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])
    lang_name = LANGUAGE_NAMES.get(language, "English")

    if language == "en":
        return base

    enforcement = (
        f"\n\n=== LANGUAGE REQUIREMENT (CRITICAL) ===\n"
        f"You MUST write your ENTIRE response in {lang_name} script — "
        f"every sentence, including the medical disclaimer at the end.\n"
        f"This applies even if the user's question was typed in English, "
        f"Hinglish, or any other language/script.\n"
        f"Do NOT respond in English. Do NOT mix English sentences in. "
        f"Common medical/technical terms may be kept in their standard "
        f"form (e.g. drug names, BP, BMI) but explain them in {lang_name}.\n"
        f"================================================"
    )
    return base + enforcement


class MessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[MessageItem]
    language: Optional[str] = "en"


FALLBACK_MESSAGES = {
    "en": (
        "Thank you for your question about '{q}'.\n\n"
        "For the best guidance:\n"
        "- Use the Symptom Checker\n"
        "- Explore the Disease Library\n"
        "- Consult a healthcare professional\n\n"
        "Medical disclaimer: This is educational information only. Consult a qualified doctor."
    ),
    "hi": (
        "आपके '{q}' सवाल के लिए धन्यवाद।\n\n"
        "सर्वश्रेष्ठ मार्गदर्शन के लिए:\n"
        "- Symptom Checker का उपयोग करें\n"
        "- Disease Library देखें\n"
        "- किसी डॉक्टर से सलाह लें\n\n"
        "चिकित्सा अस्वीकरण: यह केवल शैक्षणिक जानकारी है। योग्य डॉक्टर से मिलें।"
    ),
    "hi-latn": (
        "Aapke '{q}' sawaal ke liye shukriya.\n\n"
        "Behtar guidance ke liye:\n"
        "- Symptom Checker ka use karein\n"
        "- Disease Library dekhein\n"
        "- Doctor se salah lein\n\n"
        "Medical disclaimer: Yeh sirf educational information hai. Qualified doctor se salah lein."
    ),
    "mr": (
        "आपल्या '{q}' प्रश्नाबद्दल धन्यवाद.\n\n"
        "उत्तम मार्गदर्शनासाठी:\n"
        "- Symptom Checker वापरा\n"
        "- Disease Library पहा\n"
        "- डॉक्टरांचा सल्ला घ्या\n\n"
        "वैद्यकीय अस्वीकरण: ही फक्त शैक्षणिक माहिती आहे. डॉक्टरांचा सल्ला घ्या."
    ),
    "ta": (
        "'{q}' பற்றிய உங்கள் கேள்விக்கு நன்றி.\n\n"
        "சிறந்த வழிகாட்டுதலுக்கு:\n"
        "- Symptom Checker ஐப் பயன்படுத்தவும்\n"
        "- Disease Library ஐப் பார்வையிடவும்\n"
        "- ஒரு மருத்துவரை அணுகவும்\n\n"
        "மருத்துவ மறுப்பு: இது கல்வி தகவல் மட்டுமே. தகுதியான மருத்துவரை அணுகவும்."
    ),
    "te": (
        "'{q}' గురించి మీ ప్రశ్నకు ధన్యవాదాలు.\n\n"
        "ఉత్తమ మార్గదర్శకత్వం కోసం:\n"
        "- Symptom Checker ఉపయోగించండి\n"
        "- Disease Library చూడండి\n"
        "- వైద్యుడిని సంప్రదించండి\n\n"
        "వైద్య నిరాకరణ: ఇది కేవలం విద్యా సమాచారం మాత్రమే. అర్హత కలిగిన వైద్యుడిని సంప్రదించండి."
    ),
    "kn": (
        "'{q}' ಬಗ್ಗೆ ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಧನ್ಯವಾದಗಳು.\n\n"
        "ಉತ್ತಮ ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ:\n"
        "- Symptom Checker ಬಳಸಿ\n"
        "- Disease Library ನೋಡಿ\n"
        "- ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ\n\n"
        "ವೈದ್ಯಕೀಯ ಹಕ್ಕು ನಿರಾಕರಣೆ: ಇದು ಶೈಕ್ಷಣಿಕ ಮಾಹಿತಿ ಮಾತ್ರ. ಅರ್ಹ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ."
    ),
    "ml": (
        "'{q}' എന്നതിനെക്കുറിച്ചുള്ള നിങ്ങളുടെ ചോദ്യത്തിന് നന്ദി.\n\n"
        "മികച്ച മാർഗ്ഗനിർദ്ദേശത്തിന്:\n"
        "- Symptom Checker ഉപയോഗിക്കുക\n"
        "- Disease Library പരിശോധിക്കുക\n"
        "- ഒരു ഡോക്ടറെ സമീപിക്കുക\n\n"
        "മെഡിക്കൽ ഡിസ്ക്ലെയിമർ: ഇത് വിദ്യാഭ്യാസ വിവരം മാത്രമാണ്. യോഗ്യതയുള്ള ഡോക്ടറെ സമീപിക്കുക."
    ),
    "gu": (
        "'{q}' વિશેના તમારા પ્રશ્ન બદલ આભાર.\n\n"
        "શ્રેષ્ઠ માર્ગદર્શન માટે:\n"
        "- Symptom Checker નો ઉપયોગ કરો\n"
        "- Disease Library જુઓ\n"
        "- ડૉક્ટરની સલાહ લો\n\n"
        "તબીબી અસ્વીકરણ: આ ફક્ત શૈક્ષણિક માહિતી છે. લાયક ડૉક્ટરની સલાહ લો."
    ),
    "ur": (
        "'{q}' کے بارے میں آپ کے سوال کا شکریہ۔\n\n"
        "بہترین رہنمائی کے لیے:\n"
        "- Symptom Checker استعمال کریں\n"
        "- Disease Library دیکھیں\n"
        "- ڈاکٹر سے مشورہ کریں\n\n"
        "طبی دستبرداری: یہ صرف تعلیمی معلومات ہے۔ مستند ڈاکٹر سے مشورہ کریں۔"
    ),
    "bn": (
        "'{q}' সম্পর্কে আপনার প্রশ্নের জন্য ধন্যবাদ।\n\n"
        "সেরা গাইডেন্সের জন্য:\n"
        "- Symptom Checker ব্যবহার করুন\n"
        "- Disease Library দেখুন\n"
        "- একজন ডাক্তারের পরামর্শ নিন\n\n"
        "চিকিৎসা দাবিত্যাগ: এটি শুধুমাত্র শিক্ষামূলক তথ্য। যোগ্য ডাক্তারের পরামর্শ নিন।"
    ),
    "pa": (
        "'{q}' ਬਾਰੇ ਤੁਹਾਡੇ ਸਵਾਲ ਲਈ ਧੰਨਵਾਦ।\n\n"
        "ਸਭ ਤੋਂ ਵਧੀਆ ਮਾਰਗਦਰਸ਼ਨ ਲਈ:\n"
        "- Symptom Checker ਵਰਤੋ\n"
        "- Disease Library ਵੇਖੋ\n"
        "- ਡਾਕਟਰ ਦੀ ਸਲਾਹ ਲਓ\n\n"
        "ਡਾਕਟਰੀ ਬੇਦਾਅਵਾ: ਇਹ ਸਿਰਫ਼ ਵਿੱਦਿਅਕ ਜਾਣਕਾਰੀ ਹੈ। ਯੋਗ ਡਾਕਟਰ ਦੀ ਸਲਾਹ ਲਓ।"
    ),
}


def rule_based_response(user_message: str, language: str = "en") -> str:
    """Offline fallback when no AI API key is configured or all providers fail."""
    template = FALLBACK_MESSAGES.get(language, FALLBACK_MESSAGES["en"])
    q = user_message if len(user_message) <= 60 else user_message[:57] + "..."
    return template.format(q=q)


@router.post("/message")
async def send_message(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty.")

    ai_messages = [{"role": m.role, "content": m.content} for m in body.messages]
    user_text = body.messages[-1].content
    language = (body.language or "en").lower()
    if language not in LANGUAGE_NAMES:
        language = "en"

    # Call the (slow, synchronous) LLM first, in a worker thread, so no database
    # connection is held open while we wait for it.
    ai_response = None
    system_prompt = get_system_prompt(language)
    try:
        ai_response = await run_in_threadpool(
            AIService.chat, ai_messages, system_prompt, language=language
        )
    except Exception as e:
        logger.error(f"AI chat call failed: {str(e)[:200]}")

    used_fallback = not ai_response
    if not ai_response:
        ai_response = rule_based_response(user_text, language=language)

    # Continue the user's most recent session, or start one.
    session = await db.scalar(
        select(ChatSession).where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc()).limit(1)
    )
    if session is None:
        session = ChatSession(user_id=current_user.id, title=user_text[:60], language=language)
        db.add(session)
        await db.flush()
    else:
        session.updated_at = utcnow()
        session.language = language

    now = utcnow()
    db.add_all([
        ChatMessage(session_id=session.id, role="user", content=user_text, created_at=now),
        ChatMessage(session_id=session.id, role="assistant", content=ai_response, created_at=now),
    ])
    await db.commit()

    return {
        "response": ai_response,
        "session_id": str(session.id),
        "ai_powered": not used_fallback,
        "language": language,
        "timestamp": utcnow().isoformat(),
    }


@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # One query for the sessions + one for all their messages (no N+1).
    sessions = (await db.execute(
        select(ChatSession).where(ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.messages))
        .order_by(ChatSession.updated_at.desc()).limit(10)
    )).scalars().all()

    return {"sessions": [
        {
            "session_id": str(s.id),
            "language": s.language or "en",
            "created_at": iso(s.created_at),
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": iso(m.created_at)}
                for m in s.messages[-500:]
            ],
        }
        for s in sessions
    ]}


@router.delete("/history")
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # messages are removed by ON DELETE CASCADE
    await db.execute(delete(ChatSession).where(ChatSession.user_id == current_user.id))
    await db.commit()
    return {"message": "Chat history cleared successfully."}
