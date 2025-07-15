// Multi-language support for BhashAI Platform
// Supporting 20+ Indian and International Languages

const SUPPORTED_LANGUAGES = {
    'en': {
        name: 'English',
        nativeName: 'English',
        flag: '🇺🇸',
        rtl: false,
        voice: 'en-US'
    },
    'hi': {
        name: 'Hindi',
        nativeName: 'हिंदी',
        flag: '🇮🇳',
        rtl: false,
        voice: 'hi-IN'
    },
    'bn': {
        name: 'Bengali',
        nativeName: 'বাংলা',
        flag: '🇧🇩',
        rtl: false,
        voice: 'bn-IN'
    },
    'te': {
        name: 'Telugu',
        nativeName: 'తెలుగు',
        flag: '🇮🇳',
        rtl: false,
        voice: 'te-IN'
    },
    'ta': {
        name: 'Tamil',
        nativeName: 'தமிழ்',
        flag: '🇮🇳',
        rtl: false,
        voice: 'ta-IN'
    },
    'mr': {
        name: 'Marathi',
        nativeName: 'मराठी',
        flag: '🇮🇳',
        rtl: false,
        voice: 'mr-IN'
    },
    'gu': {
        name: 'Gujarati',
        nativeName: 'ગુજરાતી',
        flag: '🇮🇳',
        rtl: false,
        voice: 'gu-IN'
    },
    'kn': {
        name: 'Kannada',
        nativeName: 'ಕನ್ನಡ',
        flag: '🇮🇳',
        rtl: false,
        voice: 'kn-IN'
    },
    'ml': {
        name: 'Malayalam',
        nativeName: 'മലയാളം',
        flag: '🇮🇳',
        rtl: false,
        voice: 'ml-IN'
    },
    'pa': {
        name: 'Punjabi',
        nativeName: 'ਪੰਜਾਬੀ',
        flag: '🇮🇳',
        rtl: false,
        voice: 'pa-IN'
    },
    'or': {
        name: 'Odia',
        nativeName: 'ଓଡ଼ିଆ',
        flag: '🇮🇳',
        rtl: false,
        voice: 'or-IN'
    },
    'as': {
        name: 'Assamese',
        nativeName: 'অসমীয়া',
        flag: '🇮🇳',
        rtl: false,
        voice: 'as-IN'
    },
    'ur': {
        name: 'Urdu',
        nativeName: 'اردو',
        flag: '🇵🇰',
        rtl: true,
        voice: 'ur-PK'
    },
    'ne': {
        name: 'Nepali',
        nativeName: 'नेपाली',
        flag: '🇳🇵',
        rtl: false,
        voice: 'ne-NP'
    },
    'si': {
        name: 'Sinhala',
        nativeName: 'සිංහල',
        flag: '🇱🇰',
        rtl: false,
        voice: 'si-LK'
    },
    'ar': {
        name: 'Arabic',
        nativeName: 'العربية',
        flag: '🇸🇦',
        rtl: true,
        voice: 'ar-SA'
    },
    'zh': {
        name: 'Chinese',
        nativeName: '中文',
        flag: '🇨🇳',
        rtl: false,
        voice: 'zh-CN'
    },
    'ja': {
        name: 'Japanese',
        nativeName: '日本語',
        flag: '🇯🇵',
        rtl: false,
        voice: 'ja-JP'
    },
    'ko': {
        name: 'Korean',
        nativeName: '한국어',
        flag: '🇰🇷',
        rtl: false,
        voice: 'ko-KR'
    },
    'th': {
        name: 'Thai',
        nativeName: 'ไทย',
        flag: '🇹🇭',
        rtl: false,
        voice: 'th-TH'
    },
    'vi': {
        name: 'Vietnamese',
        nativeName: 'Tiếng Việt',
        flag: '🇻🇳',
        rtl: false,
        voice: 'vi-VN'
    },
    'id': {
        name: 'Indonesian',
        nativeName: 'Bahasa Indonesia',
        flag: '🇮🇩',
        rtl: false,
        voice: 'id-ID'
    },
    'ms': {
        name: 'Malay',
        nativeName: 'Bahasa Melayu',
        flag: '🇲🇾',
        rtl: false,
        voice: 'ms-MY'
    },
    'tl': {
        name: 'Filipino',
        nativeName: 'Filipino',
        flag: '🇵🇭',
        rtl: false,
        voice: 'tl-PH'
    }
};

