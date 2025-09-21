# Global language configuration for Lambda functions
# Ensures consistency across all Lambda functions

LANGUAGE_CONFIG = {
    # Global/Default languages
    'GLOBAL_NATIVE_LANGUAGE': 'en',
    'GLOBAL_TARGET_LANGUAGE': 'ms',
    'GLOBAL_NATIVE_LANGUAGE_NAME': 'English',
    'GLOBAL_TARGET_LANGUAGE_NAME': 'Malay',
    
    # Supported languages
    'SUPPORTED_LANGUAGES': {
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
    
    # Language codes for AWS services
    'LANGUAGE_CODES': {
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
    }
}

def get_language_name(code):
    """Get language name from code"""
    return LANGUAGE_CONFIG['SUPPORTED_LANGUAGES'].get(code, code.upper())

def get_language_code(lang):
    """Get language code for AWS services"""
    return LANGUAGE_CONFIG['LANGUAGE_CODES'].get(lang, 'en-US')

def get_user_languages(user_data):
    """Get user languages with fallback to global defaults"""
    return {
        'native_language': user_data.get('nativeLanguage', LANGUAGE_CONFIG['GLOBAL_NATIVE_LANGUAGE']),
        'target_language': user_data.get('targetLanguage', LANGUAGE_CONFIG['GLOBAL_TARGET_LANGUAGE']),
        'native_language_name': get_language_name(user_data.get('nativeLanguage', LANGUAGE_CONFIG['GLOBAL_NATIVE_LANGUAGE'])),
        'target_language_name': get_language_name(user_data.get('targetLanguage', LANGUAGE_CONFIG['GLOBAL_TARGET_LANGUAGE'])),
        'proficiency': user_data.get('proficiency', user_data.get('finalLevel', 'beginner'))
    }

def get_global_defaults():
    """Get global default languages"""
    return {
        'native_language': LANGUAGE_CONFIG['GLOBAL_NATIVE_LANGUAGE'],
        'target_language': LANGUAGE_CONFIG['GLOBAL_TARGET_LANGUAGE'],
        'native_language_name': LANGUAGE_CONFIG['GLOBAL_NATIVE_LANGUAGE_NAME'],
        'target_language_name': LANGUAGE_CONFIG['GLOBAL_TARGET_LANGUAGE_NAME']
    }
