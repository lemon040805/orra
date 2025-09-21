# language_config.py
"""
Central language configuration.
No global hardcoded defaults. Languages come directly from the user database.
On import, we resolve the CURRENT user and set module-level globals:
  - GLOBAL_NATIVE_LANGUAGE
  - GLOBAL_TARGET_LANGUAGE

How we resolve the current user:
  1) user_manager.get_current_user_id() if present.
  2) env var CURRENT_USER_ID if set.
  3) Otherwise: raise RuntimeError (explicitly require a user context).
"""
import os

LANGUAGE_ALIASES = {
    "english": "en",
    "en": "en",
    "malay": "ms",
    "ms": "ms",
    "bm": "ms",  # Bahasa Melayu
    "bahasa melayu": "ms",
}

def normalize_lang(lang: str) -> str:
    if not isinstance(lang, str):
        return lang
    return LANGUAGE_ALIASES.get(lang.strip().lower(), lang.strip().lower())

def _resolve_current_user_id():
    try:
        from user_manager import get_current_user_id  # type: ignore
        uid = get_current_user_id()
        if uid:
            return uid
    except Exception:
        pass
    env_uid = os.getenv("CURRENT_USER_ID")
    if env_uid:
        return env_uid
    raise RuntimeError("No current user id. Set CURRENT_USER_ID env var or implement user_manager.get_current_user_id()")

def _fetch_user_langs(user_id):
    from user_manager import get_user_language_prefs  # type: ignore
    native, target = get_user_language_prefs(user_id)
    if not native or not target:
        raise RuntimeError(f"User {user_id} missing language prefs in DB (native={native}, target={target}).")
    return normalize_lang(native), normalize_lang(target)

def refresh_language_globals():
    "Re-resolve current user and refresh module-level globals."
    global GLOBAL_NATIVE_LANGUAGE, GLOBAL_TARGET_LANGUAGE, GLOBAL_USER_ID
    uid = _resolve_current_user_id()
    native, target = _fetch_user_langs(uid)
    GLOBAL_USER_ID = uid
    GLOBAL_NATIVE_LANGUAGE = native
    GLOBAL_TARGET_LANGUAGE = target
    return GLOBAL_NATIVE_LANGUAGE, GLOBAL_TARGET_LANGUAGE

# Initialize at import
GLOBAL_USER_ID = None
GLOBAL_NATIVE_LANGUAGE = None
GLOBAL_TARGET_LANGUAGE = None
refresh_language_globals()


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