// Language translations for UI elements
const TRANSLATIONS = {
    'en': {
        // Header
        'header.title': 'BHASHAI – India\'s First Regional Language AI Voice Agent Platform',
        'header.subtitle': 'AI Voice Agent Infrastructure for India\'s Multilingual Digital Future',
        'header.description': 'Building an AI-powered voice agent layer for enterprises, startups, and governance in 20+ Indian languages.',
        
        // Navigation
        'nav.home': 'Home',
        'nav.features': 'Features',
        'nav.pricing': 'Pricing',
        'nav.about': 'About',
        'nav.contact': 'Contact',
        'nav.login': 'Login/Signup',
        
        // Buttons
        'btn.start_trial': 'Start Free Trial',
        'btn.get_started': 'Get Started',
        'btn.learn_more': 'Learn More',
        'btn.contact_us': 'Contact Us',
        'btn.play_sample': 'Play Sample',
        
        // Features
        'features.title': 'AI Voice Agent Features',
        'features.inbound': 'Inbound AI Voice Agent',
        'features.outbound': 'Outbound AI Voice Agent Campaigns',
        'features.multilingual': 'Multi-language Support',
        'features.realtime': 'Real-time Analytics',
        
        // Pricing
        'pricing.title': 'Choose Your Plan',
        'pricing.basic': 'Basic Plan',
        'pricing.pro': 'Pro Plan',
        'pricing.enterprise': 'Enterprise Plan',
        'pricing.language': 'Language',
        'pricing.languages': 'Languages',
        'pricing.calls': 'Calls/mo',
        
        // Forms
        'form.name': 'Full Name',
        'form.email': 'Email Address',
        'form.phone': 'Phone Number',
        'form.company': 'Company Name',
        'form.business_type': 'Business Type',
        'form.message': 'Message',
        'form.submit': 'Submit',
        
        // Voice Samples
        'voice.title': 'Listen to AI Voice agents conversation Samples',
        'voice.subtitle': 'Experience AI voice agents in different Indian languages',
        'voice.sample_text': 'Hello, I\'m your AI voice agent. How can I help you today?',
        
        // Footer
        'footer.company': 'Company',
        'footer.products': 'Products',
        'footer.support': 'Support',
        'footer.legal': 'Legal',
        'footer.copyright': '© 2024 BhashAI. All rights reserved.',
        
        // Notifications
        'notification.language_changed': 'Language changed to',
        'notification.welcome': 'Welcome to BHASHAI Enterprise AI Platform!',
        'notification.trial_started': 'Free trial started successfully!',
        'notification.contact_sent': 'Message sent successfully!',
        
        // Accessibility
        'accessibility.skip_content': 'Skip to main content',
        'accessibility.screen_reader': 'Screen reader access',
        'accessibility.font_decrease': 'Decrease font size',
        'accessibility.font_reset': 'Reset font size',
        'accessibility.font_increase': 'Increase font size'
    },
    
    'hi': {
        // Header
        'header.title': 'भाषाई – भारत का पहला क्षेत्रीय भाषा AI वॉयस एजेंट प्लेटफॉर्म',
        'header.subtitle': 'भारत के बहुभाषी डिजिटल भविष्य के लिए AI वॉयस एजेंट इन्फ्रास्ट्रक्चर',
        'header.description': '20+ भारतीय भाषाओं में उद्यमों, स्टार्टअप्स और शासन के लिए AI-संचालित वॉयस एजेंट लेयर का निर्माण।',
        
        // Navigation
        'nav.home': 'होम',
        'nav.features': 'विशेषताएं',
        'nav.pricing': 'मूल्य निर्धारण',
        'nav.about': 'हमारे बारे में',
        'nav.contact': 'संपर्क',
        'nav.login': 'लॉगिन/साइनअप',
        
        // Buttons
        'btn.start_trial': 'मुफ्त ट्रायल शुरू करें',
        'btn.get_started': 'शुरू करें',
        'btn.learn_more': 'और जानें',
        'btn.contact_us': 'हमसे संपर्क करें',
        'btn.play_sample': 'नमूना चलाएं',
        
        // Features
        'features.title': 'AI वॉयस एजेंट विशेषताएं',
        'features.inbound': 'इनबाउंड AI वॉयस एजेंट',
        'features.outbound': 'आउटबाउंड AI वॉयस एजेंट अभियान',
        'features.multilingual': 'बहु-भाषा समर्थन',
        'features.realtime': 'रियल-टाइम एनालिटिक्स',
        
        // Pricing
        'pricing.title': 'अपना प्लान चुनें',
        'pricing.basic': 'बेसिक प्लान',
        'pricing.pro': 'प्रो प्लान',
        'pricing.enterprise': 'एंटरप्राइज प्लान',
        'pricing.language': 'भाषा',
        'pricing.languages': 'भाषाएं',
        'pricing.calls': 'कॉल/महीना',
        
        // Forms
        'form.name': 'पूरा नाम',
        'form.email': 'ईमेल पता',
        'form.phone': 'फोन नंबर',
        'form.company': 'कंपनी का नाम',
        'form.business_type': 'व्यवसाय का प्रकार',
        'form.message': 'संदेश',
        'form.submit': 'जमा करें',
        
        // Voice Samples
        'voice.title': 'AI वॉयस एजेंट बातचीत के नमूने सुनें',
        'voice.subtitle': 'विभिन्न भारतीय भाषाओं में AI वॉयस एजेंट का अनुभव करें',
        'voice.sample_text': 'नमस्ते, मैं आपका AI वॉयस एजेंट हूं। आज मैं आपकी कैसे मदद कर सकता हूं?',
        
        // Footer
        'footer.company': 'कंपनी',
        'footer.products': 'उत्पाद',
        'footer.support': 'सहायता',
        'footer.legal': 'कानूनी',
        'footer.copyright': '© 2024 भाषाई। सभी अधिकार सुरक्षित।',
        
        // Notifications
        'notification.language_changed': 'भाषा बदली गई',
        'notification.welcome': 'भाषाई एंटरप्राइज AI प्लेटफॉर्म में आपका स्वागत है!',
        'notification.trial_started': 'मुफ्त ट्रायल सफलतापूर्वक शुरू हुआ!',
        'notification.contact_sent': 'संदेश सफलतापूर्वक भेजा गया!',
        
        // Accessibility
        'accessibility.skip_content': 'मुख्य सामग्री पर जाएं',
        'accessibility.screen_reader': 'स्क्रीन रीडर एक्सेस',
        'accessibility.font_decrease': 'फॉन्ट साइज़ कम करें',
        'accessibility.font_reset': 'फॉन्ट साइज़ रीसेट करें',
        'accessibility.font_increase': 'फॉन्ट साइज़ बढ़ाएं'
    },

    'bn': {
        // Header
        'header.title': 'ভাষাই – ভারতের প্রথম আঞ্চলিক ভাষা AI ভয়েস এজেন্ট প্ল্যাটফর্ম',
        'header.subtitle': 'ভারতের বহুভাষিক ডিজিটাল ভবিষ্যতের জন্য AI ভয়েস এজেন্ট অবকাঠামো',
        'header.description': '২০+ ভারতীয় ভাষায় উদ্যোগ, স্টার্টআপ এবং শাসনের জন্য AI-চালিত ভয়েস এজেন্ট স্তর নির্মাণ।',

        // Navigation
        'nav.home': 'হোম',
        'nav.features': 'বৈশিষ্ট্য',
        'nav.pricing': 'মূল্য',
        'nav.about': 'আমাদের সম্পর্কে',
        'nav.contact': 'যোগাযোগ',
        'nav.login': 'লগইন/সাইনআপ',

        // Buttons
        'btn.start_trial': 'বিনামূল্যে ট্রায়াল শুরু করুন',
        'btn.get_started': 'শুরু করুন',
        'btn.learn_more': 'আরও জানুন',
        'btn.contact_us': 'আমাদের সাথে যোগাযোগ করুন',
        'btn.play_sample': 'নমুনা চালান',

        // Voice Samples
        'voice.sample_text': 'নমস্কার, আমি আপনার AI ভয়েস এজেন্ট। আজ আমি কীভাবে আপনাকে সাহায্য করতে পারি?'
    },

    'ta': {
        // Header
        'header.title': 'பாஷாய் – இந்தியாவின் முதல் பிராந்திய மொழி AI குரல் முகவர் தளம்',
        'header.subtitle': 'இந்தியாவின் பன்மொழி டிஜிட்டல் எதிர்காலத்திற்கான AI குரல் முகவர் உள்கட்டமைப்பு',
        'header.description': '20+ இந்திய மொழிகளில் நிறுவனங்கள், ஸ்டார்ட்அப்கள் மற்றும் ஆட்சிக்கான AI-இயங்கும் குரல் முகவர் அடுக்கை உருவாக்குதல்।',

        // Navigation
        'nav.home': 'முகப்பு',
        'nav.features': 'அம்சங்கள்',
        'nav.pricing': 'விலை',
        'nav.about': 'எங்களைப் பற்றி',
        'nav.contact': 'தொடர்பு',
        'nav.login': 'உள்நுழைவு/பதிவு',

        // Buttons
        'btn.start_trial': 'இலவச சோதனையைத் தொடங்கவும்',
        'btn.get_started': 'தொடங்கவும்',
        'btn.learn_more': 'மேலும் அறிக',
        'btn.contact_us': 'எங்களைத் தொடர்பு கொள்ளவும்',
        'btn.play_sample': 'மாதிரியை இயக்கவும்',

        // Voice Samples
        'voice.sample_text': 'வணக்கம், நான் உங்கள் AI குரல் முகவர். இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?'
    },

    'te': {
        // Header
        'header.title': 'భాషై – భారతదేశం యొక్క మొదటి ప్రాంతీయ భాష AI వాయిస్ ఏజెంట్ ప్లాట్‌ఫారమ్',
        'header.subtitle': 'భారతదేశం యొక్క బహుభాషా డిజిటల్ భవిష్యత్తు కోసం AI వాయిస్ ఏజెంట్ మౌలిక సదుపాయాలు',
        'header.description': '20+ భారతీయ భాషలలో సంస్థలు, స్టార్టప్‌లు మరియు పాలన కోసం AI-శక్తితో కూడిన వాయిస్ ఏజెంట్ లేయర్ నిర్మాణం।',

        // Navigation
        'nav.home': 'హోమ్',
        'nav.features': 'లక్షణాలు',
        'nav.pricing': 'ధర',
        'nav.about': 'మా గురించి',
        'nav.contact': 'సంప్రదింపులు',
        'nav.login': 'లాగిన్/సైన్అప్',

        // Buttons
        'btn.start_trial': 'ఉచిత ట్రయల్ ప్రారంభించండి',
        'btn.get_started': 'ప్రారంభించండి',
        'btn.learn_more': 'మరింత తెలుసుకోండి',
        'btn.contact_us': 'మమ్మల్ని సంప్రదించండి',
        'btn.play_sample': 'నమూనా ప్లే చేయండి',

        // Voice Samples
        'voice.sample_text': 'నమస్కారం, నేను మీ AI వాయిస్ ఏజెంట్. ఈరోజు నేను మీకు ఎలా సహాయం చేయగలను?'
    },

    'mr': {
        // Header
        'header.title': 'भाषाई – भारताचे पहिले प्रादेशिक भाषा AI व्हॉइस एजंट प्लॅटफॉर्म',
        'header.subtitle': 'भारताच्या बहुभाषिक डिजिटल भविष्यासाठी AI व्हॉइस एजंट पायाभूत सुविधा',
        'header.description': '२०+ भारतीय भाषांमध्ये उद्यम, स्टार्टअप आणि शासनासाठी AI-चालित व्हॉइस एजंट स्तर तयार करणे।',

        // Navigation
        'nav.home': 'मुख्यपृष्ठ',
        'nav.features': 'वैशिष्ट्ये',
        'nav.pricing': 'किंमत',
        'nav.about': 'आमच्याबद्दल',
        'nav.contact': 'संपर्क',
        'nav.login': 'लॉगिन/साइनअप',

        // Buttons
        'btn.start_trial': 'विनामूल्य चाचणी सुरू करा',
        'btn.get_started': 'सुरुवात करा',
        'btn.learn_more': 'अधिक जाणून घ्या',
        'btn.contact_us': 'आमच्याशी संपर्क साधा',
        'btn.play_sample': 'नमुना प्ले करा',

        // Voice Samples
        'voice.sample_text': 'नमस्कार, मी तुमचा AI व्हॉइस एजंट आहे. आज मी तुम्हाला कशी मदत करू शकतो?'
    },

    'gu': {
        // Header
        'header.title': 'ભાષાઈ – ભારતનું પ્રથમ પ્રાદેશિક ભાષા AI વૉઇસ એજન્ટ પ્લેટફોર્મ',
        'header.subtitle': 'ભારતના બહુભાષી ડિજિટલ ભવિષ્ય માટે AI વૉઇસ એજન્ટ ઇન્ફ્રાસ્ટ્રક્ચર',
        'header.description': '20+ ભારતીય ભાષાઓમાં એન્ટરપ્રાઇઝ, સ્ટાર્ટઅપ અને શાસન માટે AI-સંચાલિત વૉઇસ એજન્ટ સ્તર નિર્માણ.',

        // Navigation
        'nav.home': 'હોમ',
        'nav.features': 'લક્ષણો',
        'nav.pricing': 'કિંમત',
        'nav.about': 'અમારા વિશે',
        'nav.contact': 'સંપર્ક',
        'nav.login': 'લોગિન/સાઇનઅપ',

        // Buttons
        'btn.start_trial': 'મફત ટ્રાયલ શરૂ કરો',
        'btn.get_started': 'શરૂ કરો',
        'btn.learn_more': 'વધુ જાણો',
        'btn.contact_us': 'અમારો સંપર્ક કરો',
        'btn.play_sample': 'નમૂનો ચલાવો',

        // Voice Samples
        'voice.sample_text': 'નમસ્તે, હું તમારો AI વૉઇસ એજન્ટ છું. આજે હું તમારી કેવી રીતે મદદ કરી શકું?'
    }
};

// Current language state
let currentLanguage = localStorage.getItem('bhashaiLanguage') || 'en';

// Language management functions
class LanguageManager {
    constructor() {
        this.currentLang = currentLanguage;
        this.translations = TRANSLATIONS;
        this.supportedLanguages = SUPPORTED_LANGUAGES;
    }

    // Get translation for a key
    t(key, lang = null) {
        const targetLang = lang || this.currentLang;
        if (this.translations[targetLang] && this.translations[targetLang][key]) {
            return this.translations[targetLang][key];
        }
        // Fallback to English
        return this.translations['en'][key] || key;
    }

    // Change language
    changeLanguage(langCode) {
        if (this.supportedLanguages[langCode]) {
            this.currentLang = langCode;
            localStorage.setItem('bhashaiLanguage', langCode);
            this.updatePageContent();
            this.updateDirection();
            return true;
        }
        return false;
    }

    // Update page content with translations
    updatePageContent() {
        // Update all elements with data-translate attribute
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            element.textContent = this.t(key);
        });

        // Update placeholders
        document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
            const key = element.getAttribute('data-translate-placeholder');
            element.placeholder = this.t(key);
        });

        // Update titles
        document.querySelectorAll('[data-translate-title]').forEach(element => {
            const key = element.getAttribute('data-translate-title');
            element.title = this.t(key);
        });
    }

    // Update text direction for RTL languages
    updateDirection() {
        const isRTL = this.supportedLanguages[this.currentLang].rtl;
        document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
        document.documentElement.lang = this.currentLang;
    }

    // Generate language selector HTML
    generateLanguageSelector() {
        let options = '';
        Object.keys(this.supportedLanguages).forEach(code => {
            const lang = this.supportedLanguages[code];
            const selected = code === this.currentLang ? 'selected' : '';
            options += `<option value="${code}" ${selected}>${lang.flag} ${lang.nativeName}</option>`;
        });
        return options;
    }

    // Initialize language system
    init() {
        this.updatePageContent();
        this.updateDirection();
        this.setupLanguageSelector();
    }

    // Setup language selector functionality
    setupLanguageSelector() {
        const selectors = document.querySelectorAll('.lang-selector, .language-selector');
        selectors.forEach(selector => {
            selector.innerHTML = this.generateLanguageSelector();
            selector.addEventListener('change', (e) => {
                this.changeLanguage(e.target.value);
                this.showNotification(`${this.t('notification.language_changed')} ${this.supportedLanguages[e.target.value].nativeName}`);
            });
        });
    }

    // Show notification
    showNotification(message) {
        // Remove existing notification
        const existing = document.querySelector('.language-notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = 'language-notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
}

// Initialize language manager
const languageManager = new LanguageManager();

// Export for global use
window.LanguageManager = LanguageManager;
window.languageManager = languageManager;
window.SUPPORTED_LANGUAGES = SUPPORTED_LANGUAGES;
window.TRANSLATIONS = TRANSLATIONS;
