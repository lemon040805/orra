# language_config.py
from functools import lru_cache

LANGUAGE_ALIASES = {
    "english": "en", "en": "en",
    "malay": "ms", "ms": "ms", "bm": "ms", "bahasa melayu": "ms",
}
CODE_TO_NAME = {"en": "English", "ms": "Malay"}
SUPPORTED_LANG_CODES = set(CODE_TO_NAME.keys())

GLOBAL_USER_ID: str | None = None
GLOBAL_NATIVE_LANGUAGE: str | None = None  # ISO code
GLOBAL_TARGET_LANGUAGE: str | None = None  # ISO code
GLOBAL_NATIVE_LANGUAGE_NAME: str | None = None  # Human-readable
GLOBAL_TARGET_LANGUAGE_NAME: str | None = None

def normalize_lang(lang: str) -> str:
    if not isinstance(lang, str):
        raise ValueError("Language must be a string.")
    code = LANGUAGE_ALIASES.get(lang.strip().lower())
    if not code or code not in SUPPORTED_LANG_CODES:
        raise ValueError(f"Unsupported language: {lang!r}")
    return code

@lru_cache(maxsize=1024)
def _fetch_user_language_codes(user_id: str) -> tuple[str, str]:
    from user_manager import get_user_language_prefs
    native_raw, target_raw = get_user_language_prefs(user_id)
    if not native_raw or not target_raw:
        raise ValueError(f"User {user_id} missing language prefs.")
    return normalize_lang(native_raw), normalize_lang(target_raw)

def code_to_name(code: str) -> str:
    return CODE_TO_NAME.get(code, code)

def refresh_language_globals(user_id: str) -> None:
    """
    MUST be called per-request with the current user_id.
    No defaults; raises if prefs are missing.
    """
    global GLOBAL_USER_ID, GLOBAL_NATIVE_LANGUAGE, GLOBAL_TARGET_LANGUAGE
    global GLOBAL_NATIVE_LANGUAGE_NAME, GLOBAL_TARGET_LANGUAGE_NAME

    if not user_id:
        raise ValueError("user_id is required to refresh globals.")
    native, target = _fetch_user_language_codes(user_id)

    GLOBAL_USER_ID = user_id
    GLOBAL_NATIVE_LANGUAGE = native
    GLOBAL_TARGET_LANGUAGE = target
    GLOBAL_NATIVE_LANGUAGE_NAME = code_to_name(native)
    GLOBAL_TARGET_LANGUAGE_NAME = code_to_name(target)

def clear_language_cache(user_id: str | None = None) -> None:
    if user_id is None:
        _fetch_user_language_codes.cache_clear()
    else:
        try:
            _fetch_user_language_codes.cache_pop(user_id)
        except Exception:
            _fetch_user_language_codes.cache_clear()


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
