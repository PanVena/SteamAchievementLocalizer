"""
Steam Language Codes Mapping
Simple display names for Steam language codes in table headers
"""

import locale
import os

# Steam's standard language codes with display names (excluding Russian and Chinese)
STEAM_LANGUAGE_CODES = {
    'arabic': 'Arabic (العربية)',
    'brazilian': 'Portuguese - Brazil (Português - Brasil)', 
    'bulgarian': 'Bulgarian (български)',
    'czech': 'Czech (čeština)',
    'danish': 'Danish (Dansk)',
    'dutch': 'Dutch (Nederlands)',
    'english': 'English',
    'finnish': 'Finnish (Suomi)',
    'french': 'French (Français)',
    'german': 'German (Deutsch)',
    'greek': 'Greek (Ελληνικά)',
    'hungarian': 'Hungarian (Magyar)',
    'italian': 'Italian (Italiano)',
    'japanese': 'Japanese (日本語)',
    'koreana': 'Korean (한국어)',
    'latam': 'Spanish - Latin America (Español - Latinoamérica)',
    'norwegian': 'Norwegian (Norsk)',
    'polish': 'Polish (Polski)',
    'portuguese': 'Portuguese (Português)',
    'romanian': 'Romanian (Română)',
    'spanish': 'Spanish (Español)',
    'swedish': 'Swedish (Svenska)',
    'thai': 'Thai (ไทย)',
    'turkish': 'Turkish (Türkçe)',
    'ukrainian': 'Ukrainian (Українська)',
    'vietnamese': 'Vietnamese (Tiếng Việt)'
}

# Mapping system locale codes to Steam language codes (excluding Russian and Chinese)
LOCALE_TO_STEAM = {
    'uk': 'ukrainian',
    'uk_UA': 'ukrainian', 
    'pl': 'polish',
    'pl_PL': 'polish',
    'de': 'german',
    'de_DE': 'german',
    'fr': 'french',
    'fr_FR': 'french',
    'es': 'spanish',
    'es_ES': 'spanish',
    'it': 'italian',
    'it_IT': 'italian',
    'pt': 'portuguese',
    'pt_PT': 'portuguese',
    'pt_BR': 'brazilian',
    'ja': 'japanese',
    'ja_JP': 'japanese',
    'ko': 'koreana',
    'ko_KR': 'koreana',
    'ar': 'arabic',
    'tr': 'turkish',
    'tr_TR': 'turkish'
}

def get_display_name(steam_code: str) -> str:
    """Get display name for Steam language code"""
    return STEAM_LANGUAGE_CODES.get(steam_code, steam_code.title())

def get_code_from_display_name(display_name: str) -> str:
    """Get Steam language code from display name"""
    for code, display in STEAM_LANGUAGE_CODES.items():
        if display == display_name:
            return code
    return display_name.lower()  # Fallback

def get_system_language() -> str:
    """
    Detect system language and return corresponding Steam language code
    Returns 'english' as fallback if system language is not in Steam languages
    """
    try:
        # Try to get system locale
        system_locale = locale.getdefaultlocale()[0]
        if system_locale:
            # Check full locale first (e.g., uk_UA)
            if system_locale in LOCALE_TO_STEAM:
                return LOCALE_TO_STEAM[system_locale]
            
            # Check language part only (e.g., uk from uk_UA)
            lang_part = system_locale.split('_')[0]
            if lang_part in LOCALE_TO_STEAM:
                return LOCALE_TO_STEAM[lang_part]
        
        # Try environment variables as backup
        for env_var in ['LANG', 'LANGUAGE', 'LC_ALL']:
            env_lang = os.environ.get(env_var, '')
            if env_lang:
                lang_code = env_lang.split('.')[0].split('_')[0]
                if lang_code in LOCALE_TO_STEAM:
                    return LOCALE_TO_STEAM[lang_code]
                    
    except Exception:
        pass
    
    return 'english'  # Default fallback

def get_available_languages_for_selection() -> list:
    """
    Get list of available Steam languages for selection, 
    with system language first
    """
    system_lang = get_system_language()
    languages = []
    
    # Add system language first if it's not english
    if system_lang != 'english' and system_lang in STEAM_LANGUAGE_CODES:
        languages.append(system_lang)
    
    # Add all other languages sorted by display name, excluding system language
    other_languages = [(code, display) for code, display in STEAM_LANGUAGE_CODES.items() 
                      if code != system_lang]
    other_languages.sort(key=lambda x: x[1])  # Sort by display name
    
    languages.extend([code for code, _ in other_languages])
    
    return languages