// Global language configuration for Lambda functions
// This file should be imported by all Lambda functions to ensure consistency

const LANGUAGE_CONFIG = {
    // Default/Global languages
    GLOBAL_NATIVE_LANGUAGE: 'en',
    GLOBAL_TARGET_LANGUAGE: 'ms', 
    GLOBAL_NATIVE_LANGUAGE_NAME: 'English',
    GLOBAL_TARGET_LANGUAGE_NAME: 'Malay',
    
    // Supported languages
    SUPPORTED_LANGUAGES: {
        'en': 'English',
        'ms': 'Malay',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'th': 'Thai',
        'vi': 'Vietnamese',
        'id': 'Indonesian',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'pt': 'Portuguese',
        'ru': 'Russian'
    },
    
    // Language codes for speech/translation APIs
    LANGUAGE_CODES: {
        'en': 'en-US',
        'ms': 'ms-MY',
        'es': 'es-ES',
        'fr': 'fr-FR',
        'de': 'de-DE',
        'it': 'it-IT',
        'zh': 'zh-CN',
        'ja': 'ja-JP',
        'ko': 'ko-KR',
        'th': 'th-TH',
        'vi': 'vi-VN',
        'id': 'id-ID',
        'ar': 'ar-SA',
        'hi': 'hi-IN',
        'pt': 'pt-BR',
        'ru': 'ru-RU'
    },
    
    // Helper functions
    getLanguageName: (code) => {
        return LANGUAGE_CONFIG.SUPPORTED_LANGUAGES[code] || code.toUpperCase();
    },
    
    getLanguageCode: (lang) => {
        return LANGUAGE_CONFIG.LANGUAGE_CODES[lang] || 'en-US';
    },
    
    // Get user languages with fallback to global defaults
    getUserLanguages: (userData) => {
        return {
            nativeLanguage: userData?.nativeLanguage || LANGUAGE_CONFIG.GLOBAL_NATIVE_LANGUAGE,
            targetLanguage: userData?.targetLanguage || LANGUAGE_CONFIG.GLOBAL_TARGET_LANGUAGE,
            nativeLanguageName: LANGUAGE_CONFIG.getLanguageName(userData?.nativeLanguage || LANGUAGE_CONFIG.GLOBAL_NATIVE_LANGUAGE),
            targetLanguageName: LANGUAGE_CONFIG.getLanguageName(userData?.targetLanguage || LANGUAGE_CONFIG.GLOBAL_TARGET_LANGUAGE),
            proficiency: userData?.proficiency || 'beginner'
        };
    }
};

// Export for Lambda functions
module.exports = LANGUAGE_CONFIG;

// For browser environments (if needed)
if (typeof window !== 'undefined') {
    window.LANGUAGE_CONFIG = LANGUAGE_CONFIG;
}
