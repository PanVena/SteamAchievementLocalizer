"""
Steam Language Codes Mapping
Simple display names for Steam language codes in table headers
"""

# Steam's standard language codes with display names
STEAM_LANGUAGE_CODES = {
    'arabic': 'العربية (Arabic)',
    'bulgarian': 'Български (Bulgarian)',
    'czech': 'Čeština (Czech)',
    'danish': 'Dansk (Danish)',
    'dutch': 'Nederlands (Dutch)',
    'english': 'English',
    'finnish': 'Suomi (Finnish)',
    'french': 'Français (French)',
    'german': 'Deutsch (German)',
    'greek': 'Ελληνικά (Greek)',
    'hungarian': 'Magyar (Hungarian)',
    'indonesian': 'Bahasa Indonesia (Indonesian)',
    'italian': 'Italiano (Italian)',
    'japanese': '日本語 (Japanese)',
    'koreana': '한국어 (Korean)',
    'norwegian': 'Norsk (Norwegian)',
    'polish': 'Polski (Polish)',
    'portuguese': 'Português (Portuguese)',
    'brazilian': 'Português-Brasil (Portuguese - Brazil)',
    'romanian': 'Română (Romanian)',
    'spanish': 'Español-España (Spanish)',
    'latam': 'Español-Latinoamérica (Spanish - Latin America)',
    'swedish': 'Svenska (Swedish)',
    'thai': 'ไทย (Thai)',
    'turkish': 'Türkçe (Turkish)',
    'ukrainian': 'Українська',
    'vietnamese': 'Tiếng Việt (Vietnamese)'
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

def get_available_languages_for_selection() -> list:
    """
    Get list of available Steam languages for selection, 
    sorted by display name
    """
    languages = [(code, display) for code, display in STEAM_LANGUAGE_CODES.items()]
    languages.sort(key=lambda x: x[1])  # Sort by display name
    
    return [code for code, _ in languages]